# SPDX-License-Identifier: GPL-3.0-or-later
"""UI language selection. English is the source; French, German, Spanish and
Italian tables in locales/ override module attributes. Tables hold data only
(never functions); builders format translated templates, and modules with
derived text rebuild it in _apply_language().
"""

from __future__ import annotations

import importlib

LANGUAGE_ORDER = ("en", "fr", "de", "es", "it")

# Own-language names. Never translated, never in the tables.
LANGUAGE_NAMES = {
    "en": "English",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "it": "Italiano",
}

# Translated modules in dependency order: a module's _apply_language() may
# read another module's already-translated attributes (copy reads outcomes,
# methods, inventory, storage_limits), so leaves come first and copy last.
TRANSLATED_MODULES = (
    "methods",
    "outcomes",
    "inventory",
    "storage_limits",
    "identity",
    "keyboard",
    "power",
    "progress",
    "engine_checks",
    "result_summary",
    "privacy",
    "diagnostic_report",
    "session_recovery",
    "safety",
    "discover",
    "models",
    "sound",
    "app",
    "wizard",
    "support_export",
    "copy",
    "recovery",
)

_current = "en"
_SNAPSHOT = None


def _modules():
    return {
        name: importlib.import_module(f"beamo_wipe.{name}")
        for name in TRANSLATED_MODULES
    }


def _tables(code: str):
    if code == "en":
        return {}
    module = importlib.import_module(f"beamo_wipe.locales.{code}")
    return module.STRINGS


def _snapshot():
    """English values for every translated name. Fails fast on typos."""
    global _SNAPSHOT
    if _SNAPSHOT is None:
        modules = _modules()
        snap = {}
        for module_name, table in _tables("fr").items():
            module = modules[module_name]
            snap[module_name] = {name: getattr(module, name) for name in table}
        _SNAPSHOT = snap
    return _SNAPSHOT


def current() -> str:
    return _current


def is_supported(code: object) -> bool:
    return isinstance(code, str) and code in LANGUAGE_ORDER


def surface():
    """{module: {name: english value}} for the translated surface."""
    return {module: dict(names) for module, names in _snapshot().items()}


def keys(code: str, module: str):
    if code == "en":
        return list(_snapshot()[module])
    return list(_tables(code)[module])


def english(module: str, name: str):
    return _snapshot()[module][name]


def translated(code: str, module: str, name: str):
    return _tables(code)[module][name]


def _apply_hook(module) -> None:
    hook = getattr(module, "_apply_language", None)
    if callable(hook):
        hook()


def set_language(code: str) -> str:
    """Apply a language to every translated module. Restores English exactly."""
    if not is_supported(code):
        raise ValueError(f"unsupported language: {code!r}")
    global _current
    modules = _modules()
    # Capture source English values before the first non-English table can
    # overwrite them. A later switch back to English must restore the same
    # values even when no caller requested surface() at startup.
    english_values = _snapshot()
    if code == "en":
        for module_name in TRANSLATED_MODULES:
            names = english_values.get(module_name, {})
            for name, value in names.items():
                setattr(modules[module_name], name, value)
            _apply_hook(modules[module_name])
    else:
        tables = _tables(code)
        for module_name in TRANSLATED_MODULES:
            for name, value in tables[module_name].items():
                setattr(modules[module_name], name, value)
            _apply_hook(modules[module_name])
    _current = code
    return code


_REVERSE = None


def _reverse_index():
    """{text: {(module, name), ...}} for every language's constant strings."""
    global _REVERSE
    if _REVERSE is None:
        index: dict = {}
        for code in LANGUAGE_ORDER:
            tables = _snapshot() if code == "en" else _tables(code)
            for module_name, names in tables.items():
                for name, value in names.items():
                    if isinstance(value, str):
                        index.setdefault(value, set()).add((module_name, name))
        _REVERSE = index
    return _REVERSE


def current_text(text: str) -> str:
    """A stored constant string, in the current language.

    Text kept from before a language switch (discovery runs before the owner
    picks one) maps to the current value of the translated constant it equals
    in any language, or to two such constants joined. Formatted, unknown or
    ambiguous text is returned as is.
    """
    if not isinstance(text, str):
        return text
    whole = _current_constant(text)
    if whole is not None:
        return whole
    # Two constants joined, such as the keyboard notice GRAPHICAL_ONLY +
    # SESSION_ONLY. Both halves must be exact, unambiguous constants.
    for head in _reverse_index():
        if head and len(head) < len(text) and text.startswith(head):
            first = _current_constant(head)
            second = _current_constant(text[len(head):])
            if first is not None and second is not None:
                return first + second
    return text


def _current_constant(text: str) -> str | None:
    keys = _reverse_index().get(text)
    if not keys:
        return None
    modules = _modules()
    current = {getattr(modules[module_name], name) for module_name, name in keys}
    if len(current) != 1:
        return None
    (value,) = current
    return value if isinstance(value, str) else None
