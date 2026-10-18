# Beamo Wipe 0.2.13

This release includes the safety and reliability fixes from the repeated bug
audits: disk discovery keeps mounted, contradictory and incomplete hardware
evidence out of the target list; malformed whole-disk names cannot lose their
partition evidence; and launch, cancellation and recovery retain conservative
ownership and completion rules.

The wizard handles keyboard focus, scrolling, modal sound checks and interrupted
background work more reliably. Tk resources and exact owned variable traces are
retired on their creating thread, including partial construction and teardown
failures. The accessible wizard completes independent cleanup after an earlier
error. Diagnostic line separators no longer make accepted JSONL events disappear
at readback.

The engine remains pinned to nwipe 0.42. The ownership checkbox, exact
confirmation token, five-second review and separate Erase now action remain
required. Hardware support and product claims remain those in
[claims](https://github.com/BeamoTech/beamo-wipe/blob/v0.2.13/docs/claims.md) and the
[compatibility matrix](https://github.com/BeamoTech/beamo-wipe/blob/v0.2.13/docs/compatibility-matrix.md).

Release qualification requires the exact-source Blacksmith Linux, ISO,
isolated KVM/QEMU and native Windows gates. The signed manifest and download
inventory identify the actual published source, artifacts and measured checks.
These checks do not establish physical-machine compatibility or physical USB
reconnect/readback. Historical abort, signal and timing incidents whose causes
remain unattributed are preserved in the audit records; passing current checks
does not retrospectively identify their causes.

The designated signed v0.2.11 rollback target and its recorded identity are
unchanged. Existing published releases are not replaced.
