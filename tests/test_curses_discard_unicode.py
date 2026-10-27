"""Literal localized confirmation using the shipped UTF-8 console input."""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest


def _confirmation():
    path = Path(__file__).resolve().parents[1] / "src/beamo_wipe/ui/console_wizard.py"
    tree = ast.parse(path.read_bytes())
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_confirm_report_discard"
    )
    namespace = {
        "C": SimpleNamespace(CON_TYPE_OR_RETURN="{word}"),
        "_add": lambda *args: None,
        "_curses_opt": lambda *args: None,
    }
    module = ast.Module(
        body=ast.parse("from __future__ import annotations").body + [function],
        type_ignores=[],
    )
    exec(compile(module, str(path), "exec"), namespace)  # noqa: S102 - checked-in AST, inert UI globals
    return namespace["_confirm_report_discard"]


@pytest.mark.parametrize("phrase", [
    "Shut down without saving",
    "Éteindre sans enregistrer",
    "Ohne Speichern herunterfahren",
    "Continue without saving",
    "Continuer sans enregistrer",
    "Ohne Speichern fortfahren",
])
@pytest.mark.parametrize("answer_kind", ["exact", "lowercase", "truncated", "invalid", "empty"])
def test_curses_requires_exact_localized_discard(phrase, answer_kind):
    expected = phrase.upper()
    answer = {
        "exact": expected.encode("utf-8"),
        "lowercase": phrase.lower().encode("utf-8"),
        "truncated": expected.encode("utf-8")[:-1],
        "invalid": b"\xff" + expected.encode("utf-8"),
        "empty": b"",
    }[answer_kind]
    actions = []
    modes = []
    wizard = SimpleNamespace(
        shutdown_generation=17,
        exit_confirmation_discard=phrase,
        confirm_shutdown_without_saving=lambda generation: actions.append(("confirm", generation)),
        keep_report_session=lambda: actions.append(("keep",)),
    )
    terminal = SimpleNamespace(
        getmaxyx=lambda: (24, 80),
        nodelay=modes.append,
        refresh=lambda: None,
        getstr=lambda *args: answer,
    )
    _confirmation()(terminal, wizard)
    assert actions == ([("confirm", 17)] if answer_kind == "exact" else [("keep",)])
    assert modes == [False, True]


def test_curses_captures_generation_before_reading():
    actions = []
    wizard = SimpleNamespace(
        shutdown_generation=3,
        exit_confirmation_discard="Éteindre sans enregistrer",
        confirm_shutdown_without_saving=lambda generation: actions.append(generation),
        keep_report_session=lambda: None,
    )

    def read(*args):
        wizard.shutdown_generation = 4
        return wizard.exit_confirmation_discard.upper().encode("utf-8")

    terminal = SimpleNamespace(
        getmaxyx=lambda: (24, 80), nodelay=lambda value: None,
        refresh=lambda: None, getstr=read,
    )
    _confirmation()(terminal, wizard)
    assert actions == [3]
