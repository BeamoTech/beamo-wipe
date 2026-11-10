# Decision record: SSD firmware erase (ATA Secure Erase, ATA Sanitize, NVMe Sanitize and Format)

> **Status: DECIDED 2026-11-10 — Option A (keep nwipe overwrite only). See §12 for the
> recorded answers. Backlog #186, UI review item 60; related #158.**
>
> Original status: PROPOSAL, owner decision required.
> Prepared 2026-11-07 and source-checked 2026-11-08 by Claude (Opus 5.5) on branch
> `docs/ssd-erase-decision-186` from `84efc57`. Research and decision only: no code, no `docs/claims.md`
> change and no product-copy change. Today's rules stay in force until the
> owner changes `AGENTS.md` and `docs/claims.md` explicitly.

## Summary for the owner (plain English)

1. Today Beamo Wipe only overwrites a disk with nwipe. On SSDs that cannot
   reach the spare areas the disk keeps for itself, so we show a limits warning.
2. Most SSDs also have their own built-in erase command. When it is
   implemented correctly it is faster and reaches more of the disk than an overwrite.
3. But it is the disk maker's code, it is sometimes buggy, and from outside we
   cannot fully check what it did. One study found a disk that said "done" and erased nothing.
4. The old ATA "Secure Erase" needs a temporary disk password. If it is
   interrupted the disk can stay locked. We recommend never using it.
5. The NVMe "Sanitize" command is the safest of these commands. It
   continues after a power cut and it reports a status we can show.
6. Many computers block these commands at start-up ("frozen"). The usual
   workaround is sleep/resume, and that is risky on unknown laptops. We recommend no workaround.
7. Through USB enclosures, RAID and Intel VMD setups these commands are
   often blocked or unsafe, so we would refuse them there.
8. Recommendation: keep today's overwrite as the product for now. Then, only if
   you approve, add NVMe Sanitize step by step, on internal NVMe disks only, after the normal overwrite.
9. That needs a real hardware test lab with spare disks. This remote-only computer
   cannot do it. Rough effort is 8 to 12 engineer-weeks plus the lab (estimate, unverified).
10. It changes the rules ("nwipe only") and up to four lines of the listing
    claims. Nothing changes until you decide the points in §12.

## 1. Decision needed and the rules that apply today

The UI review (item 60) found that most modern computers have SSDs. Those get the
weaker overwrite plus a large limits warning. The owner asked whether Beamo Wipe should use the
disk's own erase command (ATA Secure Erase, ATA Sanitize, NVMe Sanitize or NVMe
Format with Secure Erase Settings).

Current rules that a "yes" would change (quoted exactly):

- `AGENTS.md`, Project: "Beamo Wipe does not implement a wipe engine. It
  discovers disks, refuses to target the boot USB, walks a non-technical owner
  through confirms, then execs pinned **nwipe v0.42**."
- `AGENTS.md`, Safety boundaries: "Erasure = the `nwipe` binary only. No
  ATA/NVMe sanitize engine, no custom overwrite loop."
- Task #186 fixed constraints: "No custom erase engine, no ATA/NVMe sanitize,
  no password/BitLocker work."
- `docs/storage-and-controller-limits.md` §2: "Beamo does not invoke `hdparm`
  or `smartctl`." and "No ATA/NVMe sanitize command is issued."
- Canonical offline limits (shown in the product): "It does not issue
  controller secure-erase or sanitize commands."

This document does not change any of them.

## 2. What the product does today (checked in this session)

