"""Safe local Git fixtures for the separate agent PR authoring route."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import agent_pr


def run(*args: str, cwd: Path, env: dict[str, str] | None = None) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def proposal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    remote.mkdir()
    run("git", "init", "--bare", "-q", str(remote), cwd=tmp_path)
    run("git", "init", "-q", "-b", "main", str(repo), cwd=tmp_path)
    run("git", "config", "user.name", "Fixture", cwd=repo)
    run("git", "config", "user.email", "fixture@example.invalid", cwd=repo)
    (repo / "README.md").write_text("baseline\n", encoding="utf-8")
    run("git", "add", "README.md", cwd=repo)
    run("git", "commit", "-qm", "baseline", cwd=repo)
    base = run("git", "rev-parse", "HEAD", cwd=repo)
    run("git", "remote", "add", "origin", str(remote), cwd=repo)
    run("git", "push", "-q", "origin", "main", cwd=repo)
    run("git", "switch", "-qc", "codex/fixture", cwd=repo)
    evidence = repo / "docs/evidence/proposal.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(
        "Agent-authored fixture; no host disks used.\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("proposal\n", encoding="utf-8")
    run("git", "add", "README.md", "docs/evidence/proposal.md", cwd=repo)
    run("git", "commit", "-qm", "proposal", cwd=repo)
    source = run("git", "rev-parse", "HEAD", cwd=repo)
    run("git", "push", "-q", "origin", "codex/fixture", cwd=repo)
    run("git", "switch", "-q", "main", cwd=repo)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("GITHUB_SHA", base)
    return {"remote": remote, "repo": repo, "base": base, "source": source}


def prepare(proposal: dict[str, object], tmp_path: Path) -> dict[str, str]:
    return agent_pr.prepare(
        "codex/fixture",
        str(proposal["source"]),
        "docs/evidence/proposal.md",
        tmp_path / "plan.json",
    )


def test_prepare_replays_exact_tree_under_new_commit(
    proposal: dict[str, object],
    tmp_path: Path,
) -> None:
    plan = prepare(proposal, tmp_path)
    repo = proposal["repo"]
    assert isinstance(repo, Path)
    assert plan["base_sha"] == proposal["base"]
    assert plan["source_sha"] == proposal["source"]
    assert plan["commit_sha"] != proposal["source"]
    assert run("git", "rev-parse", "HEAD^", cwd=repo) == proposal["base"]
    assert run("git", "rev-parse", "HEAD^{tree}", cwd=repo) == run(
        "git",
        "rev-parse",
        f"{proposal['source']}^{{tree}}",
        cwd=repo,
    )
    assert json.loads((tmp_path / "plan.json").read_text()) == plan


@pytest.mark.parametrize(
    ("ref", "sha", "evidence"),
    [
        ("main", "source", "docs/evidence/proposal.md"),
        ("codex/../main", "source", "docs/evidence/proposal.md"),
        ("codex/fixture", "0" * 40, "docs/evidence/proposal.md"),
        ("codex/fixture", "source", "docs/evidence/../proposal.md"),
        ("codex/fixture", "source", "docs/evidence/stale.md"),
    ],
)
def test_prepare_rejects_invalid_or_stale_source(
    proposal: dict[str, object],
    tmp_path: Path,
    ref: str,
    sha: str,
    evidence: str,
) -> None:
    source = str(proposal["source"]) if sha == "source" else sha
    with pytest.raises(agent_pr.ProposalError):
        agent_pr.prepare(ref, source, evidence, tmp_path / "plan.json")
    assert not (tmp_path / "plan.json").exists()


def test_prepare_refuses_advanced_main(
    proposal: dict[str, object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_SHA", "0" * 40)
    with pytest.raises(agent_pr.ProposalError, match="main advanced"):
        prepare(proposal, tmp_path)


def test_prepare_refuses_symlink_evidence(
    proposal: dict[str, object],
    tmp_path: Path,
) -> None:
    repo = proposal["repo"]
    assert isinstance(repo, Path)
    run("git", "switch", "-q", "codex/fixture", cwd=repo)
    evidence = repo / "docs/evidence/proposal.md"
    evidence.unlink()
    evidence.symlink_to("../../README.md")
    run("git", "add", "docs/evidence/proposal.md", cwd=repo)
    run("git", "commit", "-qm", "symlink evidence", cwd=repo)
    source = run("git", "rev-parse", "HEAD", cwd=repo)
    run("git", "push", "-q", "origin", "codex/fixture", cwd=repo)
    run("git", "switch", "-q", "main", cwd=repo)
    with pytest.raises(agent_pr.ProposalError, match="regular file"):
        agent_pr.prepare(
            "codex/fixture", source, "docs/evidence/proposal.md", tmp_path / "plan.json"
        )


def test_publisher_uses_app_token_and_reuses_exact_branch(
    proposal: dict[str, object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = prepare(proposal, tmp_path)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gh = fake_bin / "gh"
    fake_gh.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib, sys\n"
        "marker = pathlib.Path(os.environ['FAKE_PR_MARKER'])\n"
        "if '--method' in sys.argv and sys.argv[sys.argv.index('--method') + 1] == 'GET':\n"
        "    if marker.exists():\n"
        "        print('https://github.com/BeamoTech/beamo-wipe/pull/999')\n"
        "else:\n"
        "    marker.write_text('created')\n"
        "    print('https://github.com/BeamoTech/beamo-wipe/pull/999')\n",
        encoding="utf-8",
    )
    fake_gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("GITHUB_REPOSITORY", agent_pr.REPOSITORY)
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_ACTOR", "BeamoINT")
    monkeypatch.setenv("GH_TOKEN", "test-token")
    monkeypatch.setenv("FAKE_PR_MARKER", str(tmp_path / "created"))
    assert agent_pr.publish(tmp_path / "plan.json").endswith("/pull/999")
    remote = proposal["remote"]
    assert isinstance(remote, Path)
    assert (
        run("git", "--git-dir", str(remote), "rev-parse", plan["branch"], cwd=tmp_path)
        == plan["commit_sha"]
    )
    assert agent_pr.publish(tmp_path / "plan.json").endswith("/pull/999")


def test_publisher_refuses_wrong_actor(
    proposal: dict[str, object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare(proposal, tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", agent_pr.REPOSITORY)
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_ACTOR", "another-user")
    monkeypatch.setenv("GH_TOKEN", "test-token")
    with pytest.raises(agent_pr.ProposalError, match="publisher identity"):
        agent_pr.publish(tmp_path / "plan.json")
