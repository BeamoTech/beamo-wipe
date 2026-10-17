"""Repeated malformed observations retain exclusion candidate context."""

import copy

import pytest

from test_unresolved_physical_bridge_pass17 import _rows, scan_fake  # noqa: F401 - imported pytest fixture


def _identity_only_copy(row, field, values, context):
    copied = copy.deepcopy(row)
    copied["children"] = [dict(
        name=f"fake_identity_{context}_{number}",
        path=f"/dev/mapper/fake_identity_{context}_{number}",
        type="crypt", pkname=row["name"], mountpoints=[], **{field: value},
    ) for number, value in enumerate(values, 1)]
    return copied


@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("kind", ("conflict", "malformed"))
@pytest.mark.parametrize("different", (False, True))
@pytest.mark.parametrize("reverse", (False, True))
@pytest.mark.parametrize("parent", (False, True))
def test_duplicate_invalid_observations_keep_candidate_context(
    scan_fake, field, kind, different, reverse, parent,
):
    values = ["SIDE-A", "SIDE-B"] if kind == "conflict" else ["SIDE-A", "bad\nidentity"]
    rows, _source, original, target = _rows(
        "boot", field, values, False, protected="UNRELATED-PROTECTED", leaf="FAKE-LEAF",
    )
    changed_values = (
        ["SIDE-C", "SIDE-D"] if kind == "conflict" else ["SIDE-C", "bad\nidentity"]
    ) if different else values
    # Repeating physical sda rows makes a partition's physical owner ambiguous.
    # A partition always contributes layout evidence, even without filesystem
    # metadata; that independent refusal must not be mistaken for this proof.
    # Identity-only crypt descendants have unique names and no content/layout
    # fields, so parent-authoritative copies keep identical empty layouts.
    first = _identity_only_copy(original, field, values, "first")
    second = _identity_only_copy(original, field, changed_values, "second")
    if parent:
        first[field] = second[field] = "AUTHORITATIVE-PARENT"
    copies = [second, first] if reverse else [first, second]
    rows = [row for row in rows if row is not original]
    rows[1:1] = copies
    result = scan_fake(rows)
    if different and not parent:
        assert result.error
        assert not result.boot_identified
        assert not result.selectable
    else:
        assert result.boot_identified and not result.error
        assert target["path"] in {disk.path for disk in result.selectable}
