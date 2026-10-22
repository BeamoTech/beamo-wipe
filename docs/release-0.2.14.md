# Beamo Wipe 0.2.14

This release completes the safety and reliability work from the latest repeated
bug audits. Disk discovery and launch now keep ambiguous, contradictory,
mounted, boot-related and stale hardware evidence out of the selectable target
set. Confirmation, startup, cancellation, recovery, evidence publication and
desktop handoff retain conservative ownership rules through interrupted and
late operations.

The wizard and desktop launcher handle keyboard input, focus, modal work,
thread-owned resources, process output and shutdown more reliably. Diagnostic,
result and support records bind their source, identity, locale and final byte
snapshot so incomplete or replaced evidence cannot be reported as a verified
success.

Release transfer, signing and publication now bind the qualified source, exact
tested files, signed inventory, GitHub release record and immutable tag through
the final public verification. Publication fails closed and restores the exact
verified draft when the remote release or tag no longer matches.

The engine remains pinned to nwipe 0.42. The ownership checkbox, exact
confirmation token, five-second review and separate Erase now action remain
required. Hardware support and product claims remain those in
[claims](https://github.com/BeamoTech/beamo-wipe/blob/v0.2.14/docs/claims.md) and the
[compatibility matrix](https://github.com/BeamoTech/beamo-wipe/blob/v0.2.14/docs/compatibility-matrix.md).

Release qualification requires the exact-source Blacksmith Linux, ISO,
isolated KVM/QEMU and native Windows gates. The signed manifest and download
inventory identify the actual published source, artifacts and measured checks.
These checks do not establish physical-machine compatibility or physical USB
reconnect/readback. The designated signed v0.2.11 rollback target and its
recorded identity are unchanged. Existing published releases are not replaced.
