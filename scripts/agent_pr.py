#!/usr/bin/env python3
"""Replay a reviewed agent proposal under a dedicated GitHub App identity.

The source branch is only data: this script never executes its files. The
workflow runs this script from main and keeps the App token in a protected
environment. This is a proposal transport, not proof of who wrote the source.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


REPOSITORY = "BeamoTech/beamo-wipe"
BRANCH_RE = re.compile(r"codex/[a-z0-9][a-z0-9._/-]{0,93}")
SHA_RE = re.compile(r"[0-9a-f]{40}")
EVIDENCE_RE = re.compile(r"docs/evidence/[a-zA-Z0-9][a-zA-Z0-9._/-]{0,175}\.md")
MAX_FILES = 500
TIMEOUT = 30


class ProposalError(Exception):
    """A proposal did not satisfy the bounded, fail-closed transport rules."""


def command(*args: str, input_bytes: bytes | None = None) -> str:
    try:
        completed = subprocess.run(
            args,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProposalError(f"command failed or timed out: {args[0]}") from exc
    if completed.returncode:
        raise ProposalError(
            f"{args[0]} failed with exit {completed.returncode}: "
            + completed.stderr.decode("utf-8", errors="replace")[:500]
        )
    return completed.stdout.decode("utf-8", errors="strict").strip()


def git(*args: str) -> str:
    return command("git", *args)


def validate_ref(ref: str) -> None:
    if (
        not BRANCH_RE.fullmatch(ref)
        or ".." in ref
        or "//" in ref
        or ref.endswith(("/", ".", ".lock"))
    ):
        raise ProposalError("proposal ref must be a bounded codex/* branch")


def validate_evidence(path: str) -> None:
    if not EVIDENCE_RE.fullmatch(path) or any(
        part in ("", ".", "..") for part in path.split("/")
    ):
        raise ProposalError("evidence must be a Markdown file under docs/evidence/")


def prepare(ref: str, sha: str, evidence: str, output: Path) -> dict[str, str]:
    validate_ref(ref)
    validate_evidence(evidence)
    if not SHA_RE.fullmatch(sha):
        raise ProposalError("proposal SHA must be 40 lowercase hex characters")
    if git("status", "--porcelain"):
        raise ProposalError("checkout must be clean")

    git(
        "fetch",
        "--no-tags",
        "origin",
        "+refs/heads/main:refs/remotes/origin/main",
        f"+refs/heads/{ref}:refs/remotes/origin/{ref}",
    )
    base = git("rev-parse", "refs/remotes/origin/main")
    source = git("rev-parse", f"refs/remotes/origin/{ref}")
    if os.environ.get("GITHUB_SHA") and os.environ["GITHUB_SHA"] != base:
        raise ProposalError("main advanced since workflow dispatch")
    if git("rev-parse", "HEAD") != base or source != sha:
        raise ProposalError("main checkout or proposal SHA changed")
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base, source],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProposalError("could not inspect proposal ancestry") from exc
    if ancestor.returncode:
        raise ProposalError("proposal must descend from current main")
    if git("rev-list", "--merges", f"{base}..{source}"):
        raise ProposalError("proposal must not contain merge commits")
    files = git("diff", "--name-only", "-z", base, source)
    changed = [name for name in files.split("\0") if name]
    if not changed or len(changed) > MAX_FILES:
        raise ProposalError("proposal must change between 1 and 500 files")
    if any(name.lower().endswith((".iso", ".img", ".pem", ".key")) for name in changed):
        raise ProposalError("proposal includes a prohibited binary or key file")
    if evidence not in changed:
        raise ProposalError("proposal must update its own evidence file")
    evidence_tree_entry = git("ls-tree", source, "--", evidence)
    if not evidence_tree_entry.startswith(("100644 blob ", "100755 blob ")):
        raise ProposalError("proposal evidence must be a regular file")
    if any(
        line.startswith("160000 ") for line in git("ls-tree", "-r", source).splitlines()
    ):
        raise ProposalError("submodules are not supported by this workflow")

    branch = f"agent-pr/{sha[:16]}"
    git("switch", "--create", branch, base)
    git("restore", "--source", source, "--staged", "--worktree", "--", ".")
    if git("write-tree") != git("rev-parse", f"{source}^{{tree}}"):
        raise ProposalError("replayed tree does not match proposal source")
    source_date = git("show", "-s", "--format=%cI", source)
    commit_message = (
        f"agent: replay proposal {sha[:12]}\n\n"
        f"Source-Ref: {ref}\nSource-SHA: {sha}\nEvidence-Path: {evidence}"
    )
    environment = os.environ.copy()
    environment.update(GIT_AUTHOR_DATE=source_date, GIT_COMMITTER_DATE=source_date)
    try:
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Beamo Wipe Agent",
                "-c",
                "user.email=agent@beamo.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                commit_message,
            ],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProposalError("could not commit replayed proposal") from exc
    plan = {
        "repository": REPOSITORY,
        "base_sha": base,
        "source_ref": ref,
        "source_sha": sha,
        "evidence_path": evidence,
        "branch": branch,
        "commit_sha": git("rev-parse", "HEAD"),
    }
    output.write_text(json.dumps(plan, sort_keys=True) + "\n", encoding="utf-8")
    output.chmod(0o600)
    return plan


def publish(plan_path: Path) -> str:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_ref(plan["source_ref"])
    validate_evidence(plan["evidence_path"])
    if (
        not SHA_RE.fullmatch(plan["base_sha"])
        or not SHA_RE.fullmatch(plan["source_sha"])
        or not SHA_RE.fullmatch(plan["commit_sha"])
        or plan["branch"] != f"agent-pr/{plan['source_sha'][:16]}"
        or plan["repository"] != REPOSITORY
    ):
        raise ProposalError("prepared plan is malformed")
    if (
        os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
        or os.environ.get("GITHUB_REF") != "refs/heads/main"
        or os.environ.get("GITHUB_ACTOR") != "BeamoINT"
        or os.environ.get("GITHUB_SHA") != plan["base_sha"]
        or not os.environ.get("GH_TOKEN")
    ):
        raise ProposalError("publisher identity, source, or token unavailable")
    if git("rev-parse", "HEAD") != plan["commit_sha"]:
        raise ProposalError("prepared commit changed before publication")

    remote = git("ls-remote", "--heads", "origin", plan["branch"])
    if remote:
        remote_sha = remote.split("\t", 1)[0]
        if remote_sha != plan["commit_sha"]:
            raise ProposalError("agent PR branch already exists at another commit")
    else:
        command(
            "git",
            "-c",
            "credential.helper=!gh auth git-credential",
            "push",
            "origin",
            f"HEAD:refs/heads/{plan['branch']}",
        )

    existing = command(
        "gh",
        "api",
        "--method",
        "GET",
        f"repos/{REPOSITORY}/pulls",
        "-f",
        f"head=BeamoTech:{plan['branch']}",
        "-f",
        "base=main",
        "-f",
        "state=open",
        "--jq",
        ".[0].html_url // empty",
    )
    if existing:
        return existing
    evidence_url = (
        f"https://github.com/{REPOSITORY}/blob/"
        f"{plan['source_sha']}/{plan['evidence_path']}"
    )
    body = (
        "Agent proposal replayed by the Beamo Wipe Agent GitHub App.\n\n"
        f"Source branch: `{plan['source_ref']}`\n"
        f"Source commit: `{plan['source_sha']}`\n"
        f"Replayed commit: `{plan['commit_sha']}`\n"
        f"[Agent evidence]({evidence_url})\n\n"
        "BeamoINT must inspect the source evidence and actual diff before "
        "approving. This workflow never approves a PR. The required CI gate "
        "must pass separately."
    )
    return command(
        "gh",
        "api",
        "--method",
        "POST",
        f"repos/{REPOSITORY}/pulls",
        "-f",
        f"head={plan['branch']}",
        "-f",
        "base=main",
        "-f",
        f"title=Agent proposal {plan['source_sha'][:12]}",
        "-f",
        f"body={body}",
        "--jq",
        ".html_url",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--ref", required=True)
    prepare_parser.add_argument("--sha", required=True)
    prepare_parser.add_argument("--evidence", required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            plan = prepare(args.ref, args.sha, args.evidence, args.output)
            print(f"Prepared {plan['branch']} at {plan['commit_sha']}")
        else:
            print(publish(args.plan))
    except (ProposalError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"agent PR refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