| Fact | Evidence |
|---|---|
| Only pinned nwipe v0.42 (`6082bde060091e66365d852a1877f2ee80c67105`) is executed, with `--method=prng\|dodshort\|zero`, one positional target, `--exclude=` the Beamo USB, never `--force`. | `src/beamo_wipe/nwipe_runner.py: build_nwipe_argv()`, `validate_argv()`; `docs/ADVANCED.md` |
| nwipe v0.42 has **no firmware-erase method**. Its method list is dod522022m (dod), dodshort, gutmann, ops2, random/prng/stream, zero, one, verify_zero, verify_one, is5enh, bruce7 and bmb. All of them are host overwrites or reads. | `man/nwipe.8` at the pinned commit (SHA-256 `484f9585…cb9c32`); v0.42 release notes list no secure-erase or sanitize feature |
| nwipe's own README (pinned commit) says it "cannot fully sanitise" SSDs. It recommends combining it with "manufacturer Secure Erase", "NVMe format / sanitize commands" or vendor utilities, and validating the result independently. | `README.md` SHA-256 `06d89dd9…209581` (same hash recorded in `docs/method-and-storage-wording-validation.md`) |
| nwipe's `ssd-guide.md` advises: firmware sanitize, then one nwipe PRNG pass with verification, then firmware sanitize again, then validate. Its vendor table marks SK Hynix, Kioxia, Micron, Kingston and others "Unconfirmed for Linux". | `ssd-guide.md` SHA-256 `df3477a7…123ec0d` |
| A ShredOS discussion once said ATA Secure Erase was planned for nwipe 0.35/0.36. It is **not** present in v0.42. | ShredOS discussion #156; v0.42 method list above |
| `hdparm` is in the image only because nwipe calls `hdparm --verbose -N` / `--dco-identify` to read HPA/DCO. nwipe's warning text names "ATA secure erase", but v0.42 has no code path that issues it. | `packaging/live/config/package-lists/beamo.list.chroot` comment; nwipe `src/hpa_dco.c` lines 62–106 |
| `nvme-cli` is **not** in the image. | `beamo.list.chroot` |
| Suspend is disabled in the live session (`AllowSuspend=no`, masked `suspend.target`, sleep keys and lid ignored). | `docs/live-session-power.md`; `packaging/live/config/includes.chroot/etc/systemd/sleep.conf.d/beamo-kiosk.conf` |
| Before nwipe starts, the runner holds the confirmed disk open, finds disks again under a lock, rejects any path, serial, size, WWN, model or inventory change, and refuses when nwipe is already running. | `nwipe_runner.py: _reserve_target_under_lock`, `_recheck_identity_under_lock`, `pinned_nwipe_already_running`; `safety.py: assert_rediscovered_identity` |

So **"via nwipe" is not an option** under the pin. Any firmware erase would need a
separate tool (`nvme-cli` or `hdparm`). That breaks the "nwipe only" rule and
the "do not bump nwipe" rule would also block any future upstream nwipe
feature.

## 3. User benefit

Audience: owners erasing a computer before resale, recycling or donation, and
small refurbishers erasing many computers. Most modern laptops and desktops have an
internal NVMe SSD. Fewer have a SATA SSD.

| Benefit | Size | Caveat |
|---|---|---|
| Coverage of spare/over-provisioned and remapped flash that a host overwrite cannot address | Real when the firmware implements the command correctly. An NVMe sanitize operation "alters all user data in the sanitization target such that recovery of any previous user data from any cache, the non-volatile storage media, or any Controller Memory Buffer is not possible" (NVMe Base 2.1, Sanitize Operations) | Correctness is the vendor's. Wei et al. (FAST '11) found that of 7 testable disks supporting ATA SECURITY ERASE UNIT, only 4 executed it reliably. One "reported that sanitization was successful, but all the data remained intact." |
| Hidden namespaces and caches | NVMe Sanitize scope is the whole NVM subsystem, including "unallocated or deallocated areas of the media" and caches | The same scope also erases every *other* namespace on that subsystem. That is a safety issue (see §6). |
| Speed for refurbishers | Crypto erase usually finishes in seconds to minutes. A full overwrite plus read-back of a 1 TB SSD takes hours. | Vendor-reported estimates only (Sanitize Status log ETCE/ETBE, ATA IDENTIFY erase-time words). Not measured here. |
| Less flash wear than overwrite | NVMe 2.1 itself warns that multi-pass Overwrite sanitize "may have an adverse effect on media endurance" on NAND | Minor for a one-time erase before resale |
| Honest message improves | Today: "SSD results depend on the drive's controller." With a supported command, we can say that the disk's own erase was requested and that the disk reported success. | That is still a vendor-reported result, not a certificate (§7) |

Who does **not** benefit: disks in USB enclosures, disks behind RAID/VMD, disks that
firmware leaves "frozen", disks whose firmware lacks the command, HDDs (overwrite
is already appropriate), eMMC/UFS (separate command sets, out of scope). We do
not know how often consumer disks are frozen or lack Sanitize (**unverified**;
this is a goal of the Stage 1 measurement). A community list (Purism forum,
"List of NVMe Drives' Format/Sanitize Support") suggests that many consumer
NVMe disks support Format with SES but not Sanitize. That source is not primary and is **unverified**.

Standards context: NIST SP 800-88 Rev. 2 (September 2025, which supersedes Rev. 1)
§3.1.1 says multi-pass overwrite "should be avoided" for SSDs with
over-provisioning because "very little confidentiality protection is achieved".
It says flash with spare cells makes it "infeasible for a user to sanitize all
previous data" by overwrite. §3.1.2 points to IEEE 2883 for purge techniques
"using dedicated, standardized device sanitize commands". It also warns that such
commands "require trust and assurance from the ISM vendor that the commands have
been implemented as expected".

## 4. Options

### A. Do nothing: keep overwrite plus honest limits (status quo)

- No new tool, no new failure modes, no claims change. #158 (the one-line limits
  text above the method cards, owner option B) already makes the limit visible.
- Cost: SSD owners keep a weaker result and a warning. Refurbishers who need
  more use vendor tools outside Beamo, as `docs/storage-and-controller-limits.md` §5 already says.

