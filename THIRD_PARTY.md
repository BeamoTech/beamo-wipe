# Third-party software

Beamo Wipe does not include a custom wipe algorithm. The only erasure
engine is **nwipe**, invoked as a separate program.

## nwipe

| Field | Value |
| --- | --- |
| Project | nwipe |
| Version (pinned) | **v0.42** (git tag `v0.42`) |
| Source | https://github.com/martijnvanbrummelen/nwipe |
| License | GNU General Public License v2.0 (GPL-2.0) |
| Authors | Martijn van Brummelen, Nick Law (@PartialVolume), and contributors |

The live image builds nwipe from that tag at the pinned commit
`6082bde060091e66365d852a1877f2ee80c67105`. If the build cannot clone
GitHub after 5 retries, it fails closed (`ERROR: git clone nwipe failed`)
and no ISO is produced. There is no fallback to the Debian `nwipe`
package (bookworm's nwipe is not 0.42). The running image records the
actual version in `/usr/share/doc/beamo-wipe/NWIPE_VERSION` and the
hook refuses to publish an ISO if that version is not `0.42`.

Beamo Wipe talks to nwipe only by executing the `nwipe` binary with
explicit device, method, and `--nogui --autonuke` flags. It does not
link against nwipe. That keeps this wrapper under GPL-3.0-or-later
while nwipe stays GPL-2.0.

Debian `live-boot`, `live-config`, GNU/Linux, Xorg, Python 3, and
Tkinter, GTK, PyGObject, AT-SPI, Orca, Speech Dispatcher, and PulseAudio
in the live image keep their own licenses (GPL, LGPL, MIT,
Apache, and others as shipped by Debian). Each package's license is in
`/usr/share/doc/<package>/copyright` inside the live system.

## Device firmware and CPU microcode

So screens, laptop audio and some USB 3 ports work on more PCs, the image
includes Debian's redistributable `non-free-firmware` packages for graphics
(AMD, Intel, NVIDIA), Intel and Cirrus audio, Renesas USB controllers and
other small device firmware, plus Intel and AMD CPU microcode. They are
vendor binaries under their own redistribution licenses, listed in
`/usr/share/doc/<package>/copyright` inside the live system; Beamo does not
modify them. No Wi-Fi or Bluetooth firmware is included. The graphics and
misc firmware and the Debian-signed Linux 6.12 kernel come from Debian's
`bookworm-backports`; everything else is Debian 12 (bookworm).

## Corresponding source (GPL)

Sticks and downloads carry GPL-covered programs: the Linux kernel, GRUB,
nwipe, live-boot and other Debian packages. `SOURCE.txt` on every USB is a
written offer, valid for at least three years after Beamo last distributes
that release, to provide the complete corresponding source to anyone who
asks through the support contact. A pointer to `deb.debian.org` alone is not
enough: superseded package versions disappear from it.

Fulfil the offer for each published release:

1. Verify the release manifest with `scripts/verify-usb-download.py`.
2. `python3 scripts/corresponding_source.py plan manifest.json --out SOURCES.json`
   maps every installed binary package in the signed dpkg inventory to its
   exact source package and version, plus the pinned nwipe and Beamo Wipe
   commits.
3. `python3 scripts/corresponding_source.py fetch SOURCES.json NEW_DIR`
   downloads each Debian source package from snapshot.debian.org, which keeps
   every published version, checks every file against snapshot's content
   hash and the `.dsc` checksums, and adds the nwipe and Beamo Wipe tarballs.
   `SHA256SUMS` and `ARCHIVE.json` list every file.
4. Store that archive privately with its checksums for at least three years
   after the release's last distribution, confirm readback, and answer
   requests from it.

The tool does not verify Debian's OpenPGP `.dsc` signatures. The offer text
and retention commitment need legal review before a commercial release.

## Trademarks

Debian is a registered trademark of Software in the Public Interest, Inc.
Beamo Wipe is not affiliated with or endorsed by the Debian Project or the
nwipe project.

## Why this is not “Beamo SecureErase Engine”

Do not rename nwipe in the UI, ISO volume label aside, or marketing.
The first wizard screen, this file, `NOTICE`, and `docs/boot-card.md`
must keep saying: the engine is nwipe.

## Desktop launcher runtime

The standalone Windows and Linux launchers are compiled with Go 1.26.8 and
include its runtime and standard library. Go is copyright The Go Authors and
uses the BSD 3-Clause license. The USB root includes `GO-LICENSE.txt` and
`GO-PATENTS.txt`; source is available at https://go.dev/dl/. The launcher has
no external Go module dependencies. Its Beamo source remains GPL-3.0-or-later.
