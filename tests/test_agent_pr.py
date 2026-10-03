"""Safe local Git fixtures for the separate agent PR authoring route."""

from __future__ import annotations

import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import subprocess
import threading
from urllib.parse import urlsplit

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
    # No fixture may consult a developer's credential helper or prompt for one.
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
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


@pytest.fixture
def authenticated_remote(proposal, tmp_path):
    """A tiny smart-HTTP Git remote; only pushes require a fake App token."""
    remote = proposal["remote"]
    assert isinstance(remote, Path)
    run("git", "--git-dir", str(remote), "config", "http.receivepack", "true", cwd=tmp_path)
    authenticated_pushes = []
    expected = "Basic " + base64.b64encode(b"x-access-token:test-token").decode()

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def log_message(self, _format, *args):
            pass

        def do_GET(self):
            self.serve_git()

        def do_POST(self):
            self.serve_git()

        def serve_git(self):
            url = urlsplit(self.path)
            pushing = "git-receive-pack" in url.path or "git-receive-pack" in url.query
            if pushing and self.headers.get("Authorization") != expected:
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="fixture"')
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if pushing:
                authenticated_pushes.append(self.command)
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1024 * 1024:
                self.send_error(413)
                return
            environment = os.environ.copy()
            environment.update(
                GIT_PROJECT_ROOT=str(tmp_path),
                GIT_HTTP_EXPORT_ALL="1",
                REQUEST_METHOD=self.command,
                PATH_INFO=url.path,
                QUERY_STRING=url.query,
                CONTENT_TYPE=self.headers.get("Content-Type", ""),
                CONTENT_LENGTH=str(length),
                REMOTE_USER="fixture" if pushing else "",
                REMOTE_ADDR="127.0.0.1",
            )
            result = subprocess.run(
                ["git", "http-backend"],
                input=self.rfile.read(length),
                env=environment,
                capture_output=True,
                check=True,
                timeout=10,
            )
            header_bytes, body = result.stdout.split(b"\r\n\r\n", 1)
            headers = dict(
                line.split(": ", 1) for line in header_bytes.decode().split("\r\n")
            )
            self.send_response(int(headers.pop("Status", "200").split()[0]))
            for name, value in headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    server.timeout = 2
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/remote.git", authenticated_pushes
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
        assert not worker.is_alive()


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


@pytest.mark.parametrize("valid_token", [True, False])
def test_publisher_authenticates_push_before_creating_or_reusing_pr(
    proposal: dict[str, object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    authenticated_remote,
    valid_token,
) -> None:
    plan = prepare(proposal, tmp_path)
    remote_url, authenticated_pushes = authenticated_remote
    repo = proposal["repo"]
    assert isinstance(repo, Path)
    run("git", "remote", "set-url", "origin", remote_url, cwd=repo)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gh = fake_bin / "gh"
    fake_gh.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib, sys\n"
        "marker = pathlib.Path(os.environ['FAKE_PR_MARKER'])\n"
        "if sys.argv[1:3] == ['auth', 'git-credential']:\n"
        "    if sys.argv[3] == 'get':\n"
        "        print('username=x-access-token')\n"
        "        print('password=' + os.environ['GH_TOKEN'])\n"
        "elif '--method' in sys.argv and sys.argv[sys.argv.index('--method') + 1] == 'GET':\n"
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
    monkeypatch.setenv("GH_TOKEN", "test-token" if valid_token else "rejected-token")
    monkeypatch.setenv("FAKE_PR_MARKER", str(tmp_path / "created"))
    if not valid_token:
        with pytest.raises(agent_pr.ProposalError, match="git failed"):
            agent_pr.publish(tmp_path / "plan.json")
        assert not authenticated_pushes
        assert not (tmp_path / "created").exists()
        return
    assert agent_pr.publish(tmp_path / "plan.json").endswith("/pull/999")
    assert authenticated_pushes == ["GET", "POST"]
    remote = proposal["remote"]
    assert isinstance(remote, Path)
    assert (
        run("git", "--git-dir", str(remote), "rev-parse", plan["branch"], cwd=tmp_path)
        == plan["commit_sha"]
    )
    assert agent_pr.publish(tmp_path / "plan.json").endswith("/pull/999")
    assert authenticated_pushes == ["GET", "POST"]


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