### B. NVMe Sanitize via `nvme-cli` (Block Erase, Crypto Erase, Overwrite)

Facts (NVMe Base Specification 2.1, section "Sanitize Operations" and the Sanitize
Status log page 81h; `nvme-sanitize(1)`):

- Optional command. Supported actions are advertised in Identify Controller
  SANICAP. SANACT 010b Block Erase, 011b Overwrite, 100b Crypto Erase, 001b Exit Failure Mode.
- Runs **in the background**. Command completion does not mean the sanitize has completed. Progress
  (SPROG) and the result (SSTAT: never sanitized / completed successfully / in progress /
  failed) and the Global Data Erased bit are read from the Sanitize Status log.
  The log also carries per-action time estimates (ETBE, ETCE, ETO).
- "…is not able to be aborted and continues after a Controller Level Reset,
  including across power cycles."
- Scope is the whole NVM subsystem (every namespace). It "does not affect the
  Replay Protected Memory Block, boot partitions, or other media and caches that
  do not contain user data."
- On failure in restricted mode (AUSE=0), commands are aborted with "Sanitize
  Failed" until a later sanitize succeeds. The disk is unusable until then. With
  AUSE=1, Exit Failure Mode returns the disk to use with data possibly partly intact.
- NVMe 2.1 defines an optional Media Verification state (EMVS bit, VERS capability).
  In that state the host can read media after Block or Crypto Erase despite invalid
  ECC, to audit the result. Newer `nvme-cli` also has `--preq` (IEEE 2883 purge
  required, SPRRS). **Debian bookworm ships `nvme-cli 2.4+really2.3-3` (effectively
  2.3), whose `nvme sanitize` has neither `--emvs` nor `--preq`.** Using them
  would need a newer nvme-cli than the base distribution, and disk support for VERS is
  probably rare (**unverified**).
- Default action preference if adopted: Crypto Erase when supported, otherwise
  Block Erase. Never Overwrite sanitize on NAND by default.
- Adds a package (`nvme-cli`, licence believed to be GPL-2.0 family, exact terms
  **unverified**) and a new pinned binary.

### C. NVMe Format NVM with Secure Erase Settings (SES=1 User Data Erase, SES=2 Cryptographic Erase)

- SES=1: "contents of the media allocated for user data after the erase is
  indeterminate", and the controller may do a crypto erase instead. SES=2 deletes the key.
- Scope depends on SENS/FNA. It can be every namespace on the controller.
  `nvme-format(1)` warns that `/dev/nvmeX` numbering does not imply which
  namespaces belong to it: "you may irrevocably erase data on an unintended device."
- **Synchronous** admin command. There is no progress, no status log and no defined
  persistence across power loss (this session found no resume statement for Format in Base 2.1,
  in contrast to Sanitize). Linux `nvme_core.admin_timeout` defaults to 60 s
  (`drivers/nvme/host/core.c`, v6.12). nvme-cli can pass its own timeout. A
  timeout leads to a controller reset mid-format (exact interaction **unverified**).
- A wrong `--lbaf` changes the sector size. Beamo would have to keep the current format.
- NIST SP 800-88 Rev. 1 Table A-8 listed NVMe Format User Data Erase / Crypto
  Erase under Purge, with mandatory verification. Rev. 2 removed technique tables in favour of IEEE 2883.

### D. ATA Sanitize via `hdparm` (`--sanitize-crypto-scramble`, `--sanitize-block-erase`, `--sanitize-status`)

- Present in bookworm's hdparm 9.65 (`--help`, states SD0–SD4 in `hdparm.c`).
  It is **not** in the man page and requires `--yes-i-know-what-i-am-doing`.
- Like NVMe Sanitize it runs in the background and has a status query
  (hdparm prints the sanitize states SD0 Idle, SD1 "Sanitize Frozen", SD2 In
  Process, SD3 Failed and SD4 succeeded). Firmware can set SANITIZE FREEZE LOCK.
  ACS is understood to make an ATA sanitize operation continue across power
  cycles, like NVMe. **That is unverified in this session**: the ACS-3 draft could not be re-read.
- NIST Rev. 1 (Table A-5, ATA hard disk drives) said the ATA Sanitize Device feature set
  commands "are preferred over the … SECURITY ERASE UNIT command when supported". Its Table
  A-8 lists "Apply the ATA sanitize command, if supported" under Purge for ATA SSDs.
- `hdparm` is already in the image. Using it for erase reverses the comment there:
  "Beamo never constructs ATA security-erase arguments."

### E. ATA Security Erase / Enhanced Security Erase via `hdparm`

- Needs `--security-set-pass` first. Kernel ATA wiki: "When the user password is set the drive
  will be locked after next power cycle". After interruption or timeout,
  "the password was still enabled". One user reported disks left "passworded"
  that "I cannot unpassword" after a Lenovo BIOS froze them.
