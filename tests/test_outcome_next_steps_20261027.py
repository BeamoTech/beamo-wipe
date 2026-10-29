# SPDX-License-Identifier: GPL-3.0-or-later
"""Each failed or uncertain result names its own next steps, in every language.

Fake evidence, fake logs, DryRunRunner and private Tk/curses surfaces only.
"""

from __future__ import annotations

import re

import pytest

from beamo_wipe import lang, outcomes
from beamo_wipe.outcomes import NOTHING_ERASED_CODES, may_have_erased
from test_result_presentations import CASES, case_evidence
from test_tk_runtime import ui  # noqa: F401

# Every outcome that used to show only the shared generic text.
SPECIFIC_CODES = (
    "open_failed",
    "geometry_unusable",
    "verification_failed",
    "interrupted",
    "cancelled",
    "completion_missing",
    "process_failed",
    "engine_failed",
    "indeterminate",
)
STOPPED_CODES = ("interrupted", "cancelled")

# The former shared SUPPORT text, byte for byte, before outcome-specific steps.
FORMER_GENERIC = {
    "en": (
        "Files may still be on the disk. Save the report if available and "
        "contact support. Shut down before disconnecting."
    ),
    "fr": (
        "Des fichiers sont peut-être encore sur le disque. Enregistrez le rapport "
        "si possible et contactez l’assistance. Éteignez avant de débrancher."
    ),
    "de": (
        "Es können noch Dateien auf dem Datenträger sein. Speichern Sie den "
        "Bericht, wenn verfügbar, und wenden Sie sich an den Support. Fahren Sie "
        "herunter, bevor Sie trennen."
    ),
    "es": (
        "Es posible que todavía haya archivos en el disco. Guarde el informe si "
        "está disponible y contacte con el soporte técnico. Apague antes de "
        "desconectar."
    ),
    "it": (
        "Sul disco potrebbero esserci ancora dei file. Salvi il rapporto, se "
        "disponibile, e contatti l’assistenza. Spenga il computer prima di "
        "scollegare."
    ),
}
REMAIN = {
    "en": "Files may still be on the disk.",
    "fr": "Des fichiers sont peut-être encore sur le disque.",
    "de": "Es können noch Dateien auf dem Datenträger sein.",
    "es": "Es posible que todavía haya archivos en el disco.",
    "it": "Sul disco potrebbero esserci ancora dei file.",
}
SAVE = {
    "en": "save the report if available",
    "fr": "enregistrez le rapport si possible",
    "de": "speichern sie den bericht, wenn verfügbar",
    "es": "guarde el informe si está disponible",
    "it": "salvi il rapporto, se disponibile",
}
SUPPORT = {
    "en": "contact support",
    "fr": "contactez l’assistance",
    "de": "wenden sie sich an den support",
    "es": "contacte con el soporte técnico",
    "it": "contatti l’assistenza",
}
SHUT_DOWN = {
    "en": "shut down",
    "fr": "éteignez",
    "de": "fahren sie herunter",
    "es": "apague",
    "it": "spenga il computer",
}
RESTART = {
    "en": "start again from the beginning",
    "fr": "recommencez depuis le début",
    "de": "erneut von vorn",
    "es": "vuelva a empezar desde el principio",
    "it": "ricominci dall’inizio",
}
NOT_ERASED = {
    "en": "do not treat or sell it as erased",
    "fr": "ne le considérez ni ne le vendez comme effacé",
    "de": "behandeln oder verkaufen sie ihn nicht als gelöscht",
    "es": "no lo trate ni lo venda como borrado",
    "it": "non lo consideri né lo venda come cancellato",
}
DESTROY = {
    "en": "consider replacing or physically destroying it",
    "fr": "envisagez de le remplacer ou de le détruire physiquement",
    "de": "erwägen sie, ihn zu ersetzen oder physisch zu zerstören",
    "es": "considere sustituirlo o destruirlo físicamente",
    "it": "valuti di sostituirlo o di distruggerlo fisicamente",
}
WHOLE_DISK = {
    "en": "to erase the whole disk",
    "fr": "pour effacer tout le disque",
    "de": "um den ganzen datenträger zu löschen",
    "es": "para borrar todo el disco",
    "it": "per cancellare l’intero disco",
}
REPEATS = {
    "en": "if this repeats",
    "fr": "si cela se reproduit",
    "de": "wenn das wieder auftritt",
    "es": "si se repite",
    "it": "se il problema si ripete",
}
OPEN_RESTART = {
    "en": "then start again",
    "fr": "puis recommencez",
    "de": "beginnen sie dann erneut",
    "es": "vuelva a empezar",
    "it": "poi ricominci",
}
# Actionable hints that are true for exactly one outcome and appear nowhere else.
HINTS = {
    "open_failed": {
        "en": ("check the disk's connection", "avoid usb hubs"),
        "fr": ("vérifiez le branchement du disque", "évitez les hubs usb"),
        "de": ("prüfen sie den anschluss des datenträgers", "vermeiden sie usb-hubs"),
        "es": ("revise la conexión del disco", "evite los hubs usb"),
        "it": ("controlli il collegamento del disco", "eviti gli hub usb"),
    },
    "geometry_unusable": {
        "en": ("contact support before trying this disk again",),
        "fr": ("contactez l’assistance avant de réessayer avec ce disque",),
        "de": ("bevor sie es mit diesem datenträger erneut versuchen",),
        "es": ("antes de volver a intentarlo con este disco",),
        "it": ("prima di riprovare con questo disco",),
    },
    "verification_failed": {
        "en": ("may be unreliable",),
        "fr": ("n’est peut-être pas fiable",),
        "de": ("möglicherweise unzuverlässig",),
        "es": ("no sea fiable",),
        "it": ("potrebbe essere inaffidabile",),
    },
    "engine_failed": {
        "en": ("may be failing",),
        "fr": ("peut-être défaillant",),
        "de": ("möglicherweise defekt",),
        "es": ("esté fallando",),
        "it": ("potrebbe essere guasto",),
    },
    "cancelled": {
        "en": ("for help",),
        "fr": ("pour obtenir de l’aide",),
        "de": ("wenn sie hilfe brauchen",),
        "es": ("si necesita ayuda",),
        "it": ("se ha bisogno di aiuto",),
    },
    "completion_missing": {
        "en": ("if the result is the same",),
        "fr": ("si le résultat est le même",),
        "de": ("wenn das ergebnis gleich bleibt",),
        "es": ("si el resultado es el mismo",),
        "it": ("se il risultato è lo stesso",),
    },
    "process_failed": {
        "en": ("if it fails again",),
        "fr": ("si l’effacement échoue encore",),
        "de": ("wenn es wieder fehlschlägt",),
        "es": ("si vuelve a fallar",),
        "it": ("se l’operazione non riesce di nuovo",),
    },
    "indeterminate": {
        "en": ("do not sell or give away the disk until an erase is confirmed",),
        "fr": ("ne vendez ni ne donnez le disque tant qu’un effacement n’est pas confirmé",),
        "de": ("verkaufen oder verschenken sie den datenträger erst, wenn ein löschen bestätigt ist",),
        "es": ("no venda ni regale el disco hasta que se confirme un borrado",),
        "it": ("non venda né regali il disco finché una cancellazione non è confermata",),
    },
}
NO_PROMISES = (
    "minute", "hour", "second", "heure", "stunde", "sekunde", "minuto", "hora",
    "segundo", "certif", "dod", "plug and play", "guarant", "garanti", "secure",
    "sécuris", "sicher gelöscht", "seguro", "minuti", "secondi", "sicur",
)
FAILURE_CASES = [case for case in CASES if case[0] in SPECIFIC_CODES]


