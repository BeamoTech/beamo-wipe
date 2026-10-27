# Security

This tool permanently erases disks. Treat selection bugs as safety bugs.

## Supported versions

Only the latest published release on the
[releases page](https://github.com/BeamoTech/beamo-wipe/releases) receives
security and wipe-safety fixes. Fixes ship only as a new signed release.

A USB stick never updates itself. An older stick keeps the image it was
flashed with, including any problem fixed later. If you have an older stick,
download the latest release, check it as described in
[release verification](docs/release-verification.md), and use that image.
START-HERE.html on a stick shows which build it carries.

## How to report a vulnerability or wipe-safety bug

Report privately through GitHub private vulnerability reporting:
<https://github.com/BeamoTech/beamo-wipe/security/advisories/new>
(the repository's **Security** tab, then **Report a vulnerability**). Private
vulnerability reporting is enabled for this repository. The report stays
private between you and the repository maintainers unless an advisory is
published.

If Beamo Wipe can list the boot USB as a target, skip the confirm token, start
a wipe on boot, write logs to the target disk, or report success when nwipe
failed, **do not file a public issue with a full exploit write-up**. Use the
private report above.

Include:

- What you saw (which disk was listed / wiped)
- How you booted (VM, brand of PC)
- Beamo Wipe version / git commit, or the build shown in START-HERE.html
- nwipe version (`nwipe -V`)

If you attach a wipe report, prefer the sharing copy (`SHARE.json` and
`SHARE.txt`). It omits disk serials, hardware IDs, device paths and engine
logs. Send the original report only if we ask for it in the private report.

Do not send a “bypass so I can wipe faster” request. We will not add `--force`,
hidden partitions, or in-OS wiping of the running system disk.

UI bugs that are not selection/wipe related can use the public issue templates.

## What happens after you report

1. We acknowledge the report in the private advisory.
2. We triage it: reproduce it with fake disks or a disposable virtual machine
   where possible, decide its impact, and ask follow-up questions in the
   advisory if needed.
3. A confirmed problem is fixed in a new signed release. Existing sticks are
   not changed; affected users need to flash the new release.
4. We publish a GitHub security advisory that names the affected versions and
   the fixed release. We credit you if you want to be credited.
