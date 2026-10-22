# SPDX-License-Identifier: GPL-3.0-or-later
"""Evidence CLI input and output paths stay bound to verified files."""

from __future__ import annotations

import json
import os

import pytest

from beamo_wipe import release_signing, verification_evidence as evidence


def _junit() -> str:
    return (
        '<testsuite name="pytest" errors="0" failures="0" skipped="0" tests="1">'
        '<testcase classname="audit" name="control"/></testsuite>'
    )


def _parse_junit_args(source, output) -> list[str]:
    return [
        "parse-junit",
        "--gate",
        "tests",
        "--status",
        "pass",
        "--exec-command",
        "python3 -m pytest",
        "--commit",
        "a" * 40,
        "--build-id",
        "pass16",
        "--xml",
        str(source),
        "--log-sha256",
        "b" * 64,
        "--env",
        "platform=linux",
        "--started-at",
        "2026-10-21T00:00:00Z",
        "--ended-at",
        "2026-10-21T00:00:01Z",
        "--out",
        str(output),
    ]


def test_evidence_read_rejects_a_linked_parent(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "report.xml").write_text(_junit(), encoding="utf-8")
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeError, match="safely|parent"):
        evidence._read_text_file(linked / "report.xml", what="junit xml")


def test_evidence_read_rejects_a_hardlinked_input(tmp_path):
    source = tmp_path / "report.xml"
    source.write_text(_junit(), encoding="utf-8")
    alias = tmp_path / "alias.xml"
    os.link(source, alias)

    with pytest.raises(RuntimeError, match="safely|bound"):
        evidence._read_text_file(source, what="junit xml")


def test_evidence_read_detects_leaf_replacement_after_open(tmp_path, monkeypatch):
    target = tmp_path / "report.xml"
    target.write_text(_junit(), encoding="utf-8")
    replacement = tmp_path / "replacement.xml"
    replacement.write_text("<replacement/>", encoding="utf-8")
    real_open = os.open
    real_replace = os.replace
    swapped = False

    def open_then_swap(path, flags, *args, **kwargs):
        nonlocal swapped
        fd = real_open(path, flags, *args, **kwargs)
        directory_fd = kwargs.get("dir_fd")
        opens_target = (
            os.fspath(path) == os.fspath(target)
            if directory_fd is None
            else os.fspath(path) == target.name
        )
        if opens_target and not swapped:
            swapped = True
            if directory_fd is None:
                real_replace(replacement, target)
            else:
                real_replace(
                    replacement.name,
                    target.name,
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                )
        return fd

    monkeypatch.setattr(release_signing.os, "open", open_then_swap)
    with pytest.raises(RuntimeError, match="changed|safely|bound"):
        evidence._read_text_file(target, what="junit xml")

    assert swapped
    assert target.read_text(encoding="utf-8") == "<replacement/>"


def test_evidence_output_rejects_a_linked_parent(tmp_path):
    source = tmp_path / "report.xml"
    source.write_text(_junit(), encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeError, match="safely|parent"):
        evidence.main(_parse_junit_args(source, linked / "receipt.json"))

    assert list(outside.iterdir()) == []


def test_evidence_output_does_not_follow_an_existing_link(tmp_path):
    source = tmp_path / "report.xml"
    source.write_text(_junit(), encoding="utf-8")
    outside = tmp_path / "outside.json"
    outside.write_text("keep", encoding="utf-8")
    output = tmp_path / "receipt.json"
    output.symlink_to(outside)

    with pytest.raises((FileExistsError, RuntimeError)):
        evidence.main(_parse_junit_args(source, output))

    assert outside.read_text(encoding="utf-8") == "keep"


def test_evidence_regular_input_and_output_control(tmp_path):
    source = tmp_path / "report.xml"
    source.write_text(_junit(), encoding="utf-8")
    output = tmp_path / "receipt.json"

    assert evidence.main(_parse_junit_args(source, output)) == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["gate"] == "tests"
    assert receipt["measured"]["passed"] == 1