- The kernel ATA wiki also says: "Do not attempt to do this through a USB interface!" It reports a disk
  "bricked" after the command was refused over a USB adapter.
- NIST Rev. 1 Table A-8 put SECURITY ERASE UNIT for SATA SSDs under **Clear**, not
  Purge. For flash it said the Enhanced Secure Erase command "is not recommended without first
  referring the manufacturer". Wei et al. found the failures quoted in §3.
- Recovering a locked disk is password work, which a fixed constraint forbids.
- **Recommendation: never adopt.**

### F. Vendor tools and TCG Opal PSID revert

Out of scope. Vendor tools are closed and model-specific. PSID revert means
reading a label and doing Opal password work. Keep pointing to them from
`docs/storage-and-controller-limits.md` §5 as today.

## 5. Hardware and platform risks

| Risk | What happens | Mitigation if adopted |
|---|---|---|
| **Frozen (ATA Security)** | Many BIOSes send SECURITY FREEZE LOCK at start-up (kernel ATA wiki). Every security command is then refused until power-on reset. | Refuse and explain. Offer overwrite. No workaround. |
| **Suspend/resume or hot-plug "unfreeze"** | The wiki suggests `echo -n mem > /sys/power/state` or re-plugging SATA cables ("this might crash your kernel"). `mem` maps to whatever `mem_sleep` selects (kernel `sleep-states.rst`). On computers with only s2idle (widely reported for recent laptops; **unverified** here) the disk may not be power-cycled. Resume of an unknown live system can fail: black screen or lost USB. | **Do not offer.** It conflicts with the live power policy (suspend masked) and can lose the session, the evidence and the Beamo USB. |
| **Sanitize Frozen (ATA SD1)** | Firmware can lock sanitize until power cycle. | Refuse and explain. |
| **USB bridges (UAS/BOT with SAT)** | ATA commands need ATA PASS-THROUGH in the bridge. Long erases can trip bridge resets. "Locked devices" may be hidden by the bridge (kernel ATA wiki). USB-to-NVMe bridges have no standard NVMe admin pass-through. smartmontools reaches them only through vendor-specific, partly "EXPERIMENTAL" types (`sntjmicron`, `sntasmedia`, `sntrealtek`) for health data. | Never over USB. The bus must be `nvme` over PCIe or AHCI SATA. |
| **Thunderbolt/USB4 NVMe enclosures** | They show up as ordinary `nvme` but can be unplugged mid-sanitize. | Refuse when the sysfs path crosses a Thunderbolt/USB4 tunnel (detection to be built and tested). |
| **Intel VMD / RST, hardware RAID** | VMD remaps PCIe. Linux's `vmd` driver usually exposes the NVMe disks, but sanitize through VMD is untested here. RAID volumes hide members. | Stage 2 refuses VMD-attached and RAID disks (reuse #185 detection). Revisit only with hardware evidence. |
| **Vendor bugs / bad firmware** | Reported success without erase (Wei et al., Drive B). Two more disks' ERASE UNIT "would only erase the first LBA" unless firmware was recently reset (those two did report the failure). Key material retained by wear levelling (CVE-2018-12038, Samsung 840 EVO, CERT VU#395981). That flaw concerned password-based self-encryption, not crypto erase, but it illustrates that crypto erase depends on key handling we cannot see. | Never call the result "verified". Do read-back checks (§7). Keep a deny list of models known to be bad. |
| **Long runs and power loss** | NVMe/ATA Sanitize resumes after power-on. While it runs, I/O is refused, so firmware or Windows may not see the disk, and the owner may think it is broken. Format and ATA Security Erase do not resume. | Require AC power on laptops. On next start Beamo must detect "sanitize in progress or failed" and explain it (new recovery screen). |
| **Bricking** | Kernel ATA wiki: firmware bugs "might render the drive unusable". The ATA password lock above. A failed NVMe sanitize in restricted mode leaves the disk unusable until a later sanitize succeeds. | Exclude ATA Security Erase. Choose restricted vs unrestricted mode deliberately (owner decision). Provide a gated "run the disk's own erase again" path. |
| **Wrong-device scope** | NVMe Sanitize and Format act on the subsystem/controller (`/dev/nvmeX`), not the namespace the owner picked (`/dev/nvmeYnZ`). Numbers need not match (`nvme-format(1)`). | Map namespace → controller → subsystem through sysfs. Require exactly one controller and exactly one namespace, and a serial/WWN match with the confirmed disk. Refuse otherwise. |
| **Concurrency** | nwipe or the kernel may touch the disk during sanitize. | Same global lock as nwipe. One operation at a time. No auto-retry. |

## 6. Safety gates (unchanged gates plus additions)

