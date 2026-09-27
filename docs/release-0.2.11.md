# Beamo Wipe 0.2.11

This version includes the safety and accessibility fixes made after 0.2.10:
fresh screen-reader sessions use a verified reader, boot diagnostics preserve
the correct failed-start identity, and ISO/USB inspection and QEMU tests bind
to the verified image bytes. The desktop launcher, negative disk-selection
test, and report export timing also received regression fixes.

Publication requires an x86_64 Blacksmith build and KVM verification. The
exact source commit must also pass the native Windows launcher gate. The
resulting signed manifest records the source commit, tested artifact hashes,
seven Linux gate receipts, package inventory, and QEMU evidence. The release
download inventory is separately signed with the existing Beamo Wipe publisher
key.

The erasure engine remains pinned to nwipe 0.42. QEMU results do not establish
compatibility with every physical PC or storage controller. See
[storage and controller limits](storage-and-controller-limits.md) and
[release verification](release-verification.md) before using the image.
