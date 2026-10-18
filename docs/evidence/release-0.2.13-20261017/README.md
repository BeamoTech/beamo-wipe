# Beamo Wipe 0.2.13 candidate preparation

2026-10-17 / Codex. The owner authorized committing all audit work, merging it
into protected main, and publishing the next qualified release. This record
captures local candidate preparation before any push or hosted qualification.
It does not claim publication or physical-hardware acceptance.

Repository: BeamoTech/beamo-wipe. Branch: fix/safety-audit-20261015. Starting
HEAD:35107a8d1a701093eac876a58ab4efd50e291673, twelve commits ahead of main
cad8ed397818bca09634be57cd8a46e0195690c2. All existing uncommitted audit work
was inventoried and preserved. The new patch version is0.2.13; nwipe0.42,
Go1.26.8, the designated rollback identity and approved claims are unchanged.

Final local candidate2 authenticates875 source inputs, excluding mutable memory
and evidence directories. Runtime SHA-256:
781dc5f3dab8c8a07f799b17fd25583fe19c47267d22bcfbebfc2156520e8ea9.
Source-freeze SHA-256:
f6b944b3e7f4d8c286cbfae80ececbd6cdec9bef10ca546acfd6ae241c9bf605.
Compared with the last audited runtime, only the application version changed.
Build/helper/release defaults, current documentation and version expectations
were aligned with that version. All59 retained audit regression modules remain
unchanged.

| Local verification | Result |
| --- | --- |
| Initial version-focused checks | 40 passed |
| Original version-fixture reproduction | 43 cases:23 failures,20 controls |
| Corrected and adjacent version/report checks | 125 passed; every original failed ID executed and passed |
| Final nine fresh local phases | Lint/types, preview, negative boot guard, pinned Go version/race/vet/350000 fuzz/Windows crossbuild, full Python/Orca all passed |
| Final main suite | 10126 passed,14 artifact-dependent skips, zero failures/errors in1160.83s |
| Separate clean Orca | 1 passed in59.91s |
| Combined JUnit readback | 10127 passed,14 exact prior artifact skip IDs; no failures/errors/duplicates |
| Retained audit regressions | All59 modules/3924 cases ran and passed |
| Native child readback | 64 zero exits, empty stderr, no parent timeouts or reported unraisables;36 direct source hashes,28 inherit the admitted canonical environment |
| Content review | Original2698 changed files/104 archives/15631 members scanned; zero matching secret patterns or media members |
| Historical preservation | All2617 original evidence files unchanged; all1106 entries in the five existing SHA256SUMS manifests authenticate |

Candidate1 is retained as a failed run:10103 main passes,23 failures,14 skips,
plus one separate Orca pass. The failure traces prove nine shell-fixture version
mismatches, one old finalizer filename and thirteen report golden mismatches.
The shell fixtures now explicitly select their existing fake0.2.12 version;
the finalizer fixture uses the current application version. All37 original
Python assertion predicates in those four modules are unchanged. Thirteen
report goldens change only the application-version line and the sharing
checksum derived from it. Replacing the new version in the generated fake
SHARE.json recovers the exact original checksum. No production guard, report
outcome wording, privacy assertion or timing bound was weakened.

The two local gate runs use the same runtime bytes. Their source snapshots
remain separate because the test data changed. The identical Windows test
executable is indexed to the existing pass21 raw archive when its full hash
matches; each current compile's execution and freshness remain separately
recorded. A crossbuild is not native Windows acceptance.

Evidence-helper failures remain explicit: the first content scanner rejected
an original111553533-byte Font trace at its64MiB in-memory bound; the corrected
scanner streams that ordinary member instead of omitting it. A preservation
helper initially assumed every14 audit directories had a top-level SHA256SUMS;
only five use that format. Their1106 entries authenticate, while all2617
original evidence files independently match the starting inventory. No absent
legacy manifest is labeled as a passing manifest.

The14 skips are two live-build-generated config checks and twelve
manufacturing-ISO-dependent checks. Their exact IDs/reasons are in
candidate2/gate-verification.json. They remain skips. Current local execution is
Python3.12.3/private72DPI/fake devices. Required Blacksmith Python3.11/live-image,
QEMU and native Windows qualification is pending this snapshot's subsequent
protected PR/main workflow. Publication also requires the exact main tag,
production release workflow, verified transfer and signed publisher readback.
Historical incident attribution and physical/firmware acceptance remain
unproved; current passing checks do not fill those gaps.

The post-publish verifier is prepared in preparation/ but has not run here.
It authenticates metadata before downloading and verifying actual public ISO,
compressed USB and extracted regular-file bytes. It never writes physical
media. Its eventual result, the GitHub workflow runs and signed public release
manifest establish deployment; this candidate-preparation record does not.
