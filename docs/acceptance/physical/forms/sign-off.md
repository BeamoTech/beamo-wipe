# Session sign-off sheet (#116)

Copy this file once per session. Name the copy `signoff-<UTC date>.md`.
A session can hold many runs.

The operator signs that the records are true. The reviewer signs that the
records are complete and follow the rules. The owner decides what to claim.
No signature turns NOT TESTED into Pass, and no signature approves a release.

## Session

| Field | Value |
| --- | --- |
| Session date (UTC) | |
| Image version, file name and SHA-256 | |
| Run IDs in this session | |
| Machine IDs used | |

## Rule checks (reviewer)

| Check | Yes / No |
| --- | --- |
| Every Pass, Fail and Unknown row names a run ID and an evidence file | |
| Every evidence file has a SHA-256 in a run record | |
| No row was filled from QEMU, OVMF, SeaBIOS, a VM, Xvfb, `./preview` or CI | |
| Every destructive row has written authorization and a `DISPOSABLE` target | |
| Every PHY-COLD Pass followed a power-off and physical reconnect | |
| Secure Boot rows used an image with its own component receipt | |
| No customer data, full serials, keys or passwords are in git | |
| Rows not run are still NOT TESTED | |
| Matrix `.md` and `.csv` agree (`tests/test_physical_acceptance_116.py` passes) | |

## Results summary

| Area | Pass | Fail | Excluded | BLOCKED | Unknown | NOT TESTED |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

Fails that block a claim, with row IDs:

-

## Signatures

| Role | Initials or lab handle | Date (UTC) | Statement |
| --- | --- | --- | --- |
| Operator | | | The records describe what I saw. |
| Reviewer (not the operator) | | | The records are complete and follow the packet rules. |
| Owner | | | I have read the results. Claims follow `docs/claims.md`. |
