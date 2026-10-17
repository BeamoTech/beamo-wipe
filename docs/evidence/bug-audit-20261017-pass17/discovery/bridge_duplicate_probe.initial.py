"""Unexecuted proposed duplicate-context extension to the bridge probe."""

import copy

import pytest

from bridge_probe import _bridge, _rows, scan_fake  # noqa: F401 - imported pytest fixture


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
    first, second = copy.deepcopy(original), _bridge(field, changed_values, False)
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