Every existing gate applies unchanged: the Beamo USB is never listed (and no
targets are listed if boot identity is uncertain); only whole `/dev/...` disks;
owner tick; exact confirmation token; five-second countdown that only *enables*
the separate **Erase now**; rediscovery under lock that rejects any serial, size,
WWN, path, model or inventory change; one operation at a time; logs and evidence
only under `/tmp/beamo-wipe/` (tmpfs), never on the target; no shutdown while an
operation may be running.

Additions for any firmware command:

1. **Eligibility** (read-only, before the method list): bus `nvme` over PCIe (Stage 2) or
   AHCI SATA (Stage 3). Never USB, Thunderbolt/USB4, VMD or RAID. Command supported (SANICAP or
   ATA capability). Not frozen. Not already sanitizing. No failed sanitize state.
   Exactly one controller and one namespace for NVMe. Laptop on AC power.
2. **Separate method**, never the default. The Final check names it in plain words
   ("the disk's own erase command") and says that the disk maker's firmware does the work.
3. **Fixed argv allowlist**, like `validate_argv()`: a pinned binary path, the controller path
   derived from the confirmed namespace, a fixed SANACT, AUSE as decided, never
   `--force`, never `--security-*`, never an ATA password.
4. **Re-check under lock immediately before the command**: identity as today plus
   the controller/subsystem mapping and the capability/frozen state.
5. **No unfreeze or suspend**, no automatic Exit Failure Mode, no automatic retry.
6. **Status polling is read-only** (Sanitize Status log / `--sanitize-status`).
   Shutdown and **Check disks again** stay blocked while it reports "in progress".
7. A `safety:` commit with focused regression tests for each gate, as for any nwipe-argv change.

## 7. Verification limits and how outcomes would be shown

| Command | What can be confirmed from the host | What cannot |
|---|---|---|
| NVMe Sanitize | SSTAT "completed successfully" or "failed", the GDE bit, SPROG history, and that sampled LBAs read back changed (or deallocated) | That spare/remapped flash was erased; that the old key is really gone; vendor correctness |
| NVMe Sanitize + Media Verification (2.1, if supported) | Raw post-erase reads of user media without dealloc masking | Same vendor limits. Needs newer nvme-cli than bookworm. |
| NVMe Format SES=1/2 | Command completion and status code only, plus sampled read-back | Progress, persistence, and anything beyond the visible LBAs |
| ATA Sanitize | SD4 "succeeded" / SD3 "failed" plus sampled read-back | Same as NVMe |
| ATA Security Erase | Command completion, security state afterwards, sampled read-back | Same, plus Enhanced semantics are vendor-defined |

Read-back sampling: NIST Rev. 1 §4.7.3 recommended pseudorandom samples across the
address space. For crypto erase it said the best check is to "read the pseudorandom
locations prior to Cryptographic Erase, and then again following" and compare.
Rev. 2 §4.5.1 relaxes this: "elaborate sampling … is not necessary" unless
policy requires it, and completion status, errors and disk health are checked instead.
If adopted, Beamo should keep only SHA-256 digests of the samples in memory (never
user data on disk) and compare after the erase. A changed sample proves the visible
data changed. It does not prove that hidden data or keys were destroyed. Reads that return zeros after
deallocation are not evidence of erasure.

**Recommended presentation:** a firmware erase alone is never `verified`. If it is
followed by nwipe Everyday, the existing `verified` outcome keeps its current meaning
(nwipe read-back of the final overwrite). The firmware step is recorded as a separate
`checks[]` entry (`pass`/`fail`/`unavailable`) and never rewrites `outcome`.
Draft copy (for owner review, not adopted):

- *Disk's own erase reported success, then Everyday verified.*
  What happened: "The disk's own erase command finished and the disk reported
  success. Then Beamo Wipe overwrote the disk and checked the overwrite."
  What it means for your disk: "Both steps finished. The disk maker's firmware
  decides how its own erase works. Beamo Wipe cannot inspect the disk's hidden
  spare areas. This is not a certificate."
  What to do next: "Save a report if you need one. The disk is ready to reuse or recycle."
- *Not supported, frozen, USB or RAID:* What happened: "The disk's own erase
  command was not sent. Nothing was erased." What it means: "This computer or
  this disk does not allow it here." What to do next: "Choose Everyday to
  overwrite the disk instead, or use the disk maker's tool."
- *Reported failure:* What happened: "The disk reported that its own erase failed."
  What it means: "Some data may remain, and the disk may refuse to work until its erase finishes."
  What to do next: "Leave the disk connected, keep the computer on wall power, and contact support at beamosupport.com."
- *Interrupted by power loss:* What happened: "The disk's own erase was still
  running when the computer lost power." What it means: "Most disks continue it
  when they are next powered on. Until it finishes, the disk may not appear."
  What to do next: "Start from the Beamo USB again and leave the computer on wall power. Beamo Wipe will show the disk's status."

## 8. Claims impact (`docs/claims.md`)