@pytest.fixture
def language():
    """Switch the whole UI language for one test and always restore English."""

    def use(code: str) -> None:
        lang.set_language(code)

    yield use
    lang.set_language("en")


def _views(code: str) -> dict[str, outcomes.ResultView]:
    lang.set_language(code)
    return dict(outcomes.VIEWS)


def test_former_generic_text_is_the_reference_translation(language):
    # Guards the baseline itself: the shared lead and stop warning are the
    # unchanged first sentences of the old generic text in every language.
    for code in lang.LANGUAGE_ORDER:
        language(code)
        assert outcomes.FILES_MAY_REMAIN == REMAIN[code]
        assert FORMER_GENERIC[code].startswith(REMAIN[code] + " ")
    assert set(SPECIFIC_CODES) | {"start_failed", "occupied", "stop_unconfirmed"} == {
        code for code, view in outcomes.VIEWS.items() if not view.success
    }


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_every_failure_has_its_own_next_steps(code, language):
    views = _views(code)
    stop = outcomes.STOP_WARNING
    # The byte-for-byte former text and the live translated SUPPORT key.
    generics = {FORMER_GENERIC[code], outcomes.SUPPORT}
    for outcome in SPECIFIC_CODES:
        step = views[outcome].next_step
        for generic in generics:
            assert step != generic, (code, outcome)
            assert step != f"{stop} {generic}", (code, outcome)
        assert len(step) > len(REMAIN[code]) + 40, (code, outcome)
    # No result shows the former shared text, even as part of its steps.
    for outcome, view in views.items():
        for generic in generics:
            assert generic not in view.next_step, (code, outcome)
    steps = [view.next_step for view in views.values()]
    # Every outcome code, including the unchanged ones, names distinct steps.
    assert len(set(steps)) == len(steps), code
    assert len({views[o].announcement for o in SPECIFIC_CODES}) == len(SPECIFIC_CODES)


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_unproven_erases_keep_files_may_remain(code, language):
    views = _views(code)
    for outcome in SPECIFIC_CODES:
        step = views[outcome].next_step
        if outcome in STOPPED_CODES:
            assert step.startswith(f"{outcomes.STOP_WARNING} {REMAIN[code]} "), (code, outcome)
        else:
            assert step.startswith(f"{REMAIN[code]} "), (code, outcome)
    # Every result that may have erased part of the disk, or is uncertain,
    # says files may remain. stop_unconfirmed keeps its own "may still be
    # running" warning, which is stronger than a finished-result statement.
    uncertain = {
        outcome for outcome, view in views.items()
        if not view.success and may_have_erased(outcome)
    }
    assert uncertain == {
        "verification_failed", "interrupted", "cancelled", "completion_missing",
        "process_failed", "engine_failed", "indeterminate", "stop_unconfirmed",
    }
    for outcome in uncertain - {"stop_unconfirmed"}:
        assert REMAIN[code] in views[outcome].next_step, (code, outcome)
    assert outcomes.NEXT_STOP_UNCONFIRMED == views["stop_unconfirmed"].next_step
    # Nothing-erased failures also keep the sentence; their recovery meaning
    # separately says the disk is unchanged.
    for outcome in ("open_failed", "geometry_unusable"):
        assert outcome in NOTHING_ERASED_CODES
        assert REMAIN[code] in views[outcome].next_step


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_next_steps_save_report_before_shutdown_and_name_support(code, language):
    views = _views(code)
    for outcome in SPECIFIC_CODES:
        step = views[outcome].next_step.lower()
        assert SAVE[code] in step, (code, outcome)
        assert SUPPORT[code] in step, (code, outcome)
        assert SHUT_DOWN[code] in step, (code, outcome)
        # Saved reports live in RAM until exported: saving comes first.
        assert step.index(SAVE[code]) < step.index(SHUT_DOWN[code]), (code, outcome)
        assert not re.search(r"\d", step), (code, outcome)
        for word in NO_PROMISES:
            assert word not in step, (code, outcome, word)
        assert "try again" not in step and "retry" not in step


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_actionable_hints_match_their_outcome(code, language):
    views = _views(code)
    for outcome, by_language in HINTS.items():
        step = views[outcome].next_step.lower()
        for hint in by_language[code]:
            assert hint in step, (code, outcome, hint)
        # Hints that are only true for one outcome stay there.
        for other in views:
            if other == outcome:
                continue
            for hint in by_language[code]:
                assert hint not in views[other].next_step.lower(), (code, outcome, other, hint)
    # A connection problem and a system interruption both retry, then escalate.
    assert OPEN_RESTART[code] in views["open_failed"].next_step.lower()
    for outcome in ("open_failed", "interrupted"):
        assert REPEATS[code] in views[outcome].next_step.lower(), (code, outcome)
    for outcome in ("verification_failed", "engine_failed"):
        step = views[outcome].next_step.lower()
        assert NOT_ERASED[code] in step and DESTROY[code] in step, (code, outcome)
    for outcome in SPECIFIC_CODES:
        if outcome not in {"verification_failed", "engine_failed"}:
            assert DESTROY[code] not in views[outcome].next_step.lower(), (code, outcome)
    for outcome in ("interrupted", "cancelled", "completion_missing", "process_failed"):
        assert RESTART[code] in views[outcome].next_step.lower(), (code, outcome)
    for outcome in STOPPED_CODES:
        assert WHOLE_DISK[code] in views[outcome].next_step.lower(), (code, outcome)
    # Geometry problems go to support, not to a blind restart.
    assert RESTART[code] not in views["geometry_unusable"].next_step.lower()
    assert "hub" not in views["geometry_unusable"].next_step.lower()


