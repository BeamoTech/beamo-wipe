# Beamo Wipe 0.2.15

This release carries the audit-boundary hardening and the accessibility,
translation and test-harness fixes merged since 0.2.14. Audit records keep
their boundaries through interrupted runs, and verification that was cut short
can resume without reporting an unfinished check as complete.

In the GTK result screen, an Orca user keeps their place when the screen
rebuilds, and an open Keyboard shortcuts section stays open across a Done
rebuild. The screen's handling of the first report USB answer is now tested. French, German,
Spanish and Italian strings were corrected after a native-quality review, and
the German Working screen shows its run time as "Laufzeit". The helper page's
USB and power wording now matches the app.

The QEMU journeys that qualify each image are more reliable: the BIOS boot
hotkey and its Return go in one input command, the Erase now press is accepted
from either result marker, and the wizard reports where a Return release is
lost. A two-disk dry run with the carried ownership tick is now tested. A
manual probe checks that the screen stays awake through a long erase; it ran
once in QEMU and is not a physical-machine result.

The engine remains pinned to nwipe 0.42. The ownership checkbox, exact
confirmation token, five-second review and separate Erase now action remain
required. Hardware support and product claims remain those in
[claims](https://github.com/BeamoTech/beamo-wipe/blob/v0.2.15/docs/claims.md) and the
[compatibility matrix](https://github.com/BeamoTech/beamo-wipe/blob/v0.2.15/docs/compatibility-matrix.md).

Release qualification requires the exact-source Blacksmith Linux, ISO,
isolated KVM/QEMU and native Windows gates. The signed manifest and download
inventory identify the actual published source, artifacts and measured checks.
These checks do not establish physical-machine compatibility or physical USB
reconnect/readback. The designated signed v0.2.11 rollback target and its
recorded identity are unchanged. Existing published releases are not replaced.