Lines that would have to change (quoted exactly):

- Allowed bullets: "Guided screens on top of nwipe (open source). You pay for the flashed stick and the guide, not a secret algorithm."
  (It would still be true, but it would be incomplete if a second tool erases.)
- Allowed bullets: "HDD overwrite via nwipe. SSD results depend on the drive’s controller. Not a formal erasure certificate."
- Honesty lines: "On SSD and NVMe drives, Beamo Wipe overwrites the storage the drive exposes.
  It does not send the drive's built-in sanitize or secure-erase command."
- Honesty lines: "Overwrite is not a formal certificate. On an SSD the drive's controller decides
  what remains — see `docs/storage-and-controller-limits.md` for wear-leveling,
  hidden areas, encryption, RAID, and when to use the vendor's secure-erase
  tool or physical destruction instead."

The forbidden list stays as it is: no "military certified / DoD certified / NSA / NIST compliant
(as a badge)", no "impossible to recover", no "Blancco replacement". A firmware
erase must not be described as certified, NIST/IEEE 2883 compliant or guaranteed.
Mentioning NIST SP 800-88 or IEEE 2883 at all in listing copy needs an explicit owner decision.

Other docs and surfaces that would change in the same commit: `AGENTS.md` (Project,
Safety boundaries), `docs/storage-and-controller-limits.md` (§2 "No ATA/NVMe
sanitize command is issued", §3 NVMe vs SATA row, §5, §7, §8 "Do not say … sanitize,
… secure erase", the canonical offline limits block and its pinned tests),
`docs/ADVANCED.md`, `docs/compatibility-matrix.md` ("NVMe Secure Erase / ATA
Secure Erase — not implemented"), `README.md`, `NOTICE`, `THIRD_PARTY.md`,
`docs/glossary.md`, `docs/screens.md`, the method copy and locale drafts, and the evidence schema.

## 9. Test matrix

Fakes cover logic only. Flash behaviour, firmware bugs and power loss need physical
disks on a separately authorized lab computer. This development computer is remote-only
and must not touch real disks (`~/dev/AGENTS.md`).

| # | Case | Fake/unit | QEMU | Physical |
|---|---|---|---|---|
| 1 | Capability parsing (SANICAP, ATA words, frozen bits) from recorded identify/log dumps | yes | – | capture dumps |
| 2 | Namespace → controller → subsystem mapping, mismatched numbering, 2+ namespaces, 2 controllers | yes (fake sysfs) | partial (QEMU NVMe can expose namespaces; sanitize support in QEMU **unverified**) | yes |
| 3 | Argv allowlist, never `--force`/`--security-*`, controller path derived from confirmed disk | yes | – | – |
| 4 | Gate order: owner tick, token, countdown, Erase now, lock re-check, identity change refusal | yes | yes | – |
| 5 | Consumer NVMe with Sanitize Crypto Erase (≥3 vendors) | – | – | **yes** |
| 6 | NVMe with Format SES only, no Sanitize | – | – | **yes** |
| 7 | NVMe already in Sanitize-Failed / In-progress state at boot | yes (fake log) | – | **yes** |
| 8 | Power loss at ~1 %, ~50 %, ~95 % of NVMe Sanitize; restart from Beamo USB | – | – | **yes** |
| 9 | SATA SSD with ATA Sanitize, unfrozen | – | – | **yes** (Stage 3) |
| 10 | SATA SSD frozen by firmware (several makers' laptops/desktops) | yes (fake bits) | – | **yes** |
| 11 | USB-SATA (UAS and BOT) and USB-NVMe bridges (JMicron, Realtek, ASMedia) are refused | yes | yes (usb-storage) | **yes** |
| 12 | Thunderbolt/USB4 NVMe enclosure refused | yes (fake sysfs) | – | **yes** |
| 13 | Intel VMD on, RST RAID, hardware RAID HBA refused | yes | – | **yes** |
| 14 | Laptop on battery refused, on AC accepted | yes (fake power_supply) | – | **yes** |
| 15 | Read-back sampling digests before/after; zero-after-dealloc not counted as proof | yes | yes | **yes** |
| 16 | Beamo USB removed during sanitize; session loss; evidence stays in tmpfs | – | partial | **yes** |
| 17 | Firmware erase then Everyday: outcome semantics unchanged; `checks[]` entry | yes | yes | **yes** |
| 18 | Tk 72 DPI, GTK/Orca, curses/plain console and web preview parity, FR/DE/ES/IT drafts | yes | yes | Orca on hardware |

Sizing (**estimate**): at least 10–15 sacrificial disks (NVMe from at least 4 makers,
including DRAM-less models; 3–4 SATA SSDs) and 3–4 computers (two laptops of different
makes, one desktop with VMD/RST options, one with Thunderbolt).

## 10. Effort (rough, unverified estimates)

| Work | Engineer-weeks |
|---|---|
| Stage 1: read-only capability probe and evidence field, no erase | 1.5–2 |
| Stage 2: NVMe Sanitize method with gates, recovery screen, UI parity, locales, docs and claims | 4–6 |
| Hardware lab runs and fixes (needs physical access elsewhere) | 2–3 |
| Stage 3: ATA Sanitize for AHCI SATA SSDs | 2–3 |
| **Total to Stage 3** | **≈ 8–12**, plus hosted CI and native review |

## 11. Recommendation and staged rollout

**Recommended path:** keep Option A for the shipped product now. If the owner
wants to pursue firmware erase, change the rules in stages, each with its own
approval:

- **Stage 0 (now):** no change. #158 limits line ships. This record is attached to #186.
- **Stage 1 (owner approval of a rule change, no erase):** a read-only probe
  (`nvme id-ctrl`, `nvme sanitize-log`, `hdparm -I`) records in evidence and the
  Advanced view whether the selected disk advertises Sanitize/Format crypto erase and whether it is
  frozen. This measures real-world support before committing to Stage 2. It still
  needs the "Beamo does not invoke hdparm or smartctl" text changed and nvme-cli added.
- **Stage 2 (separate approval, plus a hardware lab):** NVMe Sanitize (Crypto Erase,
  else Block Erase), internal PCIe NVMe only, as an *added first step before
  Everyday*, never alone and never the default. Gates as in §6. The existing nwipe Everyday
  pass and its verified outcome follow unchanged, as nwipe's own SSD guide
  recommends. Ship it behind an opt-in label until the lab matrix passes.
- **Stage 3 (separate approval):** ATA Sanitize on AHCI SATA SSDs, unfrozen only.
- **Not recommended:** ATA Security Erase/Enhanced (password lock, Clear-level in
  NIST Rev. 1, documented bricking), the suspend/hot-plug unfreeze, any USB or RAID path,
  and NVMe Format SES as a default (no progress, no persistence). Format could be a
  later, separately reviewed fallback.

## 12. Owner decisions needed

1. Keep the "nwipe only / no ATA/NVMe sanitize" rule (Option A), or authorize Stage 1?
2. If Stage 1: may Beamo run read-only `nvme-cli`/`hdparm` queries and add `nvme-cli` to the image?
3. If Stage 2: which commands (recommended: NVMe Sanitize Crypto/Block only), and is it
   always combined with Everyday or ever offered alone?
4. Restricted (AUSE=0, a failed disk stays unusable until erased again) or
   unrestricted (AUSE=1, the disk can be returned to use after failure) mode?
5. New `docs/claims.md` wording for the four lines in §8, and whether NIST/IEEE may be named at all.
6. Budget and location for the physical lab (this computer is remote-only). Who owns the hardware evidence?
7. Support policy for disks left mid-sanitize or failed, and the warranty statement.
8. Evidence schema: a new `checks[]` kind only (recommended), or a new outcome?

### Owner answers (2026-11-10)

On 2026-11-10 the owner directed: apply the recommended option for each point
and record it. Nothing in `AGENTS.md`, `docs/claims.md`, the product copy or the
code changes. Any later change needs a new, explicit owner decision.

1. **Option A.** Keep the "nwipe only / no ATA/NVMe sanitize" rule. Stage 1 is
   not authorized.
2. **Not authorized.** No `nvme-cli` or `hdparm` queries, and no new packages in
   the image. (Only relevant if Stage 1 is approved later.)
3. **Recorded default for any future Stage 2:** NVMe Sanitize Crypto Erase, else
   Block Erase, on internal PCIe NVMe only. Always an added first step before
   Everyday, never alone and never the default. Not built now.
4. **Deferred.** There is no recommendation in this record, and the question only
   matters for Stage 2. A future Stage 2 proposal must bring a recommendation.
5. **No change.** `docs/claims.md` keeps its four lines in §8 as they are. Listing
   copy does not name NIST SP 800-88 or IEEE 2883.
6. **No lab now.** No budget or location is assigned. Hardware evidence for the
   current product stays with the physical acceptance packet (#116).
7. **Not applicable.** No firmware erase ships, so the current support policy
   and warranty text stay as they are.
8. **Recorded default for the future:** a new `checks[]` kind only, not a new
   outcome.

## 13. Sources

Retrieved 2026-11-07. SHA-256 is given where the file was downloaded.

- nwipe v0.42 release: <https://github.com/martijnvanbrummelen/nwipe/releases/tag/v0.42>.
  Pinned commit files: `README.md` `06d89dd903af726974432e89e9ec4e2b901a378b5bbb32cf21f2fc1b73209581`,
  `ssd-guide.md` `df3477a7d4d70ae9196c506f3177ad93dbfbd3503aaec7e5b27a12c3e123ec0d`,
  `man/nwipe.8` `484f9585a509359e9ce36c038ff5995e3ddc39a00c0e209054bb946e18cb9c32`,
  `src/hpa_dco.c` `47858c2917708ee8e51fcbba9bb13a3c68c9eb9bd1876b1daf45f497fac1a240`,
  `CHANGELOG.md` `be9ad6bb04980a6a48371d2caf25c767b70c4abea2a0eca8159a1cecdb92fb2c`.
- ShredOS discussion #156, "Erasing SSD's and NVME's": <https://github.com/PartialVolume/shredos.x86_64/discussions/156> (secondary).
- NVM Express Base Specification, Revision 2.1 (2024-08-05), "Sanitize Operations",
  Sanitize Status log page, Format NVM SES:
  <https://nvmexpress.org/wp-content/uploads/NVM-Express-Base-Specification-Revision-2.1-2024.08.05-Ratified.pdf>
  (`4e31f826dd7ceaee311f93b74eef5c05ac32afe4ef45436534dfcfd6a40dc746`). The NVM Command Set
  specification was not read.
- nvme-cli documentation: `nvme-sanitize(1)`, `nvme-format(1)`, `nvme-sanitize-log(1)`, master
  `f7919e51771e31240b9201345054d3d32f105b3e`, and tag v2.3:
  <https://github.com/linux-nvme/nvme-cli/tree/master/Documentation>.
  Debian versions from <https://sources.debian.org/src/nvme-cli/> (bookworm `2.4+really2.3-3`).
- hdparm 9.65 (bookworm) man page (`a762c920…204a066a`) and `hdparm.c`
  (`8286da1a820a2e910214bab06b10af2d2a6dc49eaaafbca9904435b5b64c2d53`):
  <https://sources.debian.org/src/hdparm/9.65+ds-1/>.
- Linux kernel ATA wiki, "ATA Secure Erase" (last modified 22 July 2013):
  <https://archive.kernel.org/oldwiki/ata.wiki.kernel.org/index.php/ATA_Secure_Erase.html>
  (`cb32761d4cb828f6cba5a3d81e270ae643530261be6ceddc60cf6dd837682d1a`).
- Linux v6.12 `Documentation/admin-guide/pm/sleep-states.rst`
  (`c910a8056f69b248595fb25f2bf35676ca8a038fcde3c9006569267f015ea781`) and
  `drivers/nvme/host/core.c` (`admin_timeout = 60`).
- smartmontools 7.3 `smartctl.8.in` (`47603bff…bec599b`), USB-NVMe bridge device types.
- NIST SP 800-88 Rev. 2 (September 2025): <https://doi.org/10.6028/NIST.SP.800-88r2>,
  §3.1.1, §3.1.2, §3.2, §4.5.1, Appendix B, Appendix D
  (`39bb805c72723ed74f08e5806cd8463ca2554a62abb4f97b9d19c0398a8a7c55`).
- NIST SP 800-88 Rev. 1 (December 2014, superseded): <https://doi.org/10.6028/NIST.SP.800-88r1>,
  §4.7.3, Tables A-5 and A-8 (`acd2315cb1823d51db93b180d898fabfdf5e964e3fcb41cf44d14b4c3ec8c5c4`).
- IEEE 2883-2022, Standard for Sanitizing Storage: <https://standards.ieee.org/ieee/2883/10277/>.
  **Not read** (paywalled). Cited only through NIST Rev. 2 and NVMe 2.1.
- ATA/ATAPI Command Set ACS-3 draft d2161r5 (linked from nwipe's SSD guide). **Not re-read**
  because the download failed (host disk full). Claims are attributed to NIST Rev. 1 and hdparm.
- M. Wei, L. Grupp, F. Spada, S. Swanson, "Reliably Erasing Data From Flash-Based
  Solid State Drives", USENIX FAST '11:
  <https://www.usenix.org/legacy/events/fast11/tech/full_papers/Wei.pdf>
  (`0ca20b3c9a9bc22477743f5a7ee0471758bcde3a050becc84f99a5e77ddee5f6`).
- CERT/CC VU#395981 (CVE-2018-12037, CVE-2018-12038; Meijer and van Gastel, "Self-encrypting
  deception"): <https://kb.cert.org/vuls/id/395981/>.
- Community list (secondary, unverified): <https://forums.puri.sm/t/list-of-nvme-drives-format-sanitize-support/23519>.

## 14. Not verified

- No physical disk, computer, enclosure or firmware was touched. Every hardware
  statement comes from specifications, tool sources or literature.
- How often consumer disks are frozen or lack Sanitize; how often VMD passes Sanitize;
  QEMU's NVMe Sanitize support; nvme-cli licence; exact Format timeout behaviour.
- Effort, disk counts and time figures are estimates.
- IEEE 2883, the ACS drafts, the NVM Command Set spec and TCG Opal were not read.