def test_typed_console_words_and_tokens_are_not_introduced():
    from beamo_wipe import copy as C

    for code in lang.LANGUAGE_ORDER:
        try:
            lang.set_language(code)
            for outcome in SPECIFIC_CODES:
                step = outcomes.VIEWS[outcome].next_step
                assert "{" not in step and "}" not in step
                assert C.VIEWS[outcome] == outcomes.VIEWS[outcome]
        finally:
            lang.set_language("en")


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("case", FAILURE_CASES, ids=[c[0] for c in FAILURE_CASES])
def test_report_text_carries_the_whole_next_step(code, case, language):
    from beamo_wipe import recovery as R
    from beamo_wipe import result_summary as S
    from beamo_wipe.result_summary import build_result_report_html, build_result_summary

    language(code)
    _, ev, _ = case_evidence(case)
    view = outcomes.VIEWS[case[0]]
    assert ev["presentation"]["next_step"] == view.next_step
    text = build_result_summary(ev, evidence_sha256="a" * 64)
    assert f"{R.RECOVERY_NEXT}: {view.next_step}" in text.splitlines()
    # Translated canonical copy is never cut by the untrusted-value limit.
    assert f"{S.H_LIMITATIONS}: {view.next_step}" in text.splitlines()
    import html

    page = build_result_report_html(ev, evidence_sha256="a" * 64)
    assert html.escape(view.next_step, quote=True) in page
    assert html.escape(view.announcement, quote=True) in page


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_every_report_limitation_stays_whole(code, language):
    from beamo_wipe import result_summary as S
    from beamo_wipe.result_summary import build_result_summary

    language(code)
    for case in CASES:
        _, ev, _ = case_evidence(case)
        view = outcomes.VIEWS[case[0]]
        text = build_result_summary(ev, evidence_sha256="a" * 64)
        limitation = f"{S.H_LIMITATIONS}: {view.next_step}"
        assert limitation in text.splitlines(), (code, case[0])
        assert not limitation.endswith(S.TRUNCATED_SUFFIX), (code, case[0])


