# Beamo Wipe 0.2.16

This release carries the safety fixes and the offline stick check merged since
0.2.15. The exact confirmation token now ignores letter case only for plain
ASCII letters, so characters such as "ß" or the Kelvin sign no longer match
through Unicode case folding; the typing feedback follows the same rule. Opening Help & settings over the last-chance review now pauses its
five-second countdown in every view (console, Tk and GTK): Erase now stays
unavailable while the menu covers the review, and closing the menu starts a
fresh full countdown. Disk discovery treats a mounted filesystem whose type is
not reported as covering the members that share its identifier, and refuses a
mounted Btrfs row even when its type is missing.

A new read-only stick check (`scripts/check-beamo-stick.py`, see
[release verification](https://github.com/BeamoTech/beamo-wipe/blob/v0.2.16/docs/release-verification.md))
compares a written Beamo USB against the signed release's file list offline and
reports changed, missing and added files, including empty added folders. It
does not write to the stick. 0.2.16 is the first release whose signed USB
inventory carries the file list it needs. It is tested with fixtures; a stick
whose FAT short-name aliases differ is not covered yet.

The QEMU journeys that qualify each image are more reliable. The guest no
longer loses serial markers when two of its threads write at once, and it
reports which layer lost an Erase now key release and counts any marker it
could not send. These are test-harness and diagnostic changes; they do not
change what the wizard does on a customer's computer.

The design proposals merged in this period (Notion Refs 184-199: three modes,
network setup, OS catalog, Computer check, Keep my OS, installs and the
others) are documents only. None of them is built or enabled in this image.

The engine remains pinned to nwipe 0.42. The ownership checkbox, exact
confirmation token, five-second review and separate Erase now action remain
required. Hardware support and product claims remain those in
[claims](https://github.com/BeamoTech/beamo-wipe/blob/v0.2.16/docs/claims.md) and the
[compatibility matrix](https://github.com/BeamoTech/beamo-wipe/blob/v0.2.16/docs/compatibility-matrix.md).

Release qualification requires the exact-source Blacksmith Linux, ISO,
isolated KVM/QEMU and native Windows gates. The signed manifest and download
inventory identify the actual published source, artifacts and measured checks.
These checks do not establish physical-machine compatibility or physical USB
reconnect/readback. The designated signed v0.2.11 rollback target and its
recorded identity are unchanged. Existing published releases are not replaced.