def test_untrusted_values_are_still_bounded():
    from beamo_wipe.result_summary import MAX_VALUE, TRUNCATED_SUFFIX, sanitize_value

    long = "x " * MAX_VALUE
    assert sanitize_value(long).endswith(TRUNCATED_SUFFIX)
    assert len(sanitize_value(long)) <= MAX_VALUE + len(TRUNCATED_SUFFIX)


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_readme_announces_specific_next_step(code, language):
    import json

    from beamo_wipe.support_export import _bundle_files

    language(code)
    for case in FAILURE_CASES:
        _, ev, log = case_evidence(case)
        view = outcomes.VIEWS[case[0]]
        bundle = _bundle_files(json.dumps(ev).encode(), log.encode(), "complete")
        assert view.announcement in bundle["README.txt"].decode(), (code, case[0])
        assert FORMER_GENERIC[code] not in bundle["README.txt"].decode(), (code, case[0])


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_console_result_fits_80x24_in_every_language(code, monkeypatch, language):
    from test_console_parity import _draw

    language(code)
    for case in FAILURE_CASES:
        wiz, _, _ = case_evidence(case)
        shown, _, term = _draw(monkeypatch, wiz)
        view = wiz.result_view
        assert view.code == case[0]
        assert view.message in shown, (code, case[0])
        assert view.next_step in shown, (code, case[0])
        assert all(len(line) < 80 for line in term.frames[-1].values()), (code, case[0])
        assert max(term.frames[-1]) < 24, (code, case[0])
        # The outcome is the page title and is not repeated in the body, so
        # the longer next steps still leave Report status on the first page.
        from beamo_wipe import copy as C

        first = " ".join(term.frames[0][y] for y in sorted(term.frames[0]))
        assert first.count(view.message) == 1, (code, case[0])
        assert C.REPORT_STATUS_TITLE in first, (code, case[0])
        wiz.wants_shutdown = False


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("case", FAILURE_CASES, ids=[c[0] for c in FAILURE_CASES])
def test_tk_result_fits_800x600_in_every_language(code, case, ui, language):  # noqa: F811
    from beamo_wipe import copy as C
    from beamo_wipe.ui.layout import MIN_SIZE
    from test_adaptive_layout import _assert_actions_on_window, _buttons, _texts

    language(code)
    wiz, _, _ = case_evidence(case)
    view = wiz.result_view
    assert view.code == case[0]
    _, app = ui(size=MIN_SIZE)
    app.w = wiz
    app.root.minsize(*MIN_SIZE)
    app.root.geometry(f"{MIN_SIZE[0]}x{MIN_SIZE[1]}+40+40")
    app._draw()
    app.root.update_idletasks()
    app.root.update()
    shown = _texts(app.root)
    assert view.message in shown
    assert view.next_step in shown
    assert wiz.selected.display_name in shown
    labels = [b.itemcget(b._label, "text") for b in _buttons(app) if b.winfo_ismapped()]
    assert C.BTN_SHUTDOWN in labels
    _assert_actions_on_window(app)


LONGEST_CASES = [c for c in FAILURE_CASES if c[0] in {"verification_failed", "interrupted"}]


@pytest.mark.parametrize("case", LONGEST_CASES, ids=[c[0] for c in LONGEST_CASES])
def test_tk_recovered_german_result_still_fits_800x600(case, ui, language):  # noqa: F811
    from beamo_wipe import session_recovery
    from beamo_wipe.ui.layout import MIN_SIZE
    from test_adaptive_layout import _assert_actions_on_window, _texts

    language("de")
    wiz, _, _ = case_evidence(case)
    # The longest owner text: recovery notice before the German next step.
    wiz._recovered = True
    view = wiz.result_view
    assert view.next_step == f"{session_recovery.NOTICE} {outcomes.VIEWS[case[0]].next_step}"
    _, app = ui(size=MIN_SIZE)
    app.w = wiz
    app.root.minsize(*MIN_SIZE)
    app.root.geometry(f"{MIN_SIZE[0]}x{MIN_SIZE[1]}+40+40")
    app._draw()
    app.root.update_idletasks()
    app.root.update()
    shown = _texts(app.root)
    assert view.next_step in shown
    _assert_actions_on_window(app)
