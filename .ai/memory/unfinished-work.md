# Unfinished work

## BW-RELEASE-20261017-ALL — IN PROGRESS / FINAL LOCAL QUALIFIED, PUSH PENDING

- Date/author:2026-10-17–18 / Codex; checkpoint01:12UTC. BeamoTech/beamo-wipe,
  worktree `/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`.
- User explicitly authorized committing/pushing all work to protected main and
  publishing the latest complete release. Merge and publication are authorized
  after verification; do not ask the same permission again. Preserve required
  CI/statuses, branch protection and protected publisher. Physical host/device,
  firmware/security/remote-access restrictions remain; no physical work authorized.
- BW-REL-SOURCE — COMMITTED/PUSHED:4f7ee8d434497f52b58966792ed6cc28b587635e,
  safety: ship audited disk and UI reliability fixes in0.2.13. All2849 reviewed
  paths committed; all commit blobs independently match reviewed raw bytes;
  index/worktree were clean after commit. Remote feature branch verifiedpushed.
  Includes all pre-existing audit work, version alignment, regression/evidence
  and raw-archive Git policy. Nwipe0.42,Go1.26.8,claims and rollback unchanged.
- BW-REL-LOCAL — PASS with explicit provenance: corrected candidate2 fresh9
  local phases pass. Main10126PASS14artifactskips in1160.83s; Orca1PASS59.91s.
  Combined10127PASS0fail/error/duplicates; all59 auditmodules3924cases pass.
  All64native children zeroexit/emptystderr/noTimeout/unraisables,36directhashes.
  RuntimeSHA781dc5f3dab8c8a07f799b17fd25583fe19c47267d22bcfbebfc2156520e8ea9.
  Candidate2 source875 freezeSHAf6b944b3e7f4d8c286cbfae80ececbd6cdec9bef10ca546acfd6ae241c9bf605.
  After the full gate, one regression EOF blank line was removed: AST and
  marshaled compiled code identical,208focusedPASS. No runtime/assertion/case/
  timing changes. Final875 source map is under release-staging evidence;
  exact committed final bytes must receive hosted CI before merge/release.
- Failed history preserved: candidate1 main10103PASS23FAIL14skips/Orca1PASS.
  All23 are old version-dependent fixtures/goldens. Originalfocused43 gives
  23FAIL20controls; fixedexpanded125PASS includes every original failedID.
  Shell fixtures explicitly select fake0.2.12; finalizer path follows version;
  13goldens change only version plus derived sharechecksum. All37 original
  Python assertion predicates in4fixture modules unchanged. No guard weakened.
  Initial scan/helper count/archival-whitespace failures and corrections are
  preserved. All2617 original evidence files unchanged; five existing manifests
  authenticate1106 entries; nine older audit dirs retain their legacy formats.
- Evidence: docs/evidence/release-0.2.13-20261017/ (99retainedfiles,
  manifest991841fac716dee69b2c724f545a648425d28fefaf7750e4ce1b8222f180b9cb),
  docs/evidence/release-staging-0.2.13-20261017/, and all prior audit directories.
  Content scans cover initial2698files/104archives/15631members plus final deltas;
  zero matching secret patterns or disk-image members. Commit data166MB approx.
- BW-REL-PR — OLD CANDIDATE FAILED / CORRECTED CANDIDATE LOCAL: https://github.com/BeamoTech/beamo-wipe/pull/90,
  head4f7ee8d434497f52b58966792ed6cc28b587635e, base main. Registered with T3.
  Hosted run39079362211 failed source tests; original source not qualified:
  https://github.com/BeamoTech/beamo-wipe/actions/runs/39079362211.
  Exact run/PR state saved in working PRJSON.
  Required strict CI gate applies to admins; no separate non-author approval
  required. Use T3 watch_pull_request and end the turn while CI runs; do not
  poll or run a PR watcher. On wake inspect actual required checks, all comments,
  current head/base and readiness. Fix real failures without weakening checks.
  Once qualified, merge normally with --match-head-commit; no --admin/force.
- BW-REL-CODEQL — REVIEWED/PASS: T3 wake reported four high findings on
  archived review-artifacts.py support-copy assertions: alert32/pass13,
  alert35/pass14, alert34/pass15 (line29), alert33/pass16 (line33). Individually
  traced every operand to generated REPORT.html, not a URL. All four scripts
  match committed bytes; all280 archived bundle files authenticate;16 failure
  reports parse with visible plain support text and zero URL attributes. No
  URL validation, request, redirect or authorization sink. Product report
  escapes copy/metadata; QR accepts only exact constant support URL. Dismissed
  these four false positives with recorded rationale, preserving all archives
  and CodeQL rules/configuration. GitHub confirmed all dismissals23:38UTC;
  subsequent PR snapshot CodeQLSUCCESS. Initial long-comment dismissal request
  exited1 (stderr not retained); concise request accepted. No source fix/retry
  of hosted CI was needed. Focused23 tests at72DPI allPASS; initial no-display
  attempt22PASS/1TkSKIP is retained separately, not called full acceptance.
  Raw API/trace/JUnit receipts in /tmp/beamo-release-20261017/codeql-review/.
  PR snapshot still head4f7ee8d, mergeable butBLOCKED: Linux image gate and
  Greptile review running; Windows launcher and all4CodeQL languagesPASS.
- BW-REL-MAIN-CI — PENDING: after merge record actual merge/mainSHA; wait for
  successful ci.yml eventpush for that exactSHA (Linux/ISO/QEMU plus native
  Windows). PR qualification does not replace this. Do not duplicate existing
  equivalent hosted runs. Main starts cad8ed397818bca09634be57cd8a46e0195690c2.
- BW-REL-TK-REVIEW — FIXED LOCALLY / REQUALIFICATION PENDING: Greptile summary
  issuecomment6243204273 and discussion4304997909 identify one genuine P1 race
  in both retired native pools. Worker snapshots retain the record tuple,
  so the creator's resource-only refcount check can remove its entry; the last
  tuple then releases the native resource on the worker. Deterministic original
  regression proves8FAIL/2normal controls, including both pools, direct/GC
  callback drains, and worker with/without its own resources. Initial testv1
  paused the empty asset pool before reaching interpreter records:4FAIL/6PASS;
  preserved and corrected to select the affected pool before product edits.
  Fix partitions records by creating Thread before any snapshot, retains empty
  metadata buckets for reentrant pin safety, and preserves existing refcount,
  finalizer and explicit-owner rules. No disk/auth/nwipe changes. New regression
  tests/test_tk_retired_pool_threads.py includes an isolated real-native child
  with actual worker GC and original Font/Variable/Image destructors. Focused
  fake/private72DPI checks75PASS, all65 native children zeroexit/empty stderr/
  noTimeout/unraisables;10 deterministic fixedPASS. Full local gate and exact new hosted SHA remain
  required before merge. Prior4f7ee8d CI cannot qualify changed runtime. Evidence
  /tmp/beamo-release-20261017/tk-pool-review/. Next: fresh full local gate, retain
  proofs, commit explicit fix/test/evidence paths, push existing PR90, watch new
  hosted verification/review, then resume already-authorized merge/release.
  First fresh9-phase runner session16706 completed all0exits: main10137PASS,
  14skips/1182.67s; separateOrca1PASS59.96s. NOT QUALIFIED: one material
  PytestUnraisableExceptionWarning from GC on an unregistered/retiring thread
  calling current_thread -> DummyThread while audio fixture replaces
  Thread.__init__. Exact warning/trace retained; no publication or push.
  Freeze876inputs SHAe123a59f19dcb0027685e54087f5022e485cda79a6a86a948e7f338546dc5fcc;
  runtime dbd1ae3746527a5c2a555528433b82d075449068ebb2c56477eb89b07bd15e7e;
  Tk fefdc9963a92c7150d794392c337bf660134d683090d083a4c5d2d945575d43b.
  That candidate/source remains archived under tk-pool-review/local-gates/;
  partition-v1 source/test snapshots and unqualified-warning.json preserve it.
  Two new deterministic raw-thread regressions fail with the same KeyError
  before the next edit. Corrected code tags actual Tk owners in thread-local
  metadata during pinning; GC drains read that tag, avoiding current_thread
  and DummyThread construction for unrelated/unregistered callers. Actual
  Thread identity still selects the isolated bucket, avoiding reused IDs.
  Corrected focused/native/audio87PASS with unraisables treated as errors;
  all65 native child results clean. New full9-phase runner session53265:
  first8 phasesPASS, Python/Orca started00:08:34UTC. New876freeze
  fd1496381d10cd93169f56b276260d8aa5cbe7badf3976f18f4e7d2a8e3891a5;
  runtime d8f527df821941d73332ae365b98f45ac289848bd9e535838e006c958e14e08a;
  Tk f43af23bfb37ca184a3a85c316c5f6235c528a102fd4a98493f9df9452db740b.
  Working logs under tk-pool-review/local-gates-v2/;13new module cases now
  included in60auditmodules3937cases. First-run artifacts untouched; second
  verifier rejects unraisable warnings and warning summaries. Indexempty;
  Corrected full gate now PASS: main10139PASS14existing artifactskips1177.27s,
  separateOrca1PASS59.42s; combined10140PASS0fail/error/duplicates/warnings.
  All60auditmodules3937casesPASS; native65children0exit/emptystderr/noTimeout,
  37directsourcehashes. Source876freeze/runtime above unchanged. Native-output
  reviewer initially classified all13 mixed module cases as children; preserved
  failed helper, selected exactly its one native subprocess case, retained all
  65 native predicates/counts. Full audit classifier independently requires all
  13 module cases. Clean corrected readbackPASS. Final regression bytes replay
  archived original sources:8ownershipFAIL/2controls and2callbackFAIL, stderr0.
  Sealed111 evidencefiles11936862B under docs/evidence/release-tk-pool-review-20261017/;
  manifest a7e5be59dadce315ca9afa0c5baa92e592e925e3173c3fb88c070ca26f7977bd.
  Content scan111inputs/2archives/1752members26255212B:0secretpatterns/media.
  P1 fix still local, no commit/push/release since4f7ee8d.
  Retention helper must use the clean second-run receipts and preserve the
  first run as unqualified. Next exact action remains qualify, commit/push
  existing PR90, then new hosted checks and already-authorized merge/release.
- BW-REL-HOSTED-FAILURES — INVESTIGATING / RELEASE HELD: final pre-push
  inspection finds original4f7ee8d run39079362211 failed Linux source tests;
  Windows/Greptile/CodeQL passed, CI gate failed; ISO/QEMU not qualified. Ten
  failures: one GTK first fresh Return after sound close (test_accessible_focus_input_pass11.py)
  and nine Tk callback-lifetime failures (eight early/start/loop variants in
  test_startup_callback_retirement_pass17.py plus peer-preserving teardown in
  test_confirm_focus_callback_lifetime_pass16.py). Tk traces show pending
  ttk::ThemeChanged after root.destroy: event command/application destroyed.
  GTK second-open predicate did not settle within unchanged2s. Negative mutant
  failure earlier in log is EXPECTED, not an extra failing source check.
  Raw ci-initial-failed.log and ci-failure-comment.json in workingbase. Current
  new local Ubuntu runtime passes, so reproduce exact hosted Debian Bookworm
  Tcl/GTK in an unprivileged container before any further edit/push. No physical
  devices, Docker socket, privileged flags, ISO/QEMU or host network passthrough.
  Managed local Docker socket healthy; approved Debian digest6ebd97fa...1443
  pull session66597/log bookworm-pull.log. Use source read-only and owned temp
  output mounts, proxy/CA guidance. Root cloud skill/network/docker refs read;
  environment_status tool and network-policy file absent. Do not claim policy
  readiness or bypass denials. Next: finish local Debian setup/reproduce/fix
  proven callback/input issues, focused regressions, fresh full relevant gates,
  retain new independent evidence, then commit/push current PR90 and qualify.
  Matching Bookworm container now owned/running: beamo-pr90-bookworm-20261018,
  ID/mounts/labels in bookworm-runtime/container-identity.json. Image digest
  matches CI; Python3.11.2, Tk8.6.13-2/Tcl8.6.13+dfsg-2,
  GTK3.24.38-2~deb12u3/GI3.42.2-3+b1 exactly match failed hosted install logs.
  Read-only source, owned evidence RW/public CA RO; no devices/socket/privilege/
  host networking. Setup exec session99440 runs sleep infinity until owned
  teardown; stop/remove only this label+ID after tests. Do not leave it behind.
  Reproduction56 gives9TkFAIL/47controls. Explicit new native-timer regression
  gives4FAIL before source edit on Ubuntu as well. Timer-only cancellation
  fixes those4 on Ubuntu but Bookworm still13FAIL: ttk schedules a C-level
  idle notification absent from `after info`. That attempt/source are retained.
  Current fix cancels interpreter timers and guards only obsolete ThemeChanged
  notifications when root no longer exists, retaining the original procedure
  body/live behavior and ordinary Tcl error propagation. No global bgerror
  suppression, peer work or Tk destructors changed. Applied to owned-root init
  failure, wizard teardown and all startup close paths. Five-case regression
  includes destroy failure/retry, real live theme dispatch and deliberate Tcl
  errors. Its first control had Tcl string/int comparison TypeError; snapshot
  preserved, int conversion corrected, no product change for that fixture.
  Current focused62 BookwormPASS,20 UbuntuPASS; original9 all pass. New test
  tests/test_tk_interpreter_callback_retirement.py; source tk_wizard.py only.
  GTK investigation: first requested40 identical node IDs ran only1 due pytest
  de-duplication; corrected diagnostic80 iterations allPASS. Separate real
  native256 press/release probe proves215 false repeat classifications from
  zero-delay XTest reusing previous release timestamp while heldFalse. Native
  fixture now requests1ms server delay for fresh presses and has a256-event
  regression; source GTK repeat guard, exact same-time unit tests, assertions
  in all14 old test cases and original2s bound remain. Old CI had no event timestamps:
  exact original GTK failure attribution remains an inference, not a claimed
  trace. Proven fixture defect corrected; current Bookworm original case and
  strict fresh/repeat controls pass. No production GTK input code changed.
  Matching Debian native lifetime run77PASS/65childresults0exit/emptystderr/
  noTimeout, direct source hashes match final028e13... source. Positively
  identified container stopped/removed after every test exec completed; receipt
  bookworm-runtime/owned-cleanup.json. Setup-only sleep session99440 ended137
  by intentional owned Docker stop; NO test process was terminated. Do not
  attribute it to any earlier unexplained signal. Native readback is retained.
  Final877-input9-phase local runner session72338: first8 phasesPASS; full
  Python/Orca started00:50:52UTC. Sourcefreeze6582e76ea795a1e7f4f322c5f7844f82870fd3446e1bb1915e7377119ec5d93b;
  runtime9e2d6373ea8e6d1e8a41d0ecf59b99f0f007681b3278ccecb483234d2f23532b;
  Tk028e13c7d64c230aaaabfbd806ae900c41c64acd8e07334d3d38abd8af6c901f.
  Logs/helpers hosted-ui-repair/local-gates/.61auditmodules3943cases expected,
  native65 child classification preserved. Current tests15GTK/5newTcl plus
  newP1 thirteen all retained. All16 original assertion predicates in5GTK
  functions/14parameterized cases unchanged; exact2s timeout unchanged. Prior
  P1 sealed evidence is immutable and qualifies its
  d8f527... snapshot only, not these later callback/fixture edits. Root-owned
  logs/scripts in hosted-ui-repair/ and bookworm-runtime/. Final overall source
  has not been committed/pushed; current HEAD/PR head still4f7ee8d.
- BW-REL-FINAL-LOCAL — PASS / COMMIT-PUSH NEXT: final877 source inputs remain
  exactly frozen through all9 fresh phases. Main10145PASS14artifactskips1173.36s;
  separateOrca1PASS66.68s; combined10146PASS0fail/error/duplicate/warnings.
  All61auditmodules3943casesPASS. All65canonical native children0exit/empty
  stderr/noTimeout/unraisables,37directsourcehashes. One owned offline SDK
  fixture call,0forbidden fallbacks. Windows crossbuild9021440B unchanged
  d05ac4db...76d9, independently rerun; not native Windows acceptance.
  Finalsource/runtime/Tk hashes are6582e76e...93b/9e2d6373...32b/028e13c7...01f
  as above. Independent diff review: only production tk_wizard.py changes;
  within TkWizard only_teardown changes. GTK input/core safety files matchHEAD.
  Sealed docs/evidence/release-hosted-ui-repair-20261018/:107files10286305B,
  manifest802f4cb03539453faf90df7bfa3db10263780a1ab3df3f54ea211a75dbc13254.
  Content scan108inputs/1archive877members17781392B:0secretpatterns/media.
  Both new evidence directories independently read back:218files authenticate,
  both source archives876/877inputs authenticate; final877current bytes match.
  Failed hosted source receipts/JUnit retained, including exact15skipIDs; its
  additional skip is test_ci_hosted::test_cloud_upload_excludes_local_captures_and_env_files
  because gcloud is unavailable in that legacy test. No current ISO/QEMU pass
  claimed. Upstream Tk8.6.13 source independently confirms C idle notification.
  Next: stage only explicit own src/tests/two evidence dirs/this record,
  verify raw staged bytes and content, commit/push existing branch/PR90; update
  PR description and resolve addressed review, then T3 watch exact new checks.
  Main merge, exact-main pushCI, tagv0.2.13, protected release.yml and actual
  public signed byte verification remain authorized/pending. Never reuse old
  failed4f7ee8d/a77fbd94 CI or stale local runtime evidence for final source.
- BW-REL-PUBLISH — PENDING/AUTHORIZED: once exact main pushCI passes, create
  new annotated v0.2.13 tag at that main commit (never replace an existing tag),
  push tag, dispatch release.yml on main with version0.2.13 exactly once.
  Existing production env allows protected branches, no reviewer rule; existing
  OIDC publisher last succeeded forv0.2.12. Never invoke legacy GCP CI or request
  login. Release verifies/rebuilds7Linuxgates in credential-free worker, transfers
  measured bytes then protected publisher signs/uploads/verifies and promotes.
  Preserve all statuses and production controls; no bypass on a failure.
- BW-REL-PUBLIC-VERIFY — PENDING: verify actual publishedv0.2.13 metadata,
  signed inventory/manifest, expected mainSHA/build, all16server asset digests,
  actual downloaded ISO/compressedUSB and extracted regular-file image, strict
  manifest evidence/package checks, and latest-release designation. No media
  writes. Prepared verifier is retained in release evidence/preparation/
  post-publish-verification.py, working /tmp/beamo-release-20261017/. It takes
  exact mainSHA as sole argument and uses approved fingerprint93caaf7c...66f7,
  floor0.2.13, currenttrusted registry. Inspect/copy as needed; it is NOT RUN.
- Working artifacts/helper/status/commit proof and PR JSONs remain in
  /tmp/beamo-release-20261017/. This new operational checkpoint is local after
  the candidate commit; it is not a new runtime change or publication proof.
  Keep recording source/build/run/asset identity and remaining items before
  handoff. Physical/firmware acceptance and historical incident attribution
  stay explicitly unproved; release qualification is software/isolated-worker.
- Next exact action: retain T3 watch PR90; on required-check success recheck readiness,
  merge, qualify exact main, tag/publish and perform public-byte verification.


## BW-BUG-AUDIT-20261017-PASS21 — LOCAL VERIFIED / QUALIFICATION BLOCKED

- Date/author: 2026-10-17 / Codex, started 20:50 UTC; final checkpoint21:33UTC.
  Repo BeamoTech/beamo-wipe;
  branch fix/safety-audit-20261015, HEAD35107a8d1a701093eac876a58ab4efd50e291673,
  worktree `/root/dev/Beamo Wipe`. Starting779 inputs authenticate exactly to
  pass20 final; runtime c3a9b4c2145e86203eb7669e5073b0fb7de0a932eb2920b5b881c58fba6af2aa.
  Prior dirty work preserved; index empty. Local source only.
- Requested: another comprehensive audit; prove suspected bugs before minimal
  fixes, focused regressions, all applicable local gates and final evidence
  review. Three bounded source-only reviewers cover discovery/safety,
  runner/reports/boot and UI lifetimes. Root owns serialized fake-only runtime.
- BW-P21-AUDIT — LOCAL VERIFIED: baseline, independent source reviews, proved
  fixes and all applicable fresh fake-device checks pass on frozen source.
  Overall qualification remains blocked as below; no commit/push/release.
- Proven/fixed locally (first focused pass): missing/lexically noncanonical disk
  NAME losing flat partition evidence; direct nonfinite float overflow taxonomy;
  Unicode Zl/Zp diagnostic event loss; Tk Variable foreign/default interpreter;
  refresh Event construction/set interruption claims; GTK cleanup after audio
  failure; post-registration owned trace token adoption with peer preservation.
  Four runtime files changed: discover.py,diagnostics.py,Tk/GTK controllers.
  Original traces retain16 NAME,24 alias,9 directfloat,20diag,5variable,6refresh,
  2GTKclose,3trace failures. First trace-v1 rowfixture used invalidBooleanvalue:
  preserved INVALID controls; correctedv2 gives3FAIL1control. Strictfinalizer
  observer v2/v3 replaces v1 finally-return flag; originalversions retained.
  Independent source-only reviews complete; synchronized actual-thread refresh
  proof and rejected-start retry pass on frozen source.
- Final source frozen:788 inputs,775 starting inputs unchanged,4 runtime files
  changed and9 new canonical modules/219 cases. RuntimeSHA 8e18e259414408eff434768ad24b38432bf913b12a864439f40b585a264496c1;
  freezeSHA c4ecdfc8e8c814bd3d033bd478472cbd498a766c76e077006ba2bfb093093dac.
  Exactfinal219 replay on58 authenticated original source inputs:89FAIL and
  130controls,0errors/skips. Earlier213 canonicalPASS; corrected finalfocused
  290PASS includes6 actualThread interleavings/retry and oldnative/refresh cases.
  First finalfocused attempt exit4 selected nonexistent test_async_refresh.py:
  NOT RUN, preserved; corrected actual selection above. No source changed.
  Source/archive/diff readback PASS; independent13-input final review and788
  current/archive plus779 starting input authentication PASS. Five UI modules
  preserve68 non-admission assertions; copied discovery/runner modules preserve95.
- BW-P21-GATES — LOCAL PASS: final fresh9 local phases PASS. Main10126PASS
  14artifactskips in1147.50s; separateOrca1PASS58.60s. Combined10127PASS,
  0fail/error/duplicates; exact14priorartifactskipIDs authenticated. All59 audit
  modules3924cases executed/passed. Same788source/emptyindex; noobserver.
  All64 canonicalnativechildren0exit,empty stderr,noTimeout/unraisables;
  36emitdirectsource/hash and28inherit admitted canonical environment.
  Fresh final10sessions220originalfinalizers allcreator/returned, pools empty,
  oneGCcallback/maxdepth1;12×128Fonts pressure released/noerrors. All306logs,
  90sidecarroundtrips,54advisories,144cancel/retrypaths,621fixtures,270Tk/GTKviews,
  27criticalTkfocus and90reports/fivebundles70files authenticated. Rootviewed5PNGs;
  fresh9 actualGTKTab cases revealownercheckbox in3steps, gatesunchanged.
  Pass20 remains provenance, not pass21 runtime acceptance.
- BW-P21-RETENTION — DONE: independent final evidence review PASS; root then
  re-read all1463 review hashes and sealed167 retained files/17rawstreams.
  Independent post-seal readback authenticates exactmanifestmembership, all788
  current/finalarchived and779startingarchived inputs,171workingstage entries,
  58duplicate source files archive-resolved,621fixtures/70reports/5captures.
  Existingcheckpoint preserved;0overwrites, indexempty, gitdiffcheck PASS.
  ManifestSHA 0f9917ef86d24baacdded465c6bf9e87d0f021a72d85acab9106fd28af1baf64.
  Evidence docs/evidence/bug-audit-20261017-pass21/; sealed primary/receipts and
  SHA256SUMS retained. Rootpostseal receipt [pass21 retention readback](pass21-retention-readback.json).
  Working /tmp/pass21-primary remains; no local verification remains pending.
- BW-P21-HISTORICAL — BLOCKED: pass19's two uncanceled native aborts remain
  unattributed. Current fixed ownership/full-gate results do not identify the
  original creator/cause. Pass18 GTK latency, pass16 loop incident, pass8 SIGTERM
  attribution and pass9 original timing limits remain as recorded in pass20
  and their immutable audit evidence. Remaining acceptance: evidenced incident
  reconciliation. Next action inspect the original retained traces and obtain
  missing platform incident records; current passing tests are not attribution.
- BW-P21-PLATFORMS — NOT RUN/BLOCKED: Python3.11/live-bookworm, ISO/QEMU,
  native Windows, firmware, physical reconnect/readback and hardware. Actual
  current execution is Python3.12.3/private72DPI/fake devices only; fresh lookup
  finds no python3.11. Remaining acceptance: prescribed actual final-source and
  artifact receipts on each required platform. Next action use separately
  authorized disposable isolated workers/platform sessions under docs/ci.md
  and docs/remote-development.md, without host disks or physical unattended-PC
  changes. Hosted CI is reserved for the final public candidate; this audit
  does not authorize hosting, guests, network login or publication.
- BW-P21-COMMIT — PENDING: commit/push only after required acceptance passes;
  a discovery commit requires safety: prefix. Publication separately authorized.
  No commit, push or deployed state is claimed. No approval question is needed
  for saving the local verified work and blocked checks.
- Handoff: [pass21 README](../../docs/evidence/bug-audit-20261017-pass21/README.md).
  Repo/ref/worktree/date/author are common to all P21 items above. Final local
  evidence and retention receipts live under its primary/, with independent
  reviews in discovery/, ui/ and runner/. Historical/platform reconciliation
  remains the next qualification action; local retention is authenticated.



## BW-BUG-AUDIT-20261017-PASS20 — LOCAL VERIFIED / QUALIFICATION BLOCKED

- Date/author:2026-10-17 / Codex; checkpoint19:49 UTC. All items below share
  repo BeamoTech/beamo-wipe, branch fix/safety-audit-20261015, HEAD
  35107a8d1a701093eac876a58ab4efd50e291673, worktree `/root/dev/Beamo Wipe`.
  Local uncommitted source; prior dirty work preserved; index empty. No push,
  hosted CI, guest, device, firmware, host-settings or publication action.
- Fixed and locally verified: mounted generic dm/whitespace TYPE uncertainty;
  audio constructor/start/acceptance interruption ownership; complete Tk graph,
  partial-constructor/adoption/startup/run teardown, exact peer-preserving traces,
  creator-thread native retirement, Image preinit state and closed callbacks.
  Original destructors/tracebacks/assertions preserved; product GC modes and
  thresholds unchanged (one owner-only GC-stop callback is added).
- Source779 inputs:768 starting inputs unchanged,3 runtime files changed
  (audio_jobs.py,discover.py,ui/tk_wizard.py),8 new canonical modules/149cases.
  Start771 equals pass19 final. RuntimeSHA
  c3a9b4c2145e86203eb7669e5073b0fb7de0a932eb2920b5b881c58fba6af2aa;
  freezeSHA bc83136ee6bd52c8ef4c80206c9b80b958845f839546eb57d8d518263d59ca04.
- Original exact149 canonical replay on authenticated58 starting src:88FAIL
  (86AssertionError+2controlledRuntimeError),61controls,0errors/skips. Final
  localized663PASS; native/busy/collection106PASS. Independent exact11-input
  source review and all779 source/archive/diff readback PASS.
- Final fresh9 local phases PASS: lint/types,preview,negative safety,Go1.26.8
  version/race/vet/350000fuzz/actualWindowsPE32+crossbuild, main9907PASS and
  separateOrca1PASS. Combined9908PASS14artifactskips,0fail/error/duplicates.
  All50 retained audit modules3705cases ran/pass. Two generatedliveconfig and
  12manufacturingISO skips match exact priorIDs; crossbuild is notnativeWindows.
- All53 canonical nativechildren0exit/emptystderr/noTimeout/unraisables. Fresh
  final10sessions220originalfinalizers allcreator/returned; pools empty,oneGC
  callback,maxdepth1;12x128Fonts pressure allreleased,0errors. Source3.12.3only.
- Fresh artifact campaigns PASS:306short/actual-large logs,90evidence roundtrips,
  54advisory traces,144cancel/retrypaths,621fixtures including288cancelfiles;
  270Tk/GTKviews/27criticalTkfocus,90reportvariants/fivebundles70files. Full
  hash/manifest/archive readback PASS. Root viewedall5PNGs; GTKintrocheckbox
  belowfold concern resolved9actualnativeTabcases:3steps/fullvisibility/unchanged
  authorization ineachlanguage/textsize. No native application effects observed.
- Failed history retained: C6 final lint OptionalCanvas failure; C7 main
  9901PASS1FAIL14skips(_nav fakecontroller lacks_ui_dead); earlier private
  wrong-source134abort INVALID acceptance, constructor/Fontidentity/collectibility
  failures and corrected controls allpreserved. No failure relabeledpass.
- Evidence helper failure retained/corrected: two exclusive-created silent logs
  have sub-ms kernelmtime beforewallstart, reproduced50/50emptyfiles. Onlyknown
  silent-phase freshness check nowuses previousphase end/currentend with exact
  exclusivecreate/source receipts. Product/tests/gateresults unchanged. Existing
  TODO lintwarning is unchanged placeholderregex falsepositive, source-traced.
- BW-P20-RETENTION — DONE: independent finalreview PASS, all380 retainedfile
  hashes and36 rawstreams independently reread after retention, all779 final
  archived/current inputs match;621runnerfixtures/70reports/5captures retained.
  Existingcheckpoint preserved;116 duplicate sourcefiles archive-indexed,6unique
  metadata files preserved;0overwrites/indexempty. ManifestSHA b590d9222d8cde050747ff707bed82281015b7029be3d5f860206d73c52a74cc.
  Record primary/retention-verification.json and SHA256SUMS under pass20 evidence.
  Workingstage /tmp/pass20-primary retained. No local verification remains pending.
- BW-P20-HISTORICAL — BLOCKED: pass19's two uncanceled aborts stillunattributed;
  current ownership fixes/pass do not establish exact originalcreator/cause.
  Pass18 GTKlatency/pass16loop/pass8SIGTERM/pass9originaltrace limits retained.
  Remaining acceptance: evidenced attribution/reconciliation. Next action inspect
  original immutable logs/platform incident evidence; exact missing records may
  require external evidence. Prior audit directories/records preserve details.
- BW-P20-PLATFORMS — NOT RUN/BLOCKED: Python3.11/livebookworm,ISO/QEMU,native
  Windows,firmware,physical reconnect/readback/hardware. Remaining acceptance is
  prescribed actualplatform/worker evidence for finalsource/artifacts. Nextaction
  separately authorize disposable isolated workers/platform sessions under
  docs/ci.md and docs/remote-development.md; neveruse unattendedhost devices.
- BW-P20-COMMIT — PENDING: commit/push onlyafter everyrequired acceptance passes;
  discoverycommit needs safety: prefix. Publication separatelyauthorized. No
  current approval question is required to preserve and report these limits.
- Evidence/handoff [pass20 README](../../docs/evidence/bug-audit-20261017-pass20/README.md),
  exactsource/proof/gate/campaign/visual receipts in its primary/ and independent
  reviews in runner-boot/ and tk-lifetime/. Next action is historical evidence reconciliation and prescribed isolated-platform
  qualification; task remains blocked rather than marked complete.


## BW-BUG-AUDIT-20261017-PASS19 — BLOCKED (proved fixes; final gate and native asset lifetime fail)

- Date/author: 2026-10-17 / Codex; final checkpoint17:00 UTC. Request: another
  comprehensive pass. Repo BeamoTech/beamo-wipe; worktree `/root/dev/Beamo Wipe`;
  branch `fix/safety-audit-20261015`; HEAD
  `35107a8d1a701093eac876a58ab4efd50e291673`. All pre-existing dirty work
  preserved, index empty. Local source only; no commit/push/hosted CI/release.
- Fixed locally: discovery retains unresolved bcache/descendant filesystem and
  duplicate-holder evidence, checks contradictory transitive parents, preserves
  established mounted-error category. Tk retires its two exact owned variable
  traces. Proved fixture corrections release/settle private audio on first
  failure and retire only independent peer trace after assertions. All301/24
  original assertions and both60ms bounds preserved;1 settlement assert added.
- Source:766 start inputs exactly equal pass18 final;771 final,4 existing
  changed (discover.py, ui/tk_wizard.py, tests/test_accessible_runtime.py,
  test_checkrow_trace_lifetime_pass18.py),5 new canonical modules/214 cases;
  other762 start inputs unchanged. Runtime SHA256
  `a69d8d2d8199b71a28f5f5280bad6d4bb13f46211d0f5e68a6f1d13d99c9460b`.
  Exact9-input independent review, source/archive/diff readback PASS. Retained
  audit modules42/3556 cases; this is not a claim all ran in aborted final gate.
- Proof: exact final214 canonical cases+8 fixture probes replayed privately on
  starting source produce118 AssertionError failures/104 controls,0 errors,
  skips/deselections. Shared source never restored. Current focused329PASS;
  fresh baseline3522PASS. Original staged proofs and rejected hypotheses kept.
- Completed final phases: lint/types, preview, negative boot guard, Go1.26.8
  version/race/vet/350000 fuzz and actual PE32+ AMD64 crossbuild PASS on exact
  final771. Crossbuild does not satisfy native Windows acceptance.
- FAILED full phase1 with timing observer: main fatal Python Aborted/GC on
  audio worker, no main JUnit; Orca1PASS. Proved global PYTEST_PLUGINS breaks
  private child pytest imports (samechild exit1/no JUnit vs exit0/JUnit).
- FAILED canonical full phase2 without observer/plugin setting:7 visible early
  failure glyphs then same fatal GC/audio path, no main JUnit; Orca1PASS. No
  cancellation of either full phase. Exact native abort cause still UNEXPLAINED.
  Observer import defect cannot explain the second run. Both histories retained.
- Diagnostics: both shortened prefixes1061 actual JUnit PASS,8711 deliberately
  deselected; earlier1062 was pre-Orca selection count and is corrected in
  prefix-count-clarification.json. They release later items and are not a full
  collection reproduction. Full collection --maxfail1 then gives477PASS/1FAIL:
  test_audio_launch_ownership_pass14.py::test_start_error_after_spawn_never_leaves_a_competing_worker[False-False-True].
  next_entered.wait1 fails; final join2 fails; immediate thread snapshot locates
  live worker in tkinter/font.py:121 __del__ under Event.wait. Font creator in
  original full run remains unassigned; six later glyph IDs unconfirmed.
- BW-P19-TK-ASSET-LIFETIME — BLOCKED, proved/unfixed. Actual full constructor→
  run_tk→actual mainloop→supported teardown proof8 gives2 AssertionFAIL/6controls,
  0errors/skips/parenttimeouts. For normal and controlled exception routes,
  no outer owner leaves wizard-created fonts for later worker finalization;
  IDs match that child's constructor. Collector stuck2s, only owned child
  exits91. Retained-owner/live-input/peer/repeated controls pass. This proves
  ownership gap, not exact SIGABRT cause. No speculative Font neutralization,
  global GC change, traceback clearing or native-asset product fix applied.
- Exact next action for asset blocker: use retained owned normal/exception proof
  and source ownership graph to implement complete deterministic UI-thread
  release across normal exit, propagated failure and retained callbacks/worker
  references; preserve peer traces, live UI, return/exception semantics. A
  normal-only run_tk finally ui=None+gc is insufficient while exception frames
  retain self. Prove correction on private source, then focused tests, fresh
  independent review and all applicable full local gates on exact final bytes.
  No additional user approval is needed for safe fake-device diagnosis; do not
  start physical/guest/publication work without its separate authority.
- Extra Font provenance observer changed GC pressure and passed relevant region
  without reproduction. Root deliberately stopped it: SIGINT16:56:14 UTC was
  ignored (observed mask); exact PID/start/owned ancestry revalidated, SIGTERM
  16:57:22.335849 UTC, exit143, zero direct children. CANCELED/NOT ACCEPTANCE,
  no final JUnit. Explicit intent/signal receipts retained. This is separate
  from both uncanceled aborts and old pass8 unattributed SIGTERM.
- BW-P19-FINAL-ARTIFACTS — HELD/NOT RUN: prepared runner306 short/large cases,
  90 evidence roundtrips/54 advisory traces,144 cancellation paths,270 geometry
  views and90 report checks. Zero fresh campaign fixtures/reports/screenshots;
  no earlier campaign evidence reused. After canonical main+Orca pass, run
  prepared serial scripts, authenticate every artifact and view all5 PNGs.
- BW-P19-QUALIFICATION — PENDING: original fail/fix/source review recorded;
  native asset correction, canonical plain gate, final campaigns/readback and
  every applicable acceptance still required. No commit/push until gates pass;
  eventual disk-selection commit must use safety: prefix. No release authority.
- Retained historical blockers: pass18 original74.932779ms first GTK click;
  pass16 loop incident review; pass8 SIGTERM attribution; pass9 original timing
  trace. Fixture cleanup fixes do not explain those incidents. ISO/QEMU/native
  Windows/physical reconnect/firmware/hardware NOT RUN/BLOCKED under current
  environment; no physical media/host settings/guest changed.
- Durable evidence: docs/evidence/bug-audit-20261017-pass19/README.md and
  primary/{source-freeze,source-artifact-verification,native-asset-original-review}.json;
  complete failed logs/JUnit/JSONL/binary in raw-evidence.tar.gz plus exact hash
  index and SHA256SUMS. Working staging /tmp/pass19-primary and /tmp/pass19-ui
  retained. Initial/mid checkpoints preserved. Final retention/readback receipt
  records actual limits; pending checks are not passes.
- Final17:02 UTC readback PASS: all197 retained manifest files,29 archived raw
  streams and771 current source inputs authenticated; index empty. Manifest
  SHA25624f5954b7858bfc58f341a2d56a37616a0e9d4a4d092805c9422cacc655f0fda.
  Eight completed phases remain PASS; canonical phase remains FAILED. No owned
  test process remains. Full log/asset proof/native/canceled/unrun distinctions
  match final-retained-verification.json. Initial archive-lookup verifier
  mistake (small logs remain plain) was corrected and recorded; no bytes lost.


## BW-BUG-AUDIT-20261017-PASS18 — BLOCKED (three proved fixes; GTK latency gate failed)

- Date/author: 2026-10-17 / Codex. Request: another comprehensive pass.
- Repo/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`; branch
  `fix/safety-audit-20261015`; HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Local fixes: discovery retains pathless hardware alias bridges and candidate
  uncertainty as exclusion evidence; curses requires an enabled action in the
  displayed frame before Enter; destroyed Tk checkbox rows retire exactly their
  owned variable trace. Shared fail-closed gates and all peer observers remain.
- Source: 762 starting inputs exactly match pass17; 766 final inputs; exactly
  three runtime files changed, four new modules / 332 cases. Other 759 starting
  inputs and all prior dirty work preserved. No tracked test changed; index empty.
  Runtime SHA256 `bebdb2425c6135dc79ad9dd37c89d4995173a8ffc8183edb4515cb1c726f89b7`.
  Changed files: `src/beamo_wipe/discover.py`, `ui/console_wizard.py`,
  `ui/tk_wizard.py`; exact module names/hashes in final freeze and peer receipt.
- Failing proof: final canonical 332 test bytes replayed privately on exact
  starting source yield 137 AssertionError failures / 195 controls, zero errors,
  skips or deselections. Shared source never restored. Independent seven-input
  peer review and complete source/archive/diff readback pass.
- Completed local checks: baseline 3,190 passes; fixed/adjacent 1,062 passes.
  Lint/types, preview, private boot-guard negative mutant, pinned Go 1.26.8
  race/vet/350,000 fuzz executions and actual PE32+ AMD64 test cross-build pass.
  Cross-build is not native Windows acceptance.
- FAILED canonical gate: main 9,543 passes / 14 image-only skips / one failure;
  separate Orca one pass. Combined 9,544 passes / 14 skips / one failure,
  zero errors/duplicate IDs. All 37 retained audit modules / 3,342 cases pass.
  `tests/test_accessible_runtime.py:1620` first sound-dialog click took
  74.932779 ms against unchanged 60 ms bound. Full failed logs/JUnit/binary/
  source freeze preserved before follow-up. No cancellation or blind retry.
- Diagnostic: one bounded four-test observational replay passes unchanged
  assertions; discovery on worker, pending poll returns promptly, barrier released
  and worker settled. This does not explain the earlier 74.9 ms delay. Host load/
  pressure sample cannot attribute it. No speculative product change.
- BW-P18-GTK-LATENCY — BLOCKED: remaining acceptance is an evidenced cause and
  correction (if warranted), affected original/fixed cases, refreshed source
  review and all applicable passing gates. Exact next action: use retained
  first-failure timestamps/trace with bounded native/Python observation to
  reproduce and distinguish construction/render, worker launch, native display
  waiting and scheduling. Do not raise timing limits or call a later pass an
  explanation. No owner permission is needed for fake-device diagnosis; native
  host/device/guest acceptance remains outside the authorized environment.
- BW-P18-GTK-FIXTURE — FIXED LOCALLY in pass19 (qualification blocked): source confirms first timing assertion precedes
  release-finally. Prove forced first-assertion failure cleanup, then include the
  timed click in existing try/finally and confirm owned-worker settlement before
  audio mocks retire. Preserve both 60 ms bounds and every closed-dialog check.
  This is failure cleanup, not an established cause of click latency.
- BW-P18-TK-FIXTURE — FIXED LOCALLY in pass19 (qualification blocked): independent peer observer in first new trace test
  captures its variable and may retain the interpreter. Exact next action: prove
  the harmless private Tk cycle, then retire only peer_token in finally after
  existing assertions/evidence, including old-source failing paths. Preserve
  product traces and callback error observers. This later fixture cannot explain
  the earlier GTK failure. This was the original pass18 status; pass19 proved
  and corrected both fixture cleanup gaps (exact proof/changed bytes above),
  while broader final qualification remains blocked.
- Held acceptance: fresh runner/cancellation/geometry/report campaigns NOT RUN
  because local gate failed; zero new campaign fixtures/reports/screenshots.
  Prepared scripts retained. Do not reuse pass17 campaign evidence for new bytes.
  User's stop-on-blocker instruction prevents continuing acceptance as if passed.
- Isolation: no-space interpreter plus eight immutable child-PATH guards;
  12 admission probes pass; two actual allowed offline SDK fixture listings;
  zero forbidden guarded fallbacks. Guards are not a universal OS sandbox.
  Canonical main/Orca alone concurrent; diagnostic followed their completion.
  Private 72-DPI X11; no real engine/physical target, loop acceptance, guest,
  native Windows execution or hosted job this pass.
- Historical blockers retained: pass16 native regular-file loop-probe incident
  review; pass8 original unexplained SIGTERM/exit143 attribution; pass9 original
  unavailable timing trace. This pass cannot explain the older events. ISO/QEMU,
  native Windows, physical reconnect, firmware and real-hardware acceptance remain
  NOT RUN/BLOCKED under unattended-host constraints and prescribed worker gates.
- Remaining final action after diagnosis/correction: refresh freeze/proofs/peer
  review for changed bytes, pass applicable canonical local gate, then execute
  prepared fake campaigns serially and authenticate all new artifacts. Qualify
  final public artifacts only on prescribed authorized workers/physical sessions.
- Source local/uncommitted. Nothing pushed, merged, deployed or released.
  No commit/push while requested acceptance remains blocked; eventual discovery/
  authorization commit must use `safety:`. Publication separately authorized.
- Durable result: `docs/evidence/bug-audit-20261017-pass18/README.md`, exact source,
  proof, failed-gate, diagnostic, cross-review and retention receipts/SHA256SUMS.
  Large raw logs/JUnit/binary compacted with byte index and checked readback.
  Prior checkpoints in `primary/checkpoint-history.md`. Working staging retained
  at `/tmp/pass18-primary` and `/tmp/pass18-ui`. No required work marked complete.


## BW-BUG-AUDIT-20261017-PASS17 — BLOCKED (four areas fixed; final local verification passes; historical/platform acceptance pending)

- Date/author: 2026-10-17 / Codex. Request: another comprehensive bug audit.
- Repo/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`; branch
  `fix/safety-audit-20261015`; HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Local outcome: four proved areas fixed in `discover.py`, `nwipe_runner.py`,
  `ui/console_wizard.py`, `ui/tk_wizard.py`. All inherited hardware candidates,
  physical duplicate context and malformed-WWN uncertainty remain exclusion
  evidence; meaningful parent IDs remain authoritative. Native no-erasure
  records require complete timestamp/severity provenance; raw guards retain
  negative contradictory context. Plain TTY discards pre-expiry typeahead and
  refuses unusable/real piped consent. Startup cancels only its owned callbacks.
- Source identity: 762 frozen inputs; runtime SHA256
  `b4e76a50ff6e9d376b6a56f7d1b469192dd4284347923ac1aca02254664bf423`.
  Exactly four runtime inputs changed from pass16; all other 750 starting inputs
  and earlier work preserved. Eight new modules add 1,247 cases; 33 retained
  modules contain 3,010 cases. No tracked fixture changed during this pass.
  Exact final 12-file peer review matches all four runtime/eight new test inputs.
- Proof: exact private starting-source replay of the final high-level modules
  gives 496 AssertionError failures / 739 controls, zero errors/skips. Twelve
  new helper-only controls deselected only on old source execute in the final
  gate. Original source never restored in the shared checkout. All 754 starting
  inputs, 33-module archive, incremental and cumulative patches read back exactly.
- Final local gate: nine phases exit 0; 9,213 unique Python/Orca passes / 14 same
  image-only skips, zero failure/error/duplicate IDs. All 3,010 retained audit
  cases pass. Lint/types, preview, private boot-guard negative mutation, pinned
  Go 1.26.8 race/vet/350,000 fuzz executions pass. Actual PE32+ AMD64 Windows test
  cross-build verified (9,021,440 bytes, SHA256 d05ac4db6463aa6d7f51188f3bcfcfb4891aeab549ab481843538114904a76d9);
  native Windows acceptance is NOT RUN. Skips remain two generated live-config
  and 12 manufacturing/ISO cases, not acceptance passes.
- Fresh final campaigns: 153 short comparisons and 153 actual >1MiB fake polls,
  90 authenticated evidence/export-readiness/recovery/tamper roundtrips,
  144 cancellation/retry cases, 270 Tk/GTK small-screen layouts and 90 report
  cases pass. All 27 critical Tk inputs fully visible; five actual PNGs viewed.
  All 621 runner fixtures (including 144 log/lock pairs) and 70 report files in
  five COMPLETE-authenticated bundles hash/read back exactly. Zero guarded native
  acquisitions or callback errors. Long body content intentionally scrolls.
- Runtime isolation: no-space interpreter and eight immutable rejecting PATH
  guards; 12 admission probes pass. Three actual SDK calls across baseline,
  failed candidate and final gate only list owned local fixture files offline.
  No forbidden PATH fallback. These guards are not a universal OS sandbox.
  Substantive final campaigns ran serially after canonical main/Orca finished.
  No real engine, physical target, loop acceptance, guest or hosted job this pass.
- Failed history retained: first full candidate failed three existing runner
  contradictions; 108 added cases proved the regression before correction.
  Root caught lost physical-context and malformed-WWN alternatives before final
  acceptance; separate failing proofs and corrected duplicate/console fixtures
  retained. Two imported-fixture F811 annotations preserve identical ASTs and
  assertions. One trailing documentation space stopped result authentication;
  corrected without changing any gate input, then authentication passed. Earlier
  statuses are preserved in `primary/checkpoint-history.md`, not counted as passes.
- Final source remains local/uncommitted; index empty. Nothing pushed, merged,
  deployed or released. Methods, claims, pins, argv and automation unchanged this
  pass. Eventual discovery/authorization commit must use the `safety:` prefix.
- Remaining acceptance/blockers: review pass16's native regular-file loop-probe
  incident; obtain/reconcile pass8's original unexplained SIGTERM/exit143 platform
  attribution and pass9's unavailable original failed timing trace. Later passes
  cannot explain those historical events. ISO/QEMU, native Windows, physical
  reconnect, firmware and real hardware acceptance remain NOT RUN/BLOCKED under
  the unattended-host constraints. This record grants no worker/device/release
  authorization. Do not claim those checks passed or commit/push before the
  applicable requested acceptance gates pass.
- Exact next action: review incident evidence and recover the missing platform
  signal/timing records; retain unresolved items if originals are unavailable.
  Qualify a final public candidate only on prescribed isolated workers and an
  explicitly authorized physical session. Publication remains separately authorized.
- Durable result/evidence: `docs/evidence/bug-audit-20261017-pass17/README.md`,
  source/gate/campaign/visual/readback receipts and SHA256SUMS. Exact bulky raw
  transcripts/JUnit/test binaries are compacted with byte indexes; starting inputs,
  final regression modules, runner fixtures and report bundles have checked archives.
  Working staging remains `/tmp/pass17-primary`, `/tmp/pass17-runner`, `/tmp/pass17-ui`.


## BW-BUG-AUDIT-20261017-PASS16 — BLOCKED (four bugs fixed locally; gates pass; incident and historical acceptance review pending)

- Date/author: 2026-10-17 / Codex. Request: another comprehensive audit pass.
- Repo/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`; branch
  `fix/safety-audit-20261015`; HEAD
  `35107a8d1a701093eac876a58ab4efd50e291673`.
- Outcome: four independently proved bug classes fixed in discover.py and
  ui/tk_wizard.py / ui/accessible_wizard.py: filtered physical duplicates could
  manufacture target uniqueness; optical cmdline fallback omitted physical
  competition; modal held Escape became a fresh parent action; destroyed Tk
  widgets left queued Tcl callback commands. Three new modules add 398 cases.
  Preserve all 27 prior local fixes, 22 prior modules / 1,365 cases and earlier
  evidence. Retained/new regressions: 1,763 cases in 25 untracked modules.
- Four existing fixtures corrected without deleting any assertion: mapped-draw
  readiness retains the 140 ms interval; two AST fixtures bind the actual shared
  guard; Tcl-only picker models its leaf hierarchy. Original assertion counts
  38 / 19 / 9 / 11 preserved, one readiness assertion added. New native fixtures
  set geometry before mapping and distinguish real fresh key timestamps.
- Source: 754 inputs frozen, 744 of 751 starting inputs unchanged. Only three
  runtime files and four existing fixtures changed; three new test inputs.
  Runtime SHA256 `008add544330133a4cf979d39327dae3ccfd341925cb897b8ca19c23f983d2ab`.
  Exact source/fixture patches, starting archive, 25-module test archive and
  original/final receipts retained. Three source peers approved exact assigned
  final bytes; primary independently verified all 58 source/static hashes.
- Proof: exact private starting-source replay of final 398 cases gives
  203 AssertionError failures / 195 controls, zero errors/skips: discovery159,
  modal18, explicit Tcl-bgerror26. Shared source never restored. Native Escape
  and callback/default-bgerror traces independently support the defects.
- Completed final local gate: nine phase exits 0, 7,966 unique passes / 14 same
  image-only skips, no failure/error/xfail/duplicate IDs; every 398 new and 1,365
  prior regression passes. Fresh main/Orca reports, pinned Go1.26.8 uncached
  race/vet/350,000 fuzz executions, preview/negative and actual Windows PE32+
  AMD64 cross-build verified. Native Windows acceptance remains NOT RUN.
- Fresh final campaigns: 153 short and 153 actual >1MiB fake polls, 90 authenticated
  evidence/export-readiness/recovery roundtrips, 144 cancellation/retry cases,
  270 Tk/GTK layouts, 90 report cases all pass. Zero campaign native acquisitions
  or callback errors. All 153 large logs / 90 evidence-sidecar pairs (333 files),
  70 report files and five actual PNGs independently authenticated/viewed;
  27 critical Tk inputs fully visible. Exact readback/retention verification passes.
- Failed/corrected history is preserved in evidence and checkpoint-history.md:
  initial baseline 1,676PASS/7focusFAIL; initial adjacency2,073PASS/8new-fixtureFAIL;
  type gate2errors; private-display/observer setup corrections; full space-bearing
  interpreter run23FAIL/7,942PASS/14skips plus1OrcaPASS. Same existing interpreter
  through a no-space alias fixes Linux shebang execution; 23 exact failed cases
  pass after that and the accurate Tcl leaf fixture. No assertion weakened.
- Boundary incident: invalid fake executable shebangs fell through to real tools.
  Public metadata reads and ordinary-file xorriso work occurred. Three native
  regular-file loop probes returned0 and reported attachments/ownership-checked
  cleanup. Empty fake bookkeeping was initially misread as zero real loops; that
  statement is corrected. Original loop IDs were not retained. Read-only follow-up
  found no matching fixture backings or remaining probe-prefix directories; no
  detach performed. This crossed the allowed loop-test boundary. No wipe engine
  or physical disk target was invoked. Review incident before acceptance.
- Final test orchestration rejects remote/privileged fallback. The single allowed
  actual SDK call only lists local files under a canonical private pytest tree
  with fresh config; credentials/telemetry/update checks disabled. Installed SDK
  source and independent peer confirm this; 12 intercepted guard cases and the
  actual offline test pass. Final forbidden fallback attempts: zero. No hosted
  CI, login, credential entry, external messages, commit, push, PR or release.
- One overstrict guard run was intentionally canceled: exact owned pytestPID36787
  ignored SIGINT03:21:42.296955UTC (inherited background disposition); root sent
  SIGTERM03:22:25.187569UTC. Wrapperexit1, no fresh main JUnit; stale prior report
  rejected. Tracked pytest/child exited. This is fully attributed and distinct
  from historical pass8. No auxiliary runtime campaign overlapped final gate.
- Remaining acceptance: review this incident/guard evidence; obtain attributable
  platform execution/signal evidence for pass8's06:29UTC SIGTERM/exit143 and the
  unavailable original pass9 failed timing trace. Later passes cannot explain
  those historical events. Exact next action: obtain/reconcile those records,
  review the incident, revalidate acceptance, then make a `safety:` commit/push
  only when every required acceptance criterion passes. Source remains local,
  uncommitted, index empty. No release authorization.
- Separate final-public ISO/QEMU/native Windows/hardware/firmware/physical
  reconnect qualification remains NOT RUN/BLOCKED. Follow existing qualification
  records and current AGENTS; an isolated authorized worker is required.
- Evidence/result: `docs/evidence/bug-audit-20261017-pass16/README.md`.
  All intermediate checkpoints preserved in `primary/checkpoint-history.md`.


## BW-BUG-AUDIT-20261016-PASS15 — BLOCKED (five new bugs fixed; local gates pass; historical acceptance evidence pending)

- Date/author: 2026-10-16/17 / Codex. Request: another comprehensive pass.
- Repository/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`.
  Branch `fix/safety-audit-20261015`;
  HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Outcome: five proved bug classes fixed in seven runtime files: omitted
  physical alias bridges, filtered same-path contradictions, empty-screen nested
  wheel routing, normalized UTF8 snapshot cap, and exact positive hidden-storage
  advisory records. Four new modules add 578 cases. All 22 prior fixes, 787 prior
  cases and three fixture updates are preserved. Total retained/new regressions:
  1,365 in 22 untracked modules. Safety-only context never supplies selectable
  disks or token peers. No method/argv/token/countdown/owner/pin/claim/launcher/
  build/publication changes. Future commit requires `safety:`.
- Final source: 751 frozen inputs; 740 other starting inputs unchanged.
  Runtime SHA256 `9f34e674c64184b4a7d36fb77498d8dee7ad71321bb979c1616b7cc1772be43a`.
  Complete/incremental patches, exact 22-module archive, original 58-source
  archive and receipts retained. Three source peers approved assigned final
  bytes; final discovery path-API review supersedes earlier snapshots. Primary
  independently inspected the union and complete accumulated diff.
- Proof: private original replay of 578 cases gives 298 intended failures /
  280 controls, zero errors/skips, all 58 starting hashes verified. Each failure
  attributed: 60 missing SafetyError and 238 AssertionError. Fresh baseline
  1,105 passed; adjacency 2,275 passed; malformed-path focused 473 passed.
  Final alias 288, duplicate 36, wheel 8, UTF8 roundtrip 30, runner 432 short +
  324 large, geometry 270 and report 90 cases passed. Zero native effects or
  callback errors; 27 critical controls fully visible; five native PNGs viewed;
  108 large and ten UTF8 fixtures authenticated.
- Failed/corrected history retained: initial wheel guard hit picker (542/574),
  moved to empty; early malformed-ID refusal (2264/2271), refined per-field
  safety context plus four controls; first full main 7,566 passed / one failed /
  14 skips caught a direct invalid-path exception. It now returns a fully empty
  unidentified result. Focused 473 and all final campaigns/gates repeated on
  the new freeze. Setup/import/selection and tail-vs-complete receipt mistakes
  distinguished. No relaxed test/gate, stop/kill or unexplained termination.
- Final applicable local gate: nine phases exit 0; 7,568 unique passes / 14 same
  image-only skips; zero failures/errors/xfails/duplicate IDs. All 578 new and
  787 prior regressions pass. Pinned Go 1.26.8 race/vet/350,000 fuzz executions
  pass. Actual Windows PE cross-build inspected (native acceptance not run),
  preview and 70 actual report bundle files authenticated. No auxiliary runtime
  campaign overlapped full pytest. Retention verification passes for exact
  source/tests/archives/index/diff; final artifact counts are in evidence README.
- State: local/uncommitted/index empty; no commit/push/PR/hosted CI/release.
  Effects use fake devices/processes, regular files, owned private X11/DBus.
  Evidence: `docs/evidence/bug-audit-20261016-pass15/README.md`, with original
  proofs, failed history, exact check commands and completed receipts.
- Remaining acceptance criteria: attributable pass8 SIGTERM sender/cause and
  pass9 failed timing evidence remain unavailable; later passing tests cannot
  explain them. Exact next action: obtain platform execution/signal evidence
  and attributable failed timing trace, revalidate acceptance, then make a
  `safety:` commit/push only when all required gates are satisfied.
  Separate final-public ISO/QEMU/native Windows/hardware/firmware/reconnect
  qualification remains NOT RUN/BLOCKED. Follow its existing qualification
  record and current AGENTS; publication needs separate explicit authorization.

## BW-BUG-AUDIT-20261016-PASS14 — BLOCKED (three new bugs fixed; local gates pass; historical acceptance evidence pending)

- Date/author: 2026-10-16 / Codex. Request: another comprehensive audit, continued.
- Repository/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`.
  Branch `fix/safety-audit-20261015`;
  HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Result: three proved defects fixed in audio_jobs.py, discover.py, safety.py
  and ui/tk_wizard.py. Mixed serial/WWN chains retain boot/mounted protection
  and final guard checks while preserving contrary anchor WWNs. A rejected
  audio thread launch cannot consume a replacement queue. Focused body controls
  are revealed after focus and final wrapping, preserving manual scroll,
  stale redraws, footer behavior and consent. No method/argv/token/countdown/
  owner/engine pin/claims/launcher/build/publication changes. Future commit
  must use `safety:` after acceptance.
- Preservation: all744 starting inputs matched;747 final inputs frozen.
  Four runtime files and one existing wheel fixture are the only changed
  starting paths;739 other starting inputs unchanged. Preserve19 prior fixes,
  15 prior modules/580 cases, two prior tracked fixtures and all earlier work.
  Three new modules/207 cases bring retained/new regressions to787 in18
  untracked modules. Wheel fixture settles native focus, checks overflow
  independent of offset, cleans setup errors and gives directional headroom;
  all38 assertions retained, with only the offset-dependent assertion replaced.
- Original proof: primary72-case fake public discovery has24 violations/48
  controls; event-only audio trace proves overlapping actions after rejected
  launch; original270-case native geometry has246PASS/24 clipped-focus FAIL.
  Primary privately restored58 exact starting source/static files, verified
  hashes and ran final207 tests:108 intended FAIL/99 controls,0 errors/skips.
  Alias72/96, audio8/2, UI28/1. Every failure independently attributed:
  24 expected missing SafetyError failures and84 AssertionErrors. Shared
  source never reverted. Three bounded delegates hit provider quota after
  source/proofs/preparation; primary independently validated and implemented.
  No final independent peer patch approval is claimed.
- Focused checks: baseline42 modules898PASS/0 skips; combined98 modules1645PASS;
  affected UI100PASS including10 startup cases, all normal exit. These checks
  precede annotation-only cleanup; final gate validates exact final bytes.
  Fresh558 fake discovery cases PASS/zero native acquisition. Runner150 short
  cases/450 method assessments,96 actual >1MiB fake polls including late Stop
  and1 explicit evidence-cap refusal PASS/zero mismatches.17 large fixtures
  authenticated. Final270 Tk/GTK geometry cases PASS/zero effects or callback
  errors;27 focused input/owner/token controls fully visible;3 exact final
  native PNGs independently viewed.
- Failed/corrected history retained: first focus repair202/207; five final
  wrapping failures fixed. Initial adjacency hung because an old fixture's
  setup assertion leaked a Tk root before cleanup;350ms native two-root trace
  proves thread-wide mainloop cause. Primary verified owned PID604704/cwd/JUnit,
  disabled core dumps and intentionally sent SIGABRT at21:39:56.670888UTC;
  exit134 is not a pass. This stop is fully attributed and distinct from pass8.
  Diagnostic90 cases88PASS/2FAIL; intermediate100 cases99PASS/1 directional
  setup FAIL; final100PASS. Two lint stops fixed an unused import and explicit
  optional types, without ignores or relaxed gates. Initial runner expectation
  exceeded intentional1MiB evidence cap; auxiliary control corrected, no runner
  source change. Python after_cancel geometry cleanup introduced54 fit errors;
  independent log review rejected provisional exit0. Tcl-only timer cancellation
  preserves bindings until normal destruction; strict final270 rerun PASS with
  zero callback errors, Traceback or bgerror. Original/provisional scripts,
  logs, receipts and checkpoint history retained.
- Final local gate: all9 phase exits0. Lint/types/security/shell, fake preview,
  negative safety, Go1.26.8 version/uncached race/vet, Windows AMD64 test
  cross-build,350000 fuzz executions and canonical separate private72DPI
  Orca/main sessions. Main6989PASS/14 expected skips527.49s; Orca1PASS59.445s.
  Combined6990 unique PASS,0 failure/error/xfail/duplicate IDs; all207 new and
  580 retained regressions PASS. Unchanged sound timing case PASS. Exact14 skip
  IDs/reasons match pass13:2 generated live-config and12 manufacturing-ISO
  checks; these are not image/native acceptance. No auxiliary runtime campaign
  overlapped full pytest. No applicable local check remains pending.
- Final aggregate runtime SHA256:
  `ebe614cd285be76d948e81c7f8a04be48240ba4a95a4baab9e3ba9e040197dbb`.
  Complete source patch SHA256:
  `f0aed7147f124a6b9195393de80d20aa170fbeb77b2ce97a3d83d2f3c7104cb0`.
- Artifacts:90 final-source report cases across3 methods/3 languages/5 count
  variants/2 log sizes PASS;70 bundle files/manifests authenticated, five actual
  owner/share/result/HTML bundles inspected. Preview185540 bytes retained/hashed.
  Windows PE32+AMD64 test binary8974848 bytes,
  SHA256 `6f58501de27f93649fe59e6ff2a84b4a089639a9b9ecb12fa2951ec8297f5089`;
  cross-compilation only, native acceptance false, binary outside git.
  All final owned campaigns exited normally.
- Durable evidence: `docs/evidence/bug-audit-20261016-pass14/README.md`.
  Retention PASS:747 frozen inputs,18 exact untracked modules,210 exact original
  artifacts,211 retained hashes including the initial verification receipt,
  matching source/fixture patches, empty index and clean diff whitespace.
  Exact originals compressed; native PNG/JSON/XML/Python bytes preserved.
  Readable transcript copies normalize trailing whitespace only.
- Remaining acceptance criteria/blockers: pass8 SIGTERM06:29UTC/exit143 sender
  and cause, plus pass9 failed timing attribution, remain unavailable. Later
  passing tests do not explain either. Exact next action: obtain platform
  execution/signal audit and an attributable failed timing trace, then revalidate
  acceptance before commit/push. Separate qualification record owns ISO/QEMU/
  native Windows/physical/firmware/reconnect NOT RUN / BLOCKED for a future
  public candidate; current AGENTS reserves hosted gates for that candidate.
- State: LOCAL UNCOMMITTED; index empty. No staging/push/PR/merge/release,
  hosted CI, native engine/inventory/device/USB, power/firmware, guest/loop/
  passthrough, credential access or external messaging. Shared guide absent;
  recorded owner continuation applies. Current task/AGENTS govern; notes
  grant no additional authority.

## BW-BUG-AUDIT-20261016-PASS13 — BLOCKED (three new bugs fixed; local gates pass; historical acceptance evidence pending)

- Date/author:2026-10-16/Codex. Request:another comprehensive audit.
- Repo/worktree/branch:BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; HEAD`35107a8d1a701093eac876a58ab4efd50e291673`.
- Result:three new proved defects fixed locally in discover.py and
  ui/tk_wizard.py; two new modules165regressions. Preserve16prior fixes,
  13prior modules415cases, two prior fixture updates and all earlier evidence.
  All742starting inputs matched; final744inputs frozen and verified.
- Fixes:EFI/UEFI name tokens prevent ordinary Benefits/Definitions from
  manufacturing OS-removal guidance; nativeTk input claimed once after actual
  rootMap then existing renderer restores intendedscreen focus; generalbody
  prose wheel routed only to currentcanvas, preserving nested/native/custom
  scrollers/footer/picker/focus/consent. Boot eligibility/exclusion, hardware
  identity/token/owner/countdown, method/argv, enginepin/claims/publication
  unchanged. Discovery edit requires future `safety:` commit after acceptance.
- Proof:before-edit classification16trace8wrong/8controls; nativeUI9cases
  4intendedFAIL/5controls. Primary privately restored all58exact starting
  source/static files, hashverified, final165cases60intendedFAIL/105controls,
  0errors/skips15.252s (classifier32/72,UI28/33). Shared source never reverted.
  Independent exact-hash source/test reviews approve final classifier/Tkdelta.
- Completed focused checks:primary733PASS/0skips; classifier104PASS plus
  adjacency644PASS/0skips and156freshfake namespace/mount/RO/duplicate/identity
  casesPASS/zero nativeacquisition. Runner686PASS/0skips across58modules;
  216freshlarge-logcases/648terminalpolls full/projection outcomes/checksagree,
  exactbytes unchanged. UI61PASS17.195s plus630adjacentPASS120.512s/0skips.
  Two unedited72DPI actual800/1600fullroot captures independently viewed and
  bytes/dimensions/geometry/focus/nativehit/yview/consent/teardown verified.
  Counts overlap fullgate. No speculative nestedtopology/Unicode/recoveryfix.
- Failed/setup history retained:originalnativecanvas gutter assumptionwrong
  (label coverspoint), correctedhit-tested proof passes intendedcontrols.
  FirstfixedUI53=42PASS/11FAIL:9focus failures exposed idle-before-map repair;
  exactorderingtrace proved rootMaplater; correctedMap→idle→claim→renderer.
  Two newfooterfixtures correctedparentonly, assertions unchanged;53then61PASS.
  Auxiliary XMLreview optionaltype/message assumptions and bundleSUMMARYfilename
  assumption corrected against actual traceback/schema; rawXML/source/artifacts
  unchanged, explanations/versions retained. Tk filehash label clarified against
  aggregate runtimehash; original note retained. No test/gate weakened.
- Final localgate:all9phase exits0, lint/types/security/shell, fakepreview,
  negative safety, Go1.26.8 version/uncached race/vet, WindowsAMD64 test
  crossbuild,350000countedfuzz and fullpytest canonical separateOrca/main72DPI
  sessions. Main6782PASS/14unchangedexpected image-onlyskips551.25s;
  Orca1PASS60.06s. Combined6783uniquePASS,0fail/error/xfail/duplicateIDs;
  new165+retained415allPASS; unchangedsoundtimingcasePASS. ExactskipIDs/reasons
  matchpass12. No auxiliary runtimecampaign overlapped fullpytest.
- Runtime source SHA256:
  `e7efbba20755ff7496533504259adb4ef63eb8fafc43b52fa6fabe148cf1297d`.
  Complete sourcepatch SHA256:
  `efd6dcdc0280453fda89748a64575c6c354bfd92f895dfa0040df52352eace0a`.
  Final-source90case reportmatrix3methods/3languages/5countvariants/2sizesPASS;
  70generatedfiles/manifests authenticated, fiveactualJSON/result/HTML/share
  bundles inspected. Fakepreview185540bytes hashed/retained. Windows actual
  PE32+AMD64 testbinary8974848bytes, hash6f58501de27f93649fe59e6ff2a84b4a089639a9b9ecb12fa2951ec8297f5089;
  crosscompileonly/nativefalse, binaryoutsidegit. Allownedjobs retired.
- Durable evidence:`docs/evidence/bug-audit-20261016-pass13/README.md`.
  RetentionPASS:744frozeninputs,15exact uncommittedtestmodules,137exactoriginal
  artifacts,141retainedartifacthashes including initialverificationreceipt;
  source/fixturepatchesmatch, emptyindex/diffcheck. No required applicablelocal
  check remains pending; historicalacceptance staysblocked.
- Remaining acceptance/blockers:originalpass8 SIGTERM sender/cause at06:29UTC
  andpass9 failedtimingattribution remain unavailable; laterpasses cannot
  establish either. Exactnextaction:obtain platform execution/signal audit and
  attributable failedtimingtrace, then revalidate acceptance beforecommit/push.
  Shared `/root/dev/AGENTS.md` absent; recordedownercontinuation applies.
- State:LOCAL UNCOMMITTED; no staging/push/PR/merge/release/hostedCI oractual
  engine/nativeinventory/device/USB/power/firmware/guest operation. Separate
  BW-BUG-AUDIT-20261015-QUALIFICATION remainsNOTRUN forfuturepubliccandidate:
  ISO/QEMU/nativeWindows/physical/firmware/reconnect acceptance. Source/evidence
  notes grant no authority; current task/projectguide govern.

## BW-BUG-AUDIT-20261016-PASS12 — BLOCKED (six new bugs fixed; local gates pass; historical acceptance evidence pending)

- Date/author: 2026-10-16 / Codex. Request: another comprehensive audit.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Result: six new proved bugs fixed locally in five application modules;
  four new modules contain200 regression cases. Ten existing pass8/pass10/
  pass11 fixes, nine prior modules/215cases and earlier evidence preserved.
  Starting738 inputs matched; final742 inputs frozen and verified.
- Proven fixes: prefixed Error Summary negative rows/delimiters cannot be
  ignored in favor of success; refused remembered sound output uses actual
  default and allows same-output retry; scrolled sound content keeps Stop/Close
  visible; native Tk startup focus accepts Escape; configured startup geometry
  centers windowed mode and keeps fullscreen origin0,0; graphical stall notices
  persist until stage/terminal transition with one-shot console/serial behavior.
  No discovery/selection/method/argv/authorization/claims/pin/publication change.
- Original proof before edits: runner101cases67FAIL/34controls; native fake
  output/input/rectangle and exact post-render fake-clock traces prove all5UI
  defects. Root independently restored exact58starting source/static files
  in a private import root and ran final200 cases:135intendedFAIL/65controls,
  0errors/skips,24.66s (runner67/34,sound52/26,stall8/3,Tk8/2). Shared source
  never reverted. Independent source/test reviews approve exact final hashes.
- Focused completed checks: discovery461PASS/0skips plus1455freshfakecases;
  runner372PASS/0skips; primary report/export/power/audio328PASS/0skips;
  all99newUIcasesPASS, actual800 selection88PASS; exact final-source90case
  report/bundle matrixPASS across3methods/3languages/5countvariants/2sizes,
  with70representative generated files authenticated. Six unedited72DPI
  800/1600 native captures independently viewed and checked for bytes,
  dimensions, focus, origin and owned teardown. Counts overlap final gate.
- Failed/setup history retained separately: first UI adjacency348PASS/2FAIL
  because two Tk cleanup mocks returned MagicMock screen dimensions; only
  1600/1000 integer inputs added, original injected exceptions/destroy assertions
  unchanged; affected module5PASS. First fullgate main6611PASS/6FAIL/14skips
  (592.36s), Orca1PASS (68.21s), all200newPASS and742hashesmatch. All6failures
  were headless FakeGtk display/monitor/scroller APIs missing before intended
  operations. Only fake APIs updated; independent review confirms all18 test/
  helper ASTs identical, timing/thread/cancel assertions intact. Full affected
  module19PASS/0skips. Exact firstgate logs/XML/freeze retained as initial-gate-*.
  Auxiliary matrix expectation/count assumptions and superseded imprecise
  capture labels remain retained; no assertions/thresholds/gates weakened.
- Final local gate: all9phase exits0: lint/types/security/shell, preview,
  negative safety, pinnedGo1.26.8 version/uncached race/vet, WindowsAMD64 test
  crossbuild,350000 countedfuzz and fulltests. Main6617PASS/14unchangedexpected
  image-only skips (512.33s); separateOrca1PASS (61.02s). Combined6618uniquePASS,
  0failures/errors/xfails/duplicateIDs; new200+retained215cases allPASS; unchanged
  sound timing casePASS. Exact skipIDs/reasons matchpass11. All742frozenhashes
  match; source/fixture patches and13uncommitted test modules authenticated.
- Runtime source SHA256:
  `2033156897c47190995f47499a87c761e4d9c7bc7a1124d0bafd91722ab3ec31`.
  Source patch SHA256:
  `9eda22fbc8d0a297160a7086d5d59e2e85042988429daa83063573ca8f37c4a7`.
  Generated fakepreview and report bundles retained/hashed. Windows test binary
  is PE32+AMD64,8,974,848bytes, hash6f58501de27f93649fe59e6ff2a84b4a089639a9b9ecb12fa2951ec8297f5089;
  crosscompile only, binary outsidegit. All owned jobs retired; index empty.
- Durable evidence and retention verification:
  `docs/evidence/bug-audit-20261016-pass12/README.md`.
  Final retentionPASS:742frozeninputs,13testmodules,194exactoriginalartifacts,
  198retainedartifacthashes, exactsource/fixturepatches, emptyindex/diffcheck.
  No required local check remains pending; historical acceptance staysblocked.
- Remaining acceptance/blockers: original pass8 SIGTERM sender/cause at06:29UTC
  and pass9 failed timing attribution remain unavailable. Passing later checks
  cannot establish those causes. Exact next action: obtain platform execution/
  signal audit and attributable failed timing trace, then revalidate acceptance
  before commit/push. Shared `/root/dev/AGENTS.md` remains absent; prior recorded
  owner continuation applies to local work under current project AGENTS.md.
- State: LOCAL UNCOMMITTED; no staging/push/PR/merge/release/hostedCI, actual
  engine/native inventory/device/USB/power/firmware/guest operation. Separate
  BW-BUG-AUDIT-20261015-QUALIFICATION remains NOT RUN for a future public
  candidate: ISO/QEMU/nativeWindows/physical/firmware/reconnect acceptance.

## BW-BUG-AUDIT-20261016-PASS11 — BLOCKED (four new bugs fixed; local gates pass; prior attribution pending)

- Date/author: 2026-10-16 / Codex. Request: another comprehensive bug audit.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Result: four new proved defects fixed in nwipe_runner.py and
  ui/accessible_wizard.py; three new modules contain103 regression cases.
  Existing six pass8/pass10 fixes and six regression modules preserved byte-
  exactly except the two runtime files' approved additions. All735 starting
  inputs matched pass10; final738 inputs frozen and verified.
- Scope: three bounded discovery/safety, runner/recovery and UI/boot/build
  reviewers; primary report/export/privacy/diagnostic/integration review.
  Substantial test/GUI/CPU campaigns ran sequentially, with no auxiliary jobs
  alongside the final canonical separate Orca/main sessions.
- Proven fixes: modal key release now reaches existing held/repeat ledger;
  native startup focus makes Escape work with pointer outside; explicit monitor
  size/origin makes both GTK surfaces fullscreen on bare X11; normalized large-
  log relevance keeps prefixed summary rows/delimiters without changing raw
  records, terminal provenance, methods, argv, caps or progress order.
- Original evidence: input14 cases6FAIL/8controls; geometry8 at1600x1000:
  4FAIL/4controls, at800x600:3FAIL/5controls; runner81:25FAIL/56controls.
  Primary independently restored only two modules in a private import root,
  checked58 source/static hashes, and reproduced final103 cases35intendedFAIL/
  68controls,0errors/skips in14.15s. Shared source never reverted. Earlier95-
  case proof and exact checkpoint history retained separately.
- Completed focused checks: primary173PASS; discovery461PASS/0skip plus588 fake
  ownership/schema/boot/alias/duplicate cases; runner268PASS/0skip; final UI122
  PASS/0skip plus geometry8PASS at800. Four unedited72DPI full-root screenshots
  independently inspected; native dimensions/focus/hash/teardown verified.
  Report/evidence72-case matrix passes across3methods/3languages/four summary
  variants/both sizes, preserving full advisory payloads, outcome/verification,
  exact tail hashes and unchanged log bytes. Counts overlap final gate.
- Retained setup history: discovery initially lacked DISPLAY (458PASS/1setupFAIL/
  2skips); identical selection corrected461PASS under private72DPI Xvfb/D-Bus.
  UI fixture/import variants are retained and hash-disambiguated; no assertions,
  thresholds or gates weakened. Source reviews approve exact final hashes.
- Final local gate: main6417PASS/14expected image-only skips in530.31s;
  privateOrca1PASS in60.086s. Combined6418uniquePASS,0failures/errors/xfails/
  duplicate IDs; new103+retained112 cases allPASS; unchanged sound timing case
  PASS. All8phase exits0: lint/types/security/shell/developer-format, preview,
  negative safety, pinnedGo1.26.8 uncached race/vet/350000fuzz and full tests.
  All738 frozen hashes match; direct XML counts/source-patch hash agree.
- Runtime source SHA256:
  `70382edd3f47fba150187014901200bb35c1f76f46a74b4fc35f4fd327a8fb01`.
  Source patch and all9 uncommitted test-module archive contents match current
  bytes. Index empty; all owned jobs retired. Durable retention verification
  PASS:158 exact original artifacts,151 retained artifacts hashed; frozen files,
  archive contents and diff whitespace match. Evidence:
  `docs/evidence/bug-audit-20261016-pass11/README.md`.
- Remaining acceptance/blockers: original pass8 SIGTERM sender/cause and pass9
  timing attribution remain unavailable despite new passing checks. Exact next
  action: obtain platform execution/signal audit for original06:29UTC termination
  and an attributable failed timing trace before acceptance/commit/push. Passing
  reruns do not establish those causes. Shared `/root/dev/AGENTS.md` remains
  absent; recorded prior owner continue resolution applies to this local audit.
- State: LOCAL UNCOMMITTED; no staging/push/PR/merge/release/hosted CI or actual
  engine/native inventory/device/USB/power/firmware/guest operation. Separate
  BW-BUG-AUDIT-20261015-QUALIFICATION remains NOT RUN for future public candidate.
  Native Windows/ISO/QEMU/firmware/physical reconnect acceptance unperformed.

## BW-BUG-AUDIT-20261016-PASS10 — BLOCKED (four additional bugs fixed; local gates pass; prior attribution pending)

- Date/author:2026-10-16/Codex. Request:another comprehensive audit.
- Repo/worktree/branch:BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; HEAD`35107a8d1a701093eac876a58ab4efd50e291673`.
- Starts with pass8 source/test changes and pass8/pass9 evidence uncommitted;
  preserve all. Acceptance:prove bugs before minimal fixes/regressions,
  independent review, isolated applicable local gates, exact artifact review.
- Scope:fresh bounded source reviews across discovery/authorization,runner/
  recovery and UI/boot/build;primary report/evidence integration and measured
  GTK timing investigation. Run expensive suites sequentially to avoid
  repeating prior uncontrolled performance-test contention.
- Checkpoint:profile5PASS;actualGTK dialogconstructor4–6ms,worker submit<0.5ms
  measured wall/threadCPU/switchcounts. Earlier timing causes remain unattributed.
  Fresh discovery425PASS/0skip; known systemPython setupfailure retained.
- Proven/fixed locally:console inventory overlay hides diagnostic navigation,
  original22cases10FAIL/12controls,fixed107adjacentPASS; one visibility-state
  reset only. Runner fullscan CRstripping upgrades malformed completion banner
  tosuccess above1MiB,primary actualpoll small/large proof2falsepositives;
  original45cases13FAIL/32controls,fixed412adjacentPASS. Scanner now removes
  only terminalLF,preserving recordcontents and existing pass8 changes.
- Third finding fixed:accepted-radio reference and toggle guard restore visible
  choice on refused/exception/timeout/cancelled output changes,before reenabling
  volume/mute; no extra audio request; accepted success updates together,close
  clearsradio/ticket. ActualGTK original10cases8FAIL/2controls;fixed86adjacent
  PASS/final11PASS includingduplicate labels. Primary+independentreview approve.
- Combined exact-starting-source proof:52application module hashes matchpass9
  startingdirtysource;final78regressions32intendedFAIL/46controls,0errors/skips.
  Sharedsource never reverted. Primary initial fixedconsole trace had wrong
  case-sensitive footerliteral; retained and corrected to actualcanonicalcopy.
- Primary integration:98new+old uncommittedregressions PASS(6.24s);54actualfake
  process→runner→evidence→presentation cases PASS across3methods/3languages,
  LF/CRLF/doubleCR andbelow/above1MiB; exacttailhash+unchangedlogbytes checked.
  Final soundprofile5PASS. Initialthree-fix734inputfreeze retained separately.
- Initialthree-fix phases:lint/types/security/shell/format,preview,negative safety,
  pinnedGo1.26.8 uncachedrace/vet/350000fuzz allPASS sequentially. Fullmain
 6300PASS/14expectedimage skips(556.35s),privateOrca1PASS(71.908s),allphaseexit0.
  No auxiliary GUI/pytest/CPU campaigns ranalongside. JUnit6301uniquePASS,
  noerrors/failures/duplicateIDs,all78newcasesPASS;all734frozeninputs match.
  UnchangedGTKsoundtimingcasePASS. Runtimecode digest:
  `2f285ec1640cd4f9912d28d4c355264be072776b9faa854a3123bfa579a27d81`.
- Initialvisualcheckpoint:full-root72DPI fakeGTK capture showedonly
  parentwizard,despite mappedSoundDialog/state assertions. Visualacceptance FAILED;
  thisledtofourthprovenfixbelow. Genericbutton calls action thenrender,
  which explicitly presents/focusesparent; livekiosk startsappwithoutWM.
  Originalblacknative-window capture and correctedrootcapture retained under
  `/tmp/pass10-ui/`. Fourthbug nowproved:11nativeX11cases9intendedFAIL/2controls
  (parentcoversmodalandtakesfocus,closefocusroot,staleepochmodaluntiltick).
  Accessible-only helpers routefocus tovalidmodal,closeobsoletebefore render,
  restoreparentafterdestroy andguardappclose. Initial14+adjacent13=27PASS;
  Additionaldraftclosechildfocus2FAIL/1control proved;restoringcurrentarrival
  fixesit. Final87adjacentPASS including14newcases;independentsourcereview
  approved. Primary14finalcases on58hash-verifiedinitialthree-fixinputs:
  10intendedFAIL/4controls,0errors/skips. Actualroot72DPI repairedscreenshot
  nowvisiblyshowsrestoredSpeakers,failuretext,retry+closecontrols;X11proves
  modalabove+focused andchildstatusfocus. Ownedwindow/workerretired.
  One newcapturehelper usedGdkMonitor synthetic96DPI; retainedfailedassertion,
  correctedtoXserverphysicalscreenquery,72DPI verified;nosourceissue/retryblind.
- Finalfour-fix735inputs frozen;runtimeSHA
  `c0196a53381b5d3235b5f7cdd764d47b5ee074c2f684d18a26bb7c8183e8efcd`.
  Fullfinalmain6314PASS/14expectedimage-onlyskips(518.00s),privateOrca1PASS
  (66.067s),8localphaseexits0. JUnit6315uniquePASS/noerrors/failures/duplicates;
  all92pass10+20pass8casesPASS;unchangedsoundtimingcasePASS. All735hashesmatch.
  DirectindependentXMLcount/sourcepatchhash/indexchecksagree; exactsourcepatch
  and6testmodulesarchivecomparedbyte-for-byte. Initialthree-fixreceipts
  preservedwithinitial-threefix-prefix. NoauxiliaryGUI/testjobsalongside;
  allownedjobsretired. Durableevidenceverified:149exactoriginalartifacts,
  152retainedartifactshashed,735sourcehashes+6testmodulebytesmatch;
  gitindexempty/diffcheckPASS. READMEcontainsresult,proofs,limitsandnextaction.
- Blockers:historical pass8 SIGTERM attribution unavailable;pass9 timing
  variability remains an observation requiring attribution despite measured normal
  profile. Fourfixes local;finalintegrationgates PASS. Exactnextaction:obtain
  platformexecutionaudit/signalprovenance for original06:29UTC SIGTERM and
  attributable failedtimingtrace beforeacceptance/commit/push; no newpassing
  runprovestheircauses. Separate BW-BUG-AUDIT-20261015-QUALIFICATION remains
  NOTRUN;nohosted/ISO/native/physicalqualificationperformedorauthorizedhere.
- State:local only;no commit/push/PR/merge/release. Evidence destination:
  `docs/evidence/bug-audit-20261016-pass10/README.md`.

## BW-BUG-AUDIT-20261016-PASS9 — BLOCKED (final local gates pass; unexplained execution results)

- Date/author:2026-10-16/Codex. Request:another comprehensive bug audit.
- Repo/worktree/branch:BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; HEAD`35107a8d1a701093eac876a58ab4efd50e291673`.
- Result:no new proven defect or source/test edits. Existing pass8 fixes/tests
  preserved local uncommitted. Bounded discovery/safety, runner/recovery and
  UI/boot/build reviewers plus primary export/privacy/diagnostic/receipt review.
- Final gate:main6222PASS/14expected image-only skips(713.76s),privateOrca1PASS
  (118.16s),6223uniquePASS/no failures/errors/duplicate IDs; mandatoryGTK guard
  PASS. Lint/types/security/shell/format,preview,negative safety,Go1.26.8 race/
  vet/350000fuzz PASS. Source/test558frozen hashes match; all4pass8 hashes match.
  Runtime digest`be7d8d674e102743e61984ca60ba63c912c4b514d52dd755f243049f88562d5c`.
- Fresh evidence(overlapping):discovery589uniquePASS+195fake mutation/token
  cases;runner384PASS/41370exact projection comparisons;primary334PASS plus
  expanded export1102PASS/12image skips;202752report API calls/no exceptions.
  Independent original-source runner5FAIL/5controls;diagnostic3FAIL/7controls,
  fixed diagnostic104PASS. UI/boot215PASS;nine actual fake72DPI Tk screenshots.
- Failed auxiliary runs retained:shared AT-SPI missing-socket failure resolved
  by private runtime; sound-dialog click<60ms assertion misses76.45ms(original)
  and137.61ms(private623PASS/1FAIL/7isolated-X11 skips). Concurrent suites/Go
  compilation observed, but CPU causality not established. Exact timing case
  PASS in final full gate; after all jobs retired,private72DPI sound adjacency
  5PASS/0skips in0.70s. No thresholds/assertions/source changed. These passes do
  not explain earlier timings; no new product bug proved. Seven auxiliary
  X11 skips execute in main gate. Initial missing DISPLAY failures retained;
  corrected13operation-identity cases PASS. All failed/unrun evidence separated.
- Remaining acceptance/blockers:explain original pass8 SIGTERM using platform
  execution audit evidence(unavailable here),and auxiliary timing variation.
  Exact next action for timing:measured GTK constructor/show_all/submit wall and
  thread-CPU traces under controlled fake-only execution; no blind gate retry
  or speculative code fix. Acceptance/commit/push remain pending until resolved.
- Durable evidence:`docs/evidence/bug-audit-20261016-pass9/README.md`,raw archive,
  JUnit-derived final-summary.json,source-freeze.json,reviewer reports/scripts/
  transcripts/screenshots. Final diff/artifact review completed; no running jobs.
- State:LOCAL UNCOMMITTED,index empty;no push/PR/merge/deployment/release.
  No actual nwipe/native inventory/device/USB/host/guest action or hosted CI.
  Two lb-config and12manufacturing skips remain unrun; separate ISO/QEMU/native
  Windows/physical qualification item still applies. Shared guide absent; prior
  owner continue instruction remains applicable. This audit is no bug-free proof.

## BW-BUG-AUDIT-20261016-PASS8 — BLOCKED (local fixes verified; termination attribution pending)

- Date/author: 2026-10-16 / Codex. Request: another fresh comprehensive pass.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; clean baseline
  `35107a8d1a701093eac876a58ab4efd50e291673`.
- Scope: three bounded discovery/safety, engine/evidence, UI/boot/build reviews;
  primary independently audits persistence/privacy/report export/diagnostics/
  receipt boundaries, reviews every finding and final integration.
- Acceptance/next action: investigate and prove bugs before minimal edits and
  regression tests; exercise fake-only normal/malformed/permission/duplicate/
  concurrent/cancellation/retry/recovery paths; final applicable local gates,
  complete diff/artifact review; commit/push only after applicable gates pass.
- Proven primary finding: bounded diagnostic elapsed integer overflow and
  injected JSON decoder nesting exhaustion escape documented SafetyError.
  New10cases original3FAIL/7controls; fixed93adjacent PASS;476leaf mutations
  (7valid/469safe refusals) no unhandled exception. Narrow diagnostic_report.py
  catch normalizes OverflowError/RecursionError, without schema/outcome change.
- Runner finding fixed locally: bounded projection appended earlier progress
  after terminal Error Summary, changing explicit I/O advisory to unavailable.
  Original10cases5FAIL/5controls, fixed10PASS. Independent259adjacent/600order/
  6cap/4malformed cases PASS. Author650adjacent/45000completion+5000advisory
  comparisons PASS. Both fixes independently approved, no further finding.
- Parent exact-baseline proof20cases8FAIL/12controls, zero setup errors; fixed20
  PASS. All4frozen hashes match. Diagnostic independent140+109adjacent tests,
  entrypoint/boundary matrices PASS. Preference96regular-file observations PASS.
- Completed gates: lint/types/security/shell/preview/negative and pinnedGo1.26.8
  uncached race/vet/350000fuzz PASS. Replacement frozen-source main gate6222PASS/
  14expected image-only skips in495.62s; separateOrca1PASS64.20s. JUnit confirms
  6223unique passes/no failures/errors/duplicate IDs. Evidence directory:
  docs/evidence/bug-audit-20261016-pass8/. No hosted/platform qualification.
- Fresh checks so far: primary431baseline PASS; discovery542focused PASS plus
  756mutation/retry/concurrency cases, token/argv and900auth matrix PASS; UI654
  PASS and boot316PASS/2expected generated-config skips. Counts overlap.
- Harness history: one initial diagnostic object fixture exceeded16KiB; corrected
  before final original proof (not a product bug). Actual raw deepJSON refusals
  pass on this Python; recursion fault reproduction explicitly injected. Initial
  reviewer DISPLAY/strict fake-read harness issues retained and corrected.
- Full-gate interruption: first final main pytest stopped after5567 printed
  outcomes at06:29:29UTC with wrapper exit143, no main JUnit; privateOrcaPASS.
  Exact owned pytest357214/privateDbus357189 gone. Last-active candidate is
  test_tk_runtime::test_rebuilt_last_chance_rejects_old_erase_callback; code
  uses mocked begin_erase, no termination call. Own-service journal has no
  related lifecycle entries; cause/sender not established. This is NOT a pass.
  Preserve /tmp/beamo-pass8-interrupted-tests.txt and interrupted-orca.xml.
- Focused termination investigation:16neighbor cases,40actual repetitions and
  all311Tk runtime cases PASS under strace, all own pytest processes retired;
  no signal-send syscalls or delivered SIGTERM. Exact-source hashes unchanged.
  These results do not establish the original sender/cause. Owner answered on
  2026-10-16: "No, not knowingly" to stopping/canceling around06:29UTC. This
  does not identify the sender. Source fixes stay local until the unexplained
  result is resolved.
- Final replacement gate exited0; wrapper signal trace records normal exit.
  All four source/test hashes still match the frozen tested bytes. Final local
  diff/artifact review performed; regression source and safe boundaries preserved.
  Replacement success does not identify the first execution's SIGTERM sender.
- Blocker/remaining acceptance: attribute original06:29:29UTC exit143 using
  owner/platform cancellation or execution audit evidence; the user requires
  unexplained results resolved before completion. Owner did not knowingly
  cancel. No callable platform execution-audit tool is exposed; local kernel/
  audit-log/cgroup memory-event files are absent. Attribution requires platform
  execution audit evidence unavailable here. No further blind retry is needed.
- Exact next action: obtain cancellation/termination attribution; then reconcile
  evidence and recheck source hashes/current checkout. If no source/config change
  and all acceptance criteria satisfied, commit the four explicit implementation/
  test paths with safety: prefix; record actual SHA, commit evidence separately,
  and push only after checking automatic triggers. Do not release.
- State: both fixes/tests/evidence remain LOCAL UNCOMMITTED; index empty;
  HEAD35107a8d1a701093eac876a58ab4efd50e291673. No PASS8 push/merge/release.
  Durable evidence docs/evidence/bug-audit-20261016-pass8/README.md and
  final-summary.json; exact raw transcripts archived with checksums there.
  Separate ISO/native/physical candidate qualification remains NOT RUN.
- Limits: no actual nwipe/native inventory/disk/USB/guest/host action, ISO/QEMU,
  hosted CI/PR/publication. Separate candidate qualification remains unrun.

## BW-BUG-AUDIT-20261016-PASS7 — DONE (local acceptance and source push)

- Date/author: 2026-10-16 / Codex. Request: another fresh comprehensive pass.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; baseline
  `f102dfbe5a705fda10880fecc24626c7693c10f0`; implementation
  `de55b078514e2028a2a22633f1d7aa2941f9e0b6`, safety-prefixed commit pushed to origin.
- Outcome: fixed unchanged padded model/serial/WWN blocking report export, and
  verification receipts accepting mismatched skip/xfail kind counts. Only
  harmless hardware padding is normalized before existing strict validation;
  original safe Unicode model-to-generic-receipt behavior preserved. Paths,
  UUIDs, controls, protected identity and receipt schema/gates stay intact.
- Proof:75 new cases produce36 intended failures/39 passing controls, zero
  setup errors, on isolated exact baseline; corrected75 PASS. Original checkout
  never reverted; existing tests unchanged. All4 frozen hashes match committed
  source/test bytes. Runtime source digest
  `ff52fe2414436c9bec18cee235ee8a104fe16f567f7cd4237dabe62dcbdc0d42`.
- Final local gate: main6202PASS/14expected image-only skips (476.19s), private
  Orca1PASS =6203 unique passes; no failures/errors/duplicate IDs. Mandatory GTK
  result guardPASS. Corrected-source lint/types/security/shell/developer-format,
  preview, private negative mutation, pinned Go1.26.8 uncached race/vet/350000fuzz
  PASS. All skip reasons retained:2generated lb-config and12manufacturing ISO.
- Independent coverage: discovery648tests/454controlled sequence+retry/
  160concurrent observations; engine699tests/21600 completion projection cases/
  24readiness controls; corrected export731adjacent/1120helper-equivalence/
  240boundary cases, primary27controller roundtrips+27changed-scan refusals;
  receipt59adjacent/2268kind-count combinations. UI1359unique passes,
  build487PASS/2expectedskips; reviewer union1862PASS/2skips. Navigation54000
  events+54countdown detours;40concurrentfake sessions; primary5760malformed
  rendering/sharing calls with no unhandled exceptions. Overlaps not summed.
  Actual ./preview72DPI inspected by reviewer and primary; owned process retired.
- Draft history retained: first full integration2FAIL/6200PASS/14expected skips,
  private OrcaPASS. Discovery-parser reuse broke unchanged Unicode receipt
  contract. Focused2FAIL/3PASS proved it; narrow hardware-padding fix preserves
  original parser/display behavior. Existing tests unchanged; corrected80focused
  PASS and expanded independent sweep above. Earlier narrow reviewer approval
  superseded. Final replacement full frozen-source gate PASS as measured above.
- Setup history: initial reviewer DISPLAY/Chromium-PATH failures/skips resolved
  by private72DPI complete replacements/browser-case reruns; originals retained.
  Initial permission harness allowed predecessor read-only mount/cmdline probes;
  corrected fully fake harness reran PASS. Primary controller harness initially
  lacked preview mode; live tmpfs guard refused regular-file evidence directory
  before write; corrected explicit fake mode PASS, guard unchanged. No native
  lsblk inventory, actual nwipe, device/USB write, guest or host power action.
- Evidence: docs/evidence/bug-audit-20261016-pass7/README.md retains original and
  fixed proofs, failed draft gate, final raw logs/JUnit-derived skip list,
  independent matrices/scripts/reviews, screenshot, hashes and content manifest.
  A duplicate-skip suspicion was rejected with a real pytest call+teardown trace;
  duplicate outcome IDs are intentionally preserved, not silently deduplicated.
- State/remaining acceptance: no local audit blocker or further reproducible
  actionable finding remains in reviewed scope. Source pushed; no open PR,
  hosted run, merge/deployment/release. Documentation accompanies source; only
  docs changed after tested source freeze. Local acceptance is not a bug-free
  guarantee. No next action for this local pass; a selected public candidate
  needs separate exact-source ISO/QEMU/native/physical qualification below.
- Authorization: fake targets/process boundaries and ordinary temporary files
  only. No hosted/ISO/QEMU/native-platform/physical acceptance or publication
  authorized here. Current Blacksmith guidance applies, not legacy Cloud Build.
  Missing shared guide remains resolved by prior owner continue direction.

## BW-BUG-AUDIT-20261016-PASS6 — DONE (local acceptance and source push)

- Date/author: 2026-10-16 / Codex.
- Request: another fresh thorough comprehensive audit; prior evidence was
  baseline history, not proof for this pass. Three bounded reviewers rotated
  discovery/safety, persistence/report/privacy, UI/boot/build ownership; primary
  independently reviewed runner/progress/evidence and all fixes/original proofs.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; baseline
  `6bf8c54ce6b25dd21f8be730f705a54c2c8c3ff8`; implementation
  `ac6ed67c496090c26a9520d0244100ca371ce192`, committed with safety prefix and pushed to origin.
- Fixed: model-LF spoofed readiness could trigger premature SIGUSR1; sharing
  identifier/control collisions and UI-language restarts could corrupt valid
  results; malformed nested dictionary keys leaked private identifiers; later
  identifiers could re-redact inserted placeholders. Full timestamped readiness,
  validated machine controls/canonical presentation, scalar-only sharing leaves
  and single-pass escaped substitution fix these without touching original data.
  Method and verification prose keep intended redactions; outcomes parser strict.
- Proof/evidence: docs/evidence/bug-audit-20261016-pass6/README.md retains exact
  original/fixed cases, final logs/JUnit-derived skip list, reviews, matrices and
  scripts, preview screenshot, hashes and unsuccessful draft history. New180
  cases yield120 intended failures/60 controls on exact baseline; fixed180 PASS.
- Final local gate: main6127 PASS/14 expected image-only skips plus private
  Orca1 PASS =6128 unique passes; no errors/failures/duplicates. Mandatory GTK
  guard PASS. Lint/types/security/shell/preview/negative and pinned Go1.26.8
  uncached race/vet/350000 fuzz PASS. All9 tested hashes match committed bytes.
- Independent coverage: discovery415 +364 controlled cases; runner213/1176
  matrix plus189 primary; privacy482 adjacent/305 independent and1408 malformed
  core/118 nested-container/330 multisecret cases; UI955+358adjacent/242build
  and20000 navigation events, with2 generated lb-config skips classified.
  Overlapping counts are not summed as unique passes. Actual ./preview at72DPI
  inspected by reviewer and primary, owned subprocesses retired.
- Draft history: first complete integration FAILED1/6089pass/14skips because
  approved draft restored too much method prose. Existing pass37 test stayed
  unchanged. Method/scope redaction restored; collision tests check semantic
  controls and valid redacted prose. Cross-review then proved pre-existing
  placeholder re-scrubbing (24fail/12controls), fixed single-pass. Early
  replacement intentionally stopped on owned PID269626; missing-JUnit failure
  superseded, not a pass. Final replacement full frozen-source gate PASS above.
- Result/state: no further reproducible actionable local defect or blocker
  remains in reviewed scope. Source branch pushed; no open PR, hosted run,
  merge/deployment/release. Only evidence/handoff documentation changed after
  implementation; these artifacts accompany source. This is not proof of no bugs.
- Remaining acceptance/next action: none for local audit. A selected public
  candidate needs the separate exact-source ISO/QEMU/native/physical
  qualification item below; no guest/hosted/physical/publication authority here.
- Safety: fake targets/process boundaries, ordinary temporary files and private
  72-DPI sessions only. No real nwipe/device operation/guest/native inventory;
  current Blacksmith guidance applies, not legacy Cloud Build. Shared-guide
  absence remains resolved by prior owner continue direction. Logs /tmp/beamo-pass6-*.

## BW-BUG-AUDIT-20261015-PASS5 — DONE (local acceptance and source push)

- Date/author: 2026-10-15–16 / Codex.
- Request: another thorough and comprehensive pass after the completed
  continuous audit; prior passing evidence is baseline history, not new proof.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; clean baseline
  `604e72b3ae1fe1a2abdda08200b8f271cb5c675d` (implementation `af2b6e9`).
- Scope/acceptance: fresh source review of discovery/identity/authorization,
  runner/argv/progress/log/completion/cancel/retry, wizard/Tk/GTK/console/app,
  recovery/report/export/diagnostics and boot/build/compatibility. Prove any
  suspected defect before a minimal regression-backed fix; independent review;
  final frozen-source full local gates and artifact/diff inspection.
- Progress: read current guide/record and verified clean source. Three bounded
  reviewers resumed with rotated scopes; primary owns persistence/export/
  diagnostic integration and final independent verification.
- Proven findings this pass: falsey malformed `children` values accepted as
  empty topology (original regression fails; minimal fix now frozen);
  malformed findmnt bracket suffix trusted as a different source; embedded
  model newlines forging positive hidden-capacity/error-summary checks; stale
  import-time startup translations and hardcoded GTK status. Each reviewer
  saved a failing fake/isolated-label proof before authorized source edits.
- Additional proven fix: report mount cleanup skipped owned directory removal/
  descriptor close after lock-close or unmount I/O errors, and worker child
  close EIO skipped parent close. Original fake-only proofs fail3 cases;4
  regressions/controls now pass with independently reviewed nested-finally fixes.
- Final local acceptance PASS:59 new cases, exact-original38 intended failures/
 21 controls and fixed59 passes. Main5947 pass/14 expected image skips plus
  private Orca1 pass =5948 unique passes, no errors/failures or duplicate case
  IDs. Lint/types/security/shell/preview/negative and refreshed Go1.26.8
  uncached race/vet/350000 fuzz executions PASS. All20 frozen hashes match.
- Integration history:2 preliminary runs deliberately interrupted on exact
  owned pytest PIDs for final proven source variants; later integration run
  completed3 failed/5944 passed/14 skips from1 remaining short positive-header
  fixture and2 GTK tests selecting an unrelated global window. Original
  assertions retained; fixture corrections pass12 parser/60 ordered UI cases;
  replacement full frozen-source gate PASS above. Superseded runs are not passes.
- Evidence checkpoint: docs/evidence/bug-audit-20261015-pass5/README.md contains
  original proof, fixed cases, reviews, complete final logs, hashes and exact
  image skip reasons. Independent sweeps394 discovery,499 runner,1176 matrix,
 1203 UI plus31 resolved setup skips,380 parent persistence; overlapping counts.
- Source state: implementation `cdfe9fac6238c8fd3d867c9ef48c4ca3248facce` committed with safety prefix and
  pushed to origin after all applicable local gates passed. All20 frozen
  source/test hashes match committed bytes. No open PR or branch hosted run;
  no merge/deployment/release. Evidence/handoff are the only subsequent edits.
- Result: fresh bounded reviews and final complete local gate found no further
  reproducible actionable defect in authorized local scope. Local acceptance
  criteria passed; this is not an absolute proof of no bugs or image/hardware
  qualification. No unresolved local implementation blocker remains.
- Exact next action: no further local implementation fix required. Review the
  source/evidence if desired; any selected public candidate must follow the
  separate qualification item below. No PR/hosted run/release is part of this task.
- Constraints: fake fixtures only, isolated72-DPI Xvfb, no host/physical device
  operation, guest, hosted CI, PR, production publication or release. Current
  Blacksmith/project guidance applies; shared-guide absence remains resolved
  by prior owner continue direction. Image/native/physical qualification stays
  in the separate existing item below. Logs use `/tmp/beamo-pass5-*`; retain
  final evidence in repository before completion.

## BW-BUG-AUDIT-20261015-CONTINUOUS — DONE (local acceptance and source push)

- Date/author: 2026-10-15 / Codex.
- Request/goal: repeat comprehensive audit/fix passes until a fresh whole pass
  finds no further reproducible actionable defect in authorized safe local
  scope. Acceptance achieved after fixes, independent reviews, fresh source/
  fixture/matrix/actual-Tk checks and the final complete local gates. This is
  not an absolute proof of no bugs or image/hardware acceptance.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`. Baseline `20ae39a556ab961baf204e3108e6ebc93b695ac5`;
  implementation `af2b6e9c3d053b65e666d807a87207db14521cb2`, pushed to origin.
- Result/evidence: `docs/evidence/bug-audit-20261015-continuous/README.md` with
  exact-original failures, fixed regression transcript, final full gate logs,
  source/test hashes, independent review summaries, reproducible mutation/
  exploration scripts, and actual picker before/after screenshots. Evidence
  and this complete local handoff are retained alongside the implementation;
  final remote HEAD verification confirms their subsequent documentation push.
- Seven verified finding groups fixed: mounted aliases lost through malformed/
  hidden/type/flat-ancestry filtering; unrelated empty readers blocking recovery
  journals; diagnostic-directory substitution; completion overriding method
  counter contradictions; float-rounded malformed percentages falsely completing;
  stale concurrent runner telemetry publication; Tk comparison title mid-word
  wrapping. No method/argv/confirmation/claim/version/surface-boundary relaxation.
- Proof before fixes: private exact-baseline import tree yields67 intended
  failures /34 normal controls across101 new cases; fixed101 pass. Original
  checkout was never reverted or mutated. Every source change has a regression.
- Draft history retained: mounted-root draft missed hidden/flat observations and
  false loop/ram types; extra failing proofs drove effective mount reconciliation.
  Counter draft omitted syncing/retrying/blanking and was corrected after9
  failures against pinned engine semantics. An actual72-DPI fullscreen preview
  exposed the title bug after an early full run started;9 original layout cases
  failed, then passed after the one-line fill-X fix. That obsolete full run was
  deliberately interrupted on its exact owned pytest PID; its missing-JUnit
  failure is not a passing gate. Replacement final run passed after all changes.
- Final local gates: main pytest5,888 pass /14 image-only skips, private Orca1
  pass; combined5,889 unique passes, zero failures/errors. Mandatory GTK result
  guard passes. Lint/types/security/shell/developer-format, preview web/console/
  helper/JS, negative mutation, pinned Go1.26.8 uncached race/vet and350,000 parser
  fuzz executions pass. All12 changed source/test hashes match frozen and
  committed bytes. No source/tests changed after final freeze.
- Fresh no-new-findings evidence: discovery132-case graph matrix; runner1,176-
  case completion matrix and595-test sweep; recovery/report/diagnostics/export
 331-test sweep; primary100 fake wizard sessions/30,000 public actions/10 explicit
  fake starts preserved safety invariants;185 boot/build/compatibility cases.
  All4 isolated Tk startup cases passed. These overlap full tests; do not sum.
- Independent approvals: discovery/recovery216 cases; recovery/diagnostics88;
  final runner242 plus27 cancel/retry cases on hash2979312e...; final Tk UI524
  unique cases across main and supplementary runs (all11 initial dependency/
  isolated-X11 skips resolved). Reviewer summaries are labeled as summaries,
  not fabricated raw terminal transcripts. All temporary fixtures were fake.
- Resolved exploratory setup history: initial wizard harness keyword typo was
  corrected; two baseline fullscreen cases initially lacked isolated-X11 opt-in
  and later ran/passed. Expected missing-fake-device rdev notices are not live
  identity evidence. Existing TODO-regex warning/mypy notes are informational.
- Limits/current publication state: source branch pushed, unmerged, unreleased.
  No hosted CI/PR/ISO/guest/physical-device operation performed. T3 status/open
  worked but snapshot client errored again; no manual web inspection claimed.
  Repository browser regressions and actual Tk navigation passed separately.
  Owned preview HTTP server and Tk/Xvfb sessions were retired. Go native
  inventory override unset; this is not native Windows/hardware qualification.
- Remaining local acceptance/blockers: none. Exact next action, only for a
  selected public candidate, is the existing separate qualification item below.
  Report export can conservatively refuse unidentified/zero-capacity optional
  inventory; large-log recovery can remain indeterminate without retained
  completion evidence. These fail-closed limits are documented, not relaxed.
  Missing shared guide remains resolved by prior owner continue direction.

## BW-BUG-AUDIT-20261015-PASS2 — DONE (local fixes verified and pushed)

- Date/author: 2026-10-15 / Codex.
- Request: another thorough, comprehensive bug audit and regression pass.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`. Baseline `8a5dced72b044f22b8dee168f76a2ea882083124`;
  implementation `57ead7e4304f7f373a0c862ff36335c949f4cf7a`, pushed to origin.
- Result/evidence: `docs/evidence/bug-audit-20261015-pass2/README.md` is the
  durable report, with original failures, fixed regressions, final transcripts,
  19-file source/test SHA-256 manifest, independent descriptor review and a Tk
  preview screenshot. Committed bytes match final tested bytes.
- Completed scope: three bounded reviewers revisited discovery/identity,
  runner/progress/log/evidence/cancel/retry, recovery/reporting and boot/build.
  Primary reviewed wizard state/confirmation/stop/retry/shutdown, language/UI,
  packaging boundaries, independently proved every finding and reviewed all
  changes. Fake devices/process boundaries/files/firmware only.
- Fixed seven finding groups: retired recovery-directory ownership, obsolete
  report preference snapshots/destinations, lock replacement before exec,
  substituted/reused log inode evidence, delayed-start overwriting ambiguous
  ownership, missing translated uncertainty warnings, English-only inventory
  counts. Added 71 regression/lifecycle cases; existing fixtures retain their
  assertions and now retire actual regular-log descriptors.
- Proof: baseline-compatible regressions on a private exact-original import
  tree produce 44 intended failures / 19 passing controls; all 71 new fixed
  tests pass. Original checkout was never reverted or mutated for proof.
- Review history: an intermediate dev/inode-only log fix was rejected after
  immediate inode reuse falsely completed. Retained-FD protection resisted
  1,000 unlink/recreates, refused replacement evidence and retired the handle.
  A draft transfer leak was proved and fixed. Independent approval: 76 tests
  with zero surviving temporary-file descriptors, plus 20 adjacent cases.
- Final applicable local gates PASSED: main pytest 5,787 pass / 14 image-only
  skips; private Orca 1 pass; combined 5,788 pass, no failures. Mandatory GTK
  result guard passes. Lint/types/security/shell/format, web/console/helper/JS
  preview, negative mutation, Go 1.26.8 race/vet and 350,000 firmware-parser fuzz
  executions pass. Native inventory override unset. Frozen hashes rechecked
  after the full gate and against the committed tree; all 19 match.
- Focused overlapping evidence: 56 baseline, 273 wizard, 108 inventory/language,
  222 discovery/safety, 812 recovery/report/boot, and 494 affected runner cases
  pass. The initial display-less recovery GTK failure is historical, not a pass;
  corrected runs use private 72-DPI D-Bus/Xvfb. Actual `./preview` welcome screen
  inspected at 72 DPI with no clipping. T3 web snapshot client is unavailable;
  existing browser regression tests passed separately, no interactive web
  inspection claimed. Owned preview HTTP server was positively identified/stopped.
- Current state/remaining criteria: local audit acceptance complete; no local
  blocker. No PR, hosted CI, ISO, guest, device operation, deployment or release.
  Exact next action for a public candidate is the separate qualification item
  below. Do not infer release authority from this record. Shared-guide absence
  remains resolved by the owner's earlier continue instruction.
- Conservative behavior retained: large-log recovery can become indeterminate
  if an early completion marker lies outside authenticated retained suffix
  evidence. Recorded in the report; no false success or schema expansion.

## BW-BUG-AUDIT-20261015 — DONE (local source fixes verified and pushed)

- Date/author: 2026-10-15 / Codex.
- Resolution: owner instructed Codex to address the issue and continue on
  2026-10-15. Proceed under current project AGENTS.md without the unavailable
  shared guide; do not invent its contents. Initial stop is retained below
  as history, not an active blocker. Three bounded audit subagents started.
- Baseline history: system `python3 -m pytest` exited 1 because pytest was
  absent. Resolved with the documented `.venv-linux` development environment.
- Request: systematic bug audit and minimal proven fixes across wizard,
  discovery/classification/exclusion, command construction, progress,
  cancellation, completion verification, logs, boot, hardware compatibility,
  build pipeline and recovery. Use bounded subagents; independently validate
  results. Prove each bug before changing code; add regression tests.
- Repository: BeamoTech/beamo-wipe; worktree `/root/dev/Beamo Wipe`;
  branch `fix/safety-audit-20261015` (started from `main`);
  baseline `cad8ed397818bca09634be57cd8a46e0195690c2`;
  implementation `ff0a3da08e56c3fb38941be20e42db9553269f32`, pushed to origin.
- Completed: read current `AGENTS.md`, memory index, `pyproject.toml` and
  `scripts/test-all.sh`; confirmed initially clean checkout. Searched tracked
  and hidden workspace paths for an existing unfinished-work/backlog record;
  none found, so this is the canonical record.
- Resolved initial blocker/evidence: `AGENTS.md` requires reading `~/dev/AGENTS.md`;
  `cat /root/dev/AGENTS.md` reports “No such file or directory” and
  `test -e /root/dev/AGENTS.md` exits 1. Shared checkout, cost, documentation
  and storage instructions are therefore unavailable. Current request says
  “Stop on any blocker.” At that initial stop, no implementation or delegated
  audit had started; the owner's subsequent continue instruction resolved it.
- Local acceptance completed: read applicable current instructions and relevant
  architecture/operations guidance; establish baseline; complete bounded
  reviews; reproduce suspected defects with failing tests or concrete traces;
  make minimal fixes; independently verify regressions and adjacent paths;
  run applicable full local gates and preview checks; inspect final diff.
  Commit/push occurred only after all applicable local gates passed and automatic
  CI trigger constraints were checked. No release is authorized.
- Current progress (2026-10-15): bounded reviews completed across discovery,
  safety/methods, runner/progress/evidence, wizard transitions and shutdown,
  recovery/report export, live boot/kiosk, compatibility and build scripts.
  Discovery/safety review found no new proven defect (439 focused tests passed).
- Proven fixes, committed and pushed:
  - `progress.py`, French/German tables: nwipe SIGUSR1 reports job-wide
    `round_percent`, incorrectly labeled as a within-step percentage; secondary
    text also showed 100% before completion evidence. Labels now say overall
    and clamp telemetry to 99% until completion. Pinned upstream signal handler
    checked at https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/nwipe.c#L1350.
    Final review also proved headline/step percentages diverged during the
    five-second throttle or raw regressions. `wizard.py` now shares the displayed
    monotonic job percentage; two actual-runner fake-log regressions cover it.
  - `session_recovery.py`: lock pathname replacement left ownership/cached
    quiescence attached to obsolete inodes. Validate named inode after flock
    and before cached-quiescence/journal writes; fail closed on replacement.
  - `nwipe_runner.py`: same replacement race at wipe-lock acquisition; verify
    named inode after flock and release descriptor on refusal. Final review
    also proved an unpublished descriptor leak on KeyboardInterrupt during
    acquisition. Cleanup now catches BaseException; 66 adjacent tests passed.
  - `engine_checks.py`: incomplete final records falsely passed hidden-storage
    or I/O checks. Incomplete logs cannot produce passing parsed checks;
    explicit failures/warnings remain.
- Independent reproduction: private original-source snapshot from HEAD plus
  the four new regression modules produced **14 failures / 4 passing normal
  controls**, exit 1, in `/tmp/beamo-audit-original-repro.txt`. No mutation of
  shared source was needed to reprove the original defects. All **18** pass
  on the fixed source (`/tmp/beamo-audit-regressions-final.txt`). Independent
  progress review passed 135 tests and 36 en/fr/de boundary/staleness cases.
- Completed checks: 294 wizard confirmation/refresh/stop/retry/shutdown tests;
  177 independent changed/adjacent tests; source/tests Ruff and mypy (52 files)
  pass; web/console/helper previews generated; 3 embedded-JS syntax tests pass.
  Subagent recovery audit: 797 passed / 8 GTK dependency skips before exposing
  system GTK to the venv. Subagent runner audit: 182 runner/progress/completion
  tests and 65 security/cancellation tests passed.
- Environment diagnostics: original full-suite attempt interrupted after
  1102 passed / 18 failed / 13 skipped. Failures traced to fixture shebangs
  containing the spaced venv path and subprocess Python lacking pytest.
  Use `/tmp/beamo-wipe-audit-python` (symlink to `.venv-linux`) on PATH;
  venv now exposes installed system GTK. All 28 affected CI-fixture tests
  pass after environment correction. This interrupted run is not a gate pass.
- Intermediate direct test-all runs were interrupted after the final
  cancellation cleanup change and then an accessibility-bus failure. The
  AT-SPI quick-zero external-client test passes alone (1 passed); a combined
  run's registry tried the removed `/run/user/0/at-spi/bus` socket after speech
  testing. Do not count these interrupted runs as passes. Use the repository's
  existing private runtime/session separation rather than changing tests.
- Passed final gate: `PATH=/tmp/beamo-wipe-audit-python/bin:$PATH
  BEAMO_GATE_CHILD=1 BEAMO_GATE_JUNIT=/tmp/beamo-audit-final.xml
  ./scripts/ci-hosted.sh tests`; output `/tmp/beamo-audit-final.txt` and
  JUnit `/tmp/beamo-audit-final.xml{,.orca.xml}`. This runs locally, skips only
  dependency installation, uses existing dependencies, and does not dispatch CI.
  Local lint, preview and private safety-negative phases passed. Lint's
  existing TODO warning matches the literal placeholder-detection regex in
  unchanged `release_manifest.py:40`, not an untracked task or source warning.
- Complete-run diagnostic: pytest 9.1.1 produced 5668 passed / 58 skipped /
  2 failures in missing-GTK import simulation; its importlib-based importorskip
  bypasses that simulation's builtin-import hook. Installed repository-pinned
  pytest 9.0.3; all 15 GTK dependency-boundary tests then passed unchanged.
  Installed prescribed Playwright 1.63.0/Chromium and QR decoder for broader
  local coverage; dependency preflight passed 33 tests. The full gate passed
  with these dependencies. No source/test assertions weakened for setup errors.
- Final results: full pytest 5694 passed / 36 skipped, plus one passed Orca test;
  Go 1.26.8 launcher supplement 23 passed, resolving 22 skips (one overlapping
  bootstrap test). Combined **5717 unique passed / 14 image-dependent skipped**;
  no failures. Mandatory GTK guard, lint/types, preview, safety mutation,
  Linux Go race tests and vet all passed. Native inventory override stayed unset.
- Durable evidence retained under
  `docs/evidence/bug-audit-20261015/README.md` with original reproduction,
  fixed regressions, source/test SHA-256 manifest and local gate transcripts.
- Browser limit: T3 preview initialized, but navigation/snapshot automation
  failed repeatedly; no successful visual browser inspection claimed.
- Exact next action: review the pushed source commit and retained evidence.
  No further local implementation fix is pending. Selecting a public candidate
  requires the separate image/native qualification item below. No PR was
  opened; GitHub branch run query returned no runs after the source push.
- Safety: fake devices only for local work; ISO/QEMU requires an authorized
  isolated worker. Physical-device operations remain prohibited by current
  project instructions. Follow current Blacksmith guidance, not historical
  Cloud Build/publisher instructions in the task baseline.
- Source/publish state: implementation/tests committed and pushed on the stated
  branch. This documentation records the verification after that push. No PR,
  merge, deployment or release occurred.

## BW-BUG-AUDIT-20261015-QUALIFICATION — NOT RUN (future public candidate)

- Date/author: 2026-10-15 / Codex.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; latest implementation
  `de55b078514e2028a2a22633f1d7aa2941f9e0b6` (prior audit implementations
  `ac6ed67c496090c26a9520d0244100ca371ce192`,
  `cdfe9fac6238c8fd3d867c9ef48c4ca3248facce`,
  `af2b6e9c3d053b65e666d807a87207db14521cb2`,
  `57ead7e4304f7f373a0c862ff36335c949f4cf7a` and
  `ff0a3da08e56c3fb38941be20e42db9553269f32` retained as history).
- Remaining acceptance: final-public-candidate exact-source Blacksmith ISO/QEMU
  and native Windows gates, plus applicable physical firmware/media acceptance.
  The 14 local skips need generated live-build config/manufacturing ISO bytes.
- Exact next action: when the owner selects a public candidate, qualify its
  exact final source through current Blacksmith guidance in `docs/ci.md` and
  retain all source/image receipts. Do not use legacy Cloud Build instructions.
- Blockers/approval: no public release authorized; no local guest authorized.
  Physical acceptance is blocked by unattended-host rules and needs the
  separately specified safe physical session. Local passing tests do not
  replace these gates. T3 interactive browser automation also remained unavailable;
  repository browser regressions passed, which is distinct evidence.
- Publication state: **NOT TESTED / NOT DEPLOYED** for ISO/QEMU/native Windows/
  physical acceptance. No hosted dispatch or publication performed.

## BW-READINESS-WORK-20261026 — LOCAL COMMITS VERIFIED / RELEASE GATES OPEN

- 2026-10-26 / Claude (Opus 5.5) for the owner's request to save everything
  that cannot be done here and complete the rest. Follows the readiness review
  BW-READINESS-REVIEW-20261026. Repo BeamoTech/beamo-wipe, branch
  `fix/release-readiness-20261026` from main `58c677f` (product bytes = tag
  v0.2.14 `9764d93`). Owned shared-object sparse clone (docs/evidence omitted)
  `C:/Users/Jack/dev/BeamoTech/beamo-wipe-readiness-20261026`. Peer dirty work
  in the main checkout and PR93 untouched. State: committed locally; pushed only
  as a branch if noted below. No PR, no hosted CI, no tag, no release.
- Test environment: existing WSL distro (no /mnt/c by design) with owned copies
  `/home/beamo-qual/beamo-wipe-readiness-20261026` (work), `-red` (original
  runner), `-base` (pristine main archive), helpers
  `/home/beamo-qual/bwrt-readiness-20261026.sh` (private userns + tmpfs /tmp)
  and `bwrtx-...sh` (adds private 72 DPI Xvfb + D-Bus). Pre-existing environment
  failures reproduced identically on `-base`: tests needing `.git`
  (git rev-parse), tests reading docs/evidence, test_compat_story helper copy,
  ci_evidence gate runner, GTK sound-dialog layout under WSLg.

### Completed and verified locally (commit: evidence)

- `8872929` safety: runner holds a read-only, non-exclusive, CLOEXEC handle to
  the confirmed disk from before the final rediscovery until nwipe exits, so the
  kernel cannot hand its name to a swapped disk (nwipe 0.42 opens by name after
  scan/PRNG benchmark; verified its open flags have no O_EXCL). 15 new tests
  PASS; end-to-end case FAILS on the original runner (no handle at launch).
  176 runner-related modules rerun; only environment failures remain.
- `3ee29ed` image: troubleshoot entry = nomodeset safe video without
  memtest/noapic/nolapic/nosmp; GRUB Utilities submenu --unrestricted;
  ctrl-alt-del.target masked + CtrlAltDelBurstAction=none; kernel.sysrq=0;
  QEMU squashfs checks + new bios/uefi-troubleshoot-usb boot probes
  (BEAMO_WIPE_SAFE_VIDEO=1) + publisher inventory. Source tests PASS; ruff 0.9.2,
  mypy 2.1.0 (52 modules), shellcheck PASS. NEW QEMU PROBES/CHECKS UNRUN until
  the hosted KVM gate.
- `eaed93d` GPL: SOURCE.txt is a written offer (3 years, cost-only, via support
  URL); scripts/corresponding_source.py plans/fetches exact Debian sources from
  snapshot.debian.org + nwipe/Beamo tarballs with hash checks; THIRD_PARTY.md
  procedure + trademark/non-affiliation. Tests PASS (in-memory opener only).
- `6e149d8` docs: Secure Boot wording, boot card (helper order, Lenovo/Acer/
  Secured-core, SmartScreen, real screen order), SECURITY.md (private advisory,
  supported versions, no numeric SLA), boot-exclusion-signals refresh, claims
  (FAT32 second stick, SSD overwrite-only, no competitor comparison), version-
  neutral ci/release docs, BeamoTech URLs incl. helper EN/FR/DE.
- `ddf9b92` scripts/rescan_release_packages.py (published-release Debian
  security rescan). Ran 2026-10-26 on public v0.2.13 manifest sha256
  0f2796dc0cedd3e34c4a81e233b12c4662a6eb91a6b5aca7b54370d4afe85640 (matches
  sidecar; signature not checked in this informational run): 11 fixed issues
  missing in openssl 3.0.22-1~deb12u1, expat 2.5.0-1+deb12u4, brotli 1.0.9-2.
  Output in WSL `/home/beamo-qual/beamo-wipe-readiness-20261026-rescan/`.
- Further commits for copy changes and the manufacturing SOP/readback tool are
  listed in the checkpoint at the end of this entry.

### Cannot be done here — open items (ID, acceptance, next action, blocker)

- BW-RR-PHYS — BLOCKED (hardware; remote-only host). Run the Tier 3 matrix in
  docs/evidence/physical-acceptance-111 on dedicated hardware with the exact
  release image: BIOS, UEFI SB off/on with inspected db/dbx, vendor boot keys,
  troubleshoot (nomodeset) entry on real AMD/Intel/NVIDIA graphics, speech on
  real audio, USB2/3/C ports, lid/power, real erase of DISPOSABLE SATA and NVMe
  disks, boot-USB exclusion with a writable stick. Also a novice usability test
  with non-technical participants. Next: owner provides lab hardware/people.
- BW-RR-LEGAL — OWNER/COUNSEL. Review SOURCE.txt offer wording and 3-year
  retention; NOTICE "no warranty" for a paid consumer product (US/EU/UK) and
  whether an in-app terms/disclaimer screen is required before erasing; privacy
  policy for support/report data; "not a Blancco replacement" in README/NOTICE
  and the claims.md competitor rule; Debian trademark statement. No in-app
  legal screen was added without approved text.
- BW-RR-RELEASE — BLOCKED on PR93 + authority. v0.2.13 (latest) lacks the
  0.2.14 safety fixes and the 11 Debian fixes above; v0.2.14 cannot publish
  because check-release-ready.sh needs tag == main HEAD (now 58c677f). Next:
  resolve PR93's GTK segfault (peer-owned, run 40433850969), open a PR for this
  branch (triggers the hosted CI gate — owner authorization), merge, bump to
  0.2.15, tag at main HEAD, wait for exact-main push CI, dispatch release.yml,
  verify public bytes. Retain every gate; no bypass.
- BW-RR-GPL-ARCHIVE — OPEN. Produce and privately retain (with readback) the
  corresponding-source archive for v0.2.13 and every later release using
  scripts/corresponding_source.py. Blocked: several GB free space (C: ~1 GB)
  and an authorized private destination. Deciding whether release.yml should
  run it is an automation change needing owner authority.
- BW-RR-FIRMWARE — OWNER DECISION + ISO QUALIFICATION. Image ships no firmware
  (--firmware-* false, main only): amdgpu, Intel SOF audio, microcode absent.
  Decide on non-free-firmware packages (license review, size, THIRD_PARTY),
  then hosted ISO/QEMU and physical display/audio tests.
- BW-RR-TRIXIE — PLAN. Bookworm regular security support ended 2026-06; LTS to
  ~2028-06. Migrate to Debian 13 (kernel 6.12, Python 3.13, Tk/GTK requal) on an
  isolated build worker with full gates; new base digest pin.
- BW-RR-SHIM — MONITOR. Shipped shim 16.1 is signed only by Microsoft UEFI CA
  2011; firmware trusting only the 2023 CA (or a future revocation) will refuse
  it. Adopt a 2023-CA-signed Debian shim when available; repeat the Q12
  component inspection for the next release image (none exists for 0.2.14).
- BW-RR-SIGNING / BW-RR-ENV — OWNER. Move the Ed25519 release key from
  exportable Secret Manager to non-exportable KMS/HSM or offline custody with a
  backup; publish its fingerprint on an independent channel (support site).
  `production` environment has no required reviewer and admins can bypass;
  sole-maintainer policy decision. Authenticode-sign the Windows launcher
  (certificate purchase). Numeric SECURITY.md response targets. Dependabot
  security updates. None changed here.
- BW-RR-RESCAN-SCHEDULE — OWNER/SPEND. A scheduled hosted rescan is new spend;
  until authorized, run scripts/rescan_release_packages.py on the latest
  manifest at least weekly and before every stick production lot.
- BW-RR-LIVEMEDIA — NEEDS QEMU + HARDWARE. live-boot is not bound to the
  medium; if a stick reports non-removable, internal partitions may be probed
  (ro mount can replay an ext4 journal). Evaluate live-media=/UUID binding with
  a QEMU case (usb-storage removable=off + dirty ext4 internal disk) and
  hardware; boot-critical, not changed blind.
- BW-RR-QEMU-COVERAGE — HOSTED ITERATION. Add NVMe and AHCI erase targets and an
  end-to-end writable-boot-stick exclusion probe (snapshot=on, assert BEAMOBOOT
  absent from the pick list); current probes attach the stick readonly=on.
- BW-RR-UX — PRODUCT DECISIONS. Report export on exFAT or clearer upfront
  guidance; HiDPI auto-scaling; high-contrast theme; ES/IT locales; per-outcome
  failure next steps; plain "computer's main drive" hint; localized typed
  console words; record selected nwipe PRNG in reports.
- BW-RR-HOST-DISK — OWNER URGENT. C: had ~1.0–1.4 GB free; iCloud Drive
  `iCloudDrive.db-wal` is ~7.7 GB and Google DriveFS WAL ~0.66 GB. Not stopped
  or deleted (owner apps). Other agents also report low space.

### Final checkpoint — 2026-10-27 UTC

- Additional commits: `40a522a` customer guidance (method screen "large hard
  disks can take many hours", restart after interruption, Intel RST/VMD/RAID
  hint on the empty list; FR/DE translated; layout modules at 72 DPI Xvfb show
  no new failures; guidance tests PASS). `7174651` scripts/verify-usb-stick.py
  + docs/manufacturing.md (99 readback tests PASS on regular-file fixtures; 149
  PASS with adjacent download/signing tests; seven tool mutations caught; no
  real device opened; procedure never executed with a duplicator or stick).
- Final local checks on the branch: ruff 0.9.2 (src+tests+new scripts) PASS,
  mypy 2.1.0 52 modules PASS, shellcheck PASS, `git diff --check` PASS. Not run:
  full pytest suite in one session, ISO build, hosted CI/QEMU, native Windows,
  browser/Orca live checks, anything physical.
- Next exact action: owner decides whether to open a PR for
  `fix/release-readiness-20261026` (starts the hosted CI gate) after or with
  PR93's fix; then follow BW-RR-RELEASE. Translation wording (FR/DE) for the
  three new sentences should get a native-speaker review.

### BW-RR-UX-POLISH-20261027 — LOCAL, UNCOMMITTED (subagent, Claude Opus 5.5)

- Same clone/branch, working tree only (not staged/committed). Done locally:
  HiDPI readable mode in `usr/local/bin/beamo-wipe` (xrandr, fake-fixture
  tests `tests/test_launcher_readable_mode.py`); method-screen rough time guide
  (`progress.time_guide`, `copy.method_time_guide`, Tk/GTK/console, FR/DE; ES
  added by the locale agent; `tests/test_method_time_guide.py`,
  `tests/test_time_guide_other_views.py`); Tk polish pinned by
  `tests/test_ui_polish_20261027.py`; docs progress-timing + DISP-12 row.
- OPEN: BW-RR-HIDPI-QEMU/PHYS — run the readable-mode launcher in QEMU (e.g.
  virtio-vga xres=3840) and on real 4K/2560x1600 panels incl. Orca view; NOT
  TESTED. Native-speaker review of the FR/DE/ES guide strings.
- OPEN (outside this task's files): wizard.py `elapsed_text` hardcodes English
  "Elapsed:" on FR/DE/ES result screens; build identity "unavailable" is not
  translated; initial focus reveal slices the Owner/Confirm title on 1280x720
  (EN) and 800x600 (DE); GTK view at 800x600 leaves the third method radio
  below the footer for the 1 TB demo HDD and in German (identical on base).

## BW-COMPAT-UX-20261027 — LOCAL VERIFIED / HOSTED, NATIVE-REVIEW AND PHYSICAL GATES OPEN

- 2026-10-27 / Claude (Opus 5.5) for the owner's request: more devices, smoother
  and better-looking experience without breaking anything. Branch
  `fix/release-readiness-20261026`, commits `261cf58`, `2fb1176`, `5fb9d90`,
  `2d1c434`, `f42acd0` after `317914d`. Clone and WSL copies as in
  BW-READINESS-WORK-20261026. No PR, hosted CI, release or device operation.
- Done locally: console-data (console layouts actually load); non-free
  graphics/audio/USB firmware + microcode; Debian-signed 6.12 kernel and
  firmware 20250410 from bookworm-backports via a chroot-only apt pin (apt
  resolution simulated against the live archive, no unmet deps); quiet normal
  boot; usbcore.autosuspend=-1 and NVMe APST off on every entry; QEMU gate
  checks for kernel >= 6.12, firmware packages/dirs, no radio firmware, and an
  X layout + console keymap for every offered layout; GPL plan adds linux/grub2/
  shim sources behind signed wrappers; HiDPI xrandr mode switch; Spanish UI and
  helper; UK/ES/LatAm/IT layouts; per-disk time guide; eight visual fixes;
  curses Left/Right layout choice; localized Elapsed label.
- Verification: full suite in three fresh sessions (private 72 DPI Xvfb,
  RAM /tmp): 96 failures, every one also failing on pristine main (no .git /
  no docs/evidence in the copy); 71 re-run on base gave the identical set.
  Note tests/test_usb_image_readback.py alone needs ~1.5 GB of /tmp (builds a
  2 GiB image) — size test temp space accordingly. ruff, security lint, mypy
  53 modules, shellcheck, git diff --check PASS.

### Open items

- BW-CU-HOSTED — NEXT CANDIDATE GATE. None of the image changes has been built:
  backports pin, archive areas, firmware/microcode/console-data, boot params,
  troubleshoot probes, squashfs/keymap/firmware checks, keyboard-layouts.txt
  evidence. The first hosted ISO/QEMU run may need iteration; ISO size grows
  (~+80–100 MB est.). Needs owner authorization for the PR/hosted gate.
- BW-CU-SB — REQUIRED BEFORE RELEASE. New image boots linux-image-6.12.95+deb12
  (backports, Debian-signed): repeat the Secure Boot component inspection
  (docs/secure-boot-acceptance.md) for the exact new image.
- BW-CU-PHYS — BLOCKED (hardware). Firmware effect on AMD/Intel/NVIDIA panels
  (incl. nouveau GSP on RTX), SOF/Cirrus audio and speech, Renesas USB 3, the
  6.12 kernel on 2023–2025 laptops, HiDPI xrandr switch on real 4K/2560x1600
  panels and docks, autosuspend/APST effect, console keymaps and all seven
  layouts typed on physical keyboards.
- BW-CU-L10N-REVIEW — NATIVE REVIEW. Spanish (choices: memoria USB, equipo,
  cuenta regresiva vs cuenta atrás, ratón, presione, Habitual, Compilación,
  omitido; SOUND_SELECTED phrasing) and every new FR/DE string (time guide,
  RST/VMD hint, power restart, keyboard limits/footer, Elapsed).
- BW-CU-VOICE — FEATURE. No language→voice mapping: Spanish (and FR/DE) text
  is spoken by Orca/espeak-ng with the default English voice; boot menu and
  kiosk recovery screens stay English.
- BW-CU-UI-LEFTOVERS — OPEN. Focus scroll clips the title (Owner 1280x720 EN,
  Confirm 800x600 DE); GTK view at 800x600 puts the third method below the
  footer (also on base); Working screen empty block before first percent;
  800x600 method cards/pick list start below the fold; Last-chance ring half
  visible at 800x600; body-scroll stale offset race when content grows then
  shrinks; preview-only banner does not re-translate; support build ID token
  "unavailable" stays English by design (support readback).
- BW-CU-QEMU-COVERAGE — unchanged from BW-RR-QEMU-COVERAGE (NVMe/AHCI targets,
  writable boot stick); a QEMU 4K VGA probe for the xrandr path is also open.

## BW-FINISH-20261028 — LOCAL VERIFIED, BRANCH PUSHED / HOSTED, NATIVE-REVIEW AND PHYSICAL GATES OPEN

- 2026-10-28 / Claude (Opus 5.5) for the owner's request to finish all open
  work from BW-READINESS-WORK-20261026, BW-RR-UX-POLISH-20261027 and
  BW-COMPAT-UX-20261027. Repo BeamoTech/beamo-wipe, branch
  `fix/release-readiness-20261026`, clone
  `C:/Users/Jack/dev/BeamoTech/beamo-wipe-readiness-20261026`. Commits after
  the pushed `40ccf8b`: 26 commits `0a02a03`..`872d38c` plus the commit adding this entry. State: pushed as branch `fix/release-readiness-20261026` (head = the commit adding this entry; ci.yml runs only for PRs/pushes to main or dispatch, so no workflow ran). No PR, no hosted
  CI, no tag, no release, no device operation.
- Agent clones (owned, safe to delete after merge): `beamo-wipe-{ui,results,
  l10n,export,it}-20261027`, `beamo-wipe-helper-20261028`,
  `beamo-wipe-pr93trial-20261028` under `C:/Users/Jack/dev/BeamoTech/`; WSL
  copies `/home/beamo-qual/bw-*-2026102[78]`.

### Done (commit: what, evidence)

- `0a02a03`…`b723156`: native-quality review fixes for FR/DE/ES UI and
  helper pages; placeholder/cited-label/safety-wording consistency test;
  `docs/translations.md` translator guide + native review checklist.
- `d842818` safety: exFAT 1.0 report USBs accepted beside FAT32 (still one
  partition, same mount/readback rules); QEMU gate requires `exfat.ko`.
- `d2f8035`: QEMU gate refuses a `shim-signed` older than `1.51~1+deb12u1`
  (Debian 12's shim 16.1-2 dual-signed by the Microsoft UEFI CA 2011 and
  2023, NX-capable per its changelog); secure-boot doc marks the next image
  UNKNOWN until Q12. German stale-progress label no longer needs a dative.
- `121697c`, `c5d125d` (UI agent): titles never sliced by focus reveal;
  stale/negative body scroll clamped; Working shows "Progress not reported"
  in a fixed slot; short windows put method cards / disk rows first;
  last-chance ring visible at 800x600 and 1024x600; preview stripe and Tk
  title re-translate; GTK limits notice after the radios; pick rows say
  "Windows / Operating system / No operating system found on this disk".
  New tests fail on the reference (143+16+13+…), pass on the branch.
- `274c80c`, `951a485`, `98c97cd` (results agent): every failed or uncertain
  outcome has its own next steps (all languages); report Limitations no
  longer truncates canonical copy; nwipe's logged PRNG shown as "Random data
  generator" for random/three-pass results (display only; parser accepts one
  exact manifest record; argv/launch/outcome unchanged, runner diff additive).
- `3599614`: countdown caption and Tk hint cite "Erase now"; EN helper says
  "Stop erase" / "Restart computer"; report-saving status reworded (EN/FR/IT).
- `4a8117e`, `4c9725a`: discovery snapshots made before the language choice
  now read in the chosen language (reasons, nested kind labels, identity
  labels, translated "Cannot erase:"); the silent nested "unsupported device"
  reason stays silent in every language; " (old)" percent mark, GTK
  "Select <disk>" name and GTK window title translated.
- `4a90eeb`: blocked-screen error (copy.IDENTIFY_ERROR, stored in English by
  discovery) is shown in the chosen language and keeps its specific heading
  and recovery guidance (`lang.current_text`); blocking logic unchanged.
- `f017eaa`, `71c2855`, `ea39f90`, `9ee7a5d`: Italian as fifth language (UI,
  helper/it.html, staging/manifest, preview `--lang it`), all later keys
  translated; key sets/order identical across fr/de/es/it.
- `ca3d813`, `e885447`: FR/DE helper troubleshooting panels rebuilt to
  English parity (illustrations, five steps, Windows menu paths, Technical
  detail with the BitLocker recovery-key warning, stylesheet); new
  section-parity test across all five helper pages. `60cdffb`, `0bba5b1`,
  `872d38c`: narrow console result test pages to the end; FR/DE
  forbidden-claims lists; the curses result page no longer repeats the
  outcome, so Report status and safe removal stay on the first 80x24 page.
- Verification: full suite on exact `872d38c` in six fresh sessions (private 72 DPI
  Xvfb, 3 GB RAM /tmp; WSL copy byte-identical to the clone; no `.git`;
  docs/evidence only secure-boot-119 and physical-acceptance-111): 12,840
  passed, 63 failed, 2 errors, 86 skipped. Reference `d842818`, same method:
  12,086 passed, 64 failed, 2 errors, 86 skipped. Every final failure and
  both errors also occur on the reference (CI/receipt/evidence tests needing
  `.git` or the omitted docs/evidence; tmp_path collisions in
  test_corresponding_source); the reference's extra failure is the GTK 60 ms
  sound-dialog timing test. ruff 0.9.2 (src+tests), security subsets,
  compileall, mypy 2.1.0 (54 files), shellcheck, `git diff --check
  40ccf8b..HEAD`: PASS. Logs: WSL `~/bw-full-872d38c-20261028/`,
  `~/bw-full-ref-d842818-20261028/` (chunk05 re-run in `rerun05/` after a
  1.5 GB tmpfs filled). Not run: ISO build, hosted CI/QEMU, native
  Windows, Chrome pixel checks (4 skips), Orca, anything physical.

### Open items (ID — acceptance, next action, blocker)

- BW-FIN-HOSTED — OWNER AUTHORIZATION (spend). The lab coverage says
  "no new spend authorized" for WIPE-ISO-QEMU. None of the image changes
  since 0.2.14 has been built (firmware/backports/console-data/boot params,
  exfat.ko, shim floor, troubleshoot probes). Next: owner authorizes the
  hosted gate; open a PR for this branch (PR/main triggers ci.yml on
  Blacksmith) or dispatch ci.yml on a verification ref; fix every failure.
- BW-FIN-PR93 — AFTER PR93 MERGES. Trial merge of PR93 head `bf2b490` into
  `4c9725a` (scratch clone `beamo-wipe-pr93trial-20261028`, aborted): one
  textual conflict, `nwipe_runner.py` duplicate-run check in start(); keep
  this branch's `or self._target_fd is not None` with PR93's
  `error = SafetyError(...)`/_close_pinned_engine pattern. PR93's new error
  paths call `_release_wipe_lock()`, which on this branch also closes the
  target reservation, so no extra cleanup is needed. Re-run the full suite
  after the real rebase/merge; PR93 may change before merge.
- BW-FIN-SB-Q12 — REQUIRED BEFORE RELEASE. Inspect the next built image
  (shim 16.1-2 dual-signed, kernel 6.12 backports): signer list, SBAT,
  2023-only firmware behaviour, per docs/secure-boot-acceptance.md.
- BW-FIN-SHIM-BUILD — WATCH FIRST HOSTED BUILD. shim-signed's preinst
  refuses to install when mokutil reports Secure Boot enabled without a
  matching db entry, or prints unexpected output. The live-build chroot runs
  in Docker on the build worker; confirm in the first hosted build log that
  the preinst passes, and that the QEMU gate's new shim floor holds.
- BW-FIN-EXFAT-QEMU — HOSTED. Add/run a QEMU report-export probe onto an
  exFAT image (only the module presence is gated today); physical exFAT
  sticks from several vendors under BW-RR-PHYS.
- BW-FIN-VOICE — FEATURE/DESIGN. Orca 43 takes its language from the
  process locale; the image runs LANG=C.UTF-8 without the `locales`
  package, so FR/DE/ES/IT text is spoken with the default English voice.
  Needs locales + espeak-ng voices in the image, a per-language Orca restart
  or settings change, and real-audio testing. Not started.
- BW-FIN-CONSOLE-WORDS — BY DESIGN. Typed confirmation words and key names
  stay English in every language (safety tokens; documented in locale
  headers and docs/translations.md). Revisit only with a safety review.
- BW-FIN-L10N-REVIEW — NATIVE REVIEW. FR/DE/ES/IT native speakers review the
  checklist in docs/translations.md (Italian entirely machine-made, incl.
  Windows names in helper/it.html; new FR/DE helper troubleshooting text).
- BW-FIN-PICK-ROW — PARTIAL. At 800x600 the first pick row starts at
  ~108 px but a full row (up to 217 px) does not fit the 192–273 px body;
  name, capacity and serial are visible. Needs a compact row design.
- BW-FIN-BUILD-TOKEN — BY DESIGN. Support "Build" value "unavailable" (no
  injected build ID: previews/dev builds only) stays an English token.
- BW-RR-PHYS, BW-RR-LEGAL, BW-RR-RELEASE, BW-RR-GPL-ARCHIVE, BW-RR-TRIXIE,
  BW-RR-SIGNING/ENV, BW-RR-RESCAN-SCHEDULE, BW-RR-LIVEMEDIA,
  BW-RR-QEMU-COVERAGE, BW-RR-HOST-DISK, BW-RR-HIDPI-QEMU/PHYS, BW-CU-HOSTED,
  BW-CU-SB, BW-CU-PHYS — unchanged (see their entries); BW-RR-SHIM is now
  BW-FIN-SB-Q12 + BW-FIN-SHIM-BUILD.
- Closed by this entry: BW-RR-UX (exFAT, ES/IT, per-outcome steps, contents
  hint, PRNG; console words by design), BW-CU-UI-LEFTOVERS (all except
  BW-FIN-PICK-ROW), BW-RR-UX-POLISH leftovers (Elapsed, focus slicing, GTK
  third radio; build token by design).

## BW-PASS2-20261028 — LOCAL VERIFIED, BRANCH PUSHED / HOSTED, NATIVE-REVIEW AND PHYSICAL GATES OPEN

- 2026-10-28 / Claude (Opus 5.5) for the owner's request to run another very
  thorough pass. Branch `fix/release-readiness-20261026` (clone
  `C:/Users/Jack/dev/BeamoTech/beamo-wipe-readiness-20261026`), continuing
  from `465274d`. Four independent read-only reviewers covered
  `58c677f..465274d` (runtime safety; UI and locales; image, build and release
  scripts; docs, helper pages and claims). Every finding was re-checked against
  the code or primary sources (Debian package lists, live-build 1:20230502,
  amd64-/intel-microcode hooks, madison, security tracker) before fixing.
  No PR, hosted CI, tag, release, device or host-setting change.
- Lab: current lab revision `6fd49c5` in owned clone
  `C:/Users/Jack/dev/beamo-remote-lab-claude-20261028` (peer checkout at
  `d3d0959` left untouched); run root
  `C:/Users/Jack/beamo-release-evidence/wipe-pass2-claude-20261028`:
  self-test PASS (61 tests, framework), doctor/sync/plan PASS (preparation).
  Plan still lists WIPE-ISO-QEMU "no new spend authorized".

### Done (commit: what, evidence)

- `89373fe` safety: the pick row never says "No operating system found"; it
  names only a recognised system. Contents check now recognises EFI+APFS/HFS+
  (Intel Mac), Linux with swap or a GPT BIOS boot partition, and a Linux
  vendor "Recovery" partition (no longer "Windows"). Selection, tokens, nwipe
  unchanged. 766 related tests PASS.
- `78dafdd`: START-HERE.html linked to fr/de/es/it.html that were never on the
  stick root; they are now staged there as START-HERE-<code>.html with links
  rewritten (live-system copies unchanged), README.txt lists them, and
  THIRD_PARTY.md is on the root as SOURCE.txt/NOTICE say.
- `6ab504f`: NOTICE/README no longer name a competitor or promise
  "sanitization"; support guidance carries the BitLocker key warning;
  "outside what the overwrite reaches" (EN/FR/DE); ADVANCED.md lists --quiet;
  THIRD_PARTY/compat matrix: misc-nonfree's legacy radio files, no PC Renesas
  USB 3 firmware, SOF 2.2.4 predates Meteor Lake.
- `9bbd3e6`: FR/DE/ES/IT helper pages say speech uses the English voice.
- `1796b6a`: verify-usb-stick.py keeps exit 1 for a FAIL whose receipt cannot
  be written; manufacturing.md: boot-QA units never ship without a fresh
  readback.
- `5437259`: corresponding_source.py `plan` no longer fails on every real
  image (shim version from the binary version; shim-helpers mapped); `fetch`
  validates nwipe/Beamo identities before writing and binds GitHub tarballs to
  the commit via the git-archive header. Real v0.2.13 manifest: plan lists
  319 sources incl. linux 6.1.190-1, grub2 2.06-13+deb12u2, shim
  16.1-2~deb12u1. rescan_release_packages.py checks linux/grub2/shim and
  ~bpo12 backports against trixie. Weekly rescan of v0.2.13 (manifest sha256
  0f2796dc…5640) 2026-10-28: same 11 fixed issues missing (openssl, expat,
  brotli); its boot packages are current. Output WSL
  `~/beamo-wipe-readiness-20261026-rescan/rescan-20261028.txt`.
- `945313e`: /etc/default/amd64-microcode forces "early" (the default "auto"
  depends on the build CPU); QEMU gate parses every live initramfs early cpio
  and requires AuthenticAMD.bin and GenuineIntel.bin (parser tested on
  synthetic archives; image not built).
- `ff6b737`: Tk keyboard screen: Up/Down choose layouts even from the
  focused check box (1–7 typed digits there; the hint now names Up/Down in
  all languages; browser preview matches); over-wide footer hints wrap;
  a long sub-page caption no longer overlaps the third stage name at
  1000-1100 px (100-case test); console keyboard screen pages its lead on
  short consoles (80x14-80x20, all languages).
- `a496b73`: FR/ES "new report USB" no longer reads "brand-new".
- `ad7fe73`: a two-part keyboard notice follows a language switch.
- `8d5e445`: the held-reservation and curses time-guide tests now check what
  their names claim.
- Verification: see "Final verification" below.

### Open items from this pass (ID — acceptance, next action, blocker)

- BW-P2-KERNEL-LAG — OWNER DECISION before the next release. Debian 12
  backports' newest kernel is linux-signed-amd64 6.12.95+1~bpo12+1; Debian 13
  has 6.12.107+1 and the tracker lists fixes up to 6.12.113-1. The corrected
  rescan counts 3,504 tracker issues fixed in trixie 6.12.96–6.12.113 that a
  6.12.95 image would lack (all urgency "not yet assigned"); the shipped
  v0.2.13 6.1.190 kernel lacks none. The build-time `debsecan --suite
  bookworm` gate cannot see backports. Options: accept the lag (offline kiosk,
  no network software), go back to the bookworm 6.1 kernel (loses newer
  hardware support), or move the base to Debian 13 (BW-RR-TRIXIE). Whatever
  is chosen, run scripts/rescan_release_packages.py on the candidate
  manifest before publication.
- BW-P2-GRUB-UTILITIES — OWNER DECISION. live-build 1:20230502 never fills
  `@ENABLE_VERIFY_CHECKSUMS@`, so "Verify integrity of the boot medium" never
  appears (the `3ee29ed` message claimed otherwise); the unlocked Utilities
  submenu exposes only "UEFI Firmware Settings" (fwsetup) on UEFI.
  tests/test_boot_menus.py::test_uefi_recovery_and_utility_blocks_preserved
  deliberately keeps both, so nothing was removed. Decide keep / lock again /
  remove (then update that test). Verify works after a live-build upgrade.
- BW-P2-GPL-SYSLINUX — OPEN, needs hosted build data. The source plan reads the
  squashfs dpkg inventory only. ISO isolinux files (Debian isolinux/
  syslinux-common, installed by live-build only during binary_syslinux) and
  the USB image's ldlinux/mbr.bin (CI host's Ubuntu syslinux) are not listed.
  Next: record those package versions in the release manifest and add them to
  corresponding_source.py (Debian via snapshot, Ubuntu via Launchpad), or
  install the USB image's syslinux from the pinned Debian container.
- BW-P2-PRNG-LONG — KNOWN LIMIT. "Random data generator" in the report comes
  from the 1 MiB log snapshot whose digest the evidence carries; after about
  5.5 h of 2-second progress lines the options header leaves that window and
  the line is omitted (never wrong). A fix needs an evidence-schema change
  (head snapshot plus digest); not done blind.
- BW-P2-RADIO-FILES — DOCUMENTED. firmware-misc-nonfree (bpo) carries Agere/
  VT6656/WF200/CW1200 Wi-Fi, Broadcom/NXP Bluetooth and Multi-Tech modem
  files; no radio package or connection software is installed. If file-level
  removal is required, it needs a reviewed hook (stage_wrapper_sources
  approves exactly one) and a squashfs file gate.
- BW-P2-SOF-MTL — DOCUMENTED. Debian 12 SOF 2.2.4 predates Meteor Lake; no
  backport exists (Debian 13 has 2025.01). 2024+ Intel laptops may be silent.
- BW-P2-HOSTED-NEW — HOSTED. Unrun until the hosted gate: the initramfs
  microcode check, START-HERE-<code>.html and THIRD_PARTY.md on a real ISO
  root and USB image, README.txt lines.
- Unchanged and still open: BW-FIN-HOSTED (spend authorization), BW-FIN-PR93,
  BW-FIN-SB-Q12, BW-FIN-SHIM-BUILD, BW-FIN-EXFAT-QEMU, BW-FIN-VOICE,
  BW-FIN-L10N-REVIEW (now also the FR/ES "new USB" and Up/Down hint lines),
  BW-FIN-PICK-ROW, BW-RR-* and BW-CU-* items listed in BW-FINISH-20261028.

### Final verification — 2026-10-28 (pass 2)

- Full suite on exact `8d5e445` (product tree of this entry's commit), WSL
  `BeamoComboQualification-20261001` as beamo-qual, pristine `git archive`
  copy `/home/beamo-qual/bw-pass2-8d5e445-20261028` (full docs/evidence, no
  `.git`), six fresh sessions with private 72 DPI Xvfb and 3 GB RAM /tmp:
  13,038 passed, 60 failed, 0 errors, 86 skipped. Every failure is in the
  known environment set of the `d842818` and `872d38c` runs (CI/receipt
  gates needing `.git`: test_ci_log_snapshot 36, ci_evidence_directory 6,
  blacksmith_ci 4, ci_evidence_pipeline 3, release_manifest 2 and 8 single
  modules; plus the GTK 60 ms sound-dialog timing test). No new failure; four
  formerly evidence-dependent tests now pass. Logs
  `~/bw-full-pass2-8d5e445-20261028/`.
- Targeted runs during the pass: contents/UI-fit/locales 766, staging and
  helper 162, docs/claims/readback 534, docs/image-config 648, source plan and
  rescan 53, microcode/boot 100, Tk layout suites 907, later UI fixes 681 —
  failures only from the same no-`.git` set.
- Static: ruff 0.9.2 (src, tests, scripts) PASS; mypy 2.1.0
  `--ignore-missing-imports` (CI form) 54 files PASS; shellcheck 0.9.0 on
  qemu-verify, build-usb-image, inside-docker, launcher, kiosk PASS;
  compileall PASS; `git diff --check` PASS.
- Lab receipts (lab `6fd49c5`, owned clone): self-test
  20261028T185439Z-786c42caac55, doctor 20261028T195848Z-25f63c5da8df, sync
  20261028T195937Z-7d9b8901b313, plan 20261028T195950Z-1186c8d08a71 — all
  `verify` VALID / PASS at framework or preparation level only.
- Not run: ISO build, hosted CI/QEMU, native Windows, Chrome pixel checks,
  Orca/speech, anything physical.

## BW-PASS3-20261028 — LOCAL TARGETED VERIFIED / HOSTED GATE PENDING; WSL DOWN; NATIVE-REVIEW AND PHYSICAL GATES OPEN

- 2026-10-28/29 / Claude (Opus 5.5) for the owner's request to "fully take
  care of all of the rest of the stuff ... do what's best for the mass
  majority of customers". The open owner decisions from BW-PASS2-20261028
  were decided on that basis (below). Branch `fix/release-readiness-20261026`,
  clone `C:/Users/Jack/dev/BeamoTech/beamo-wipe-readiness-20261026`, from
  `22fa70c`. Lab `6fd49c5` (owned clone), run root
  `C:/Users/Jack/beamo-release-evidence/wipe-pass3-claude-20261028`: doctor
  20261028T230010Z-b9c571b692a3, sync 20261028T230035Z-07fe5d9eb357, plan
  20261028T230038Z-e303374f8e43 PASS (preparation only).
- The owner's message is taken as the go-ahead for the paid hosted gate
  (BW-FIN-HOSTED). Three helper agents (Italian review, 800x600 row, PR93
  crash) were stopped by the owner mid-run; their uncommitted Italian and
  row work was reviewed, corrected and verified here before committing.

### Done (commit: what, evidence)

- `3dd48d8` BW-P2-KERNEL-LAG: the image installs Debian 12's LTS-maintained
  `linux-image-6.12-amd64` from bookworm-security (Debian-signed,
  6.12.113-1~deb12u1; DLA-4745/4788/4817) via `--linux-packages
  linux-image-6.12` (flavour stays amd64: GRUB looks for vmlinuz-*amd64);
  backports pin now firmware only. apt resolution simulated against the live
  archive (469 packages, kernel from bookworm-security, firmware 20250410
  from backports, no unmet dependency). Source plan/rescan map
  linux-signed-6.12-amd64 to `linux-6.12` (tracker files 2,886 bookworm
  issues there). Build-time debsecan can now see kernel fixes.
- `c3e37fd` BW-P2-GRUB-UTILITIES: kept "UEFI Firmware Settings", removed the
  never-filled verify-checksums block; template markers limited to those
  live-build fills; QEMU gate rejects any unfilled marker.
- `32725c8` BW-P2-PRNG-LONG: completion projection keeps nwipe's exact
  options header/prng/auto records; evidence falls back to it only when the
  digested tail cannot answer (display only; outcome/check equality tested;
  red on the old code).
- `2020bb8` BW-P2-GPL-SYSLINUX: plan always lists Debian 12 syslinux
  3:6.04~git20190206.bf6db5b4+dfsg1-3 (on snapshot); QEMU gate binds ISO
  isolinux/*.c32 and isolinux.bin (outside the boot info table) and the
  worker's syslinux packages to it.
- `b03b5a5`, `e3f35ad` BW-RR-QEMU-COVERAGE / BW-FIN-EXFAT-QEMU: QEMU erase-
  and-report journeys on an AHCI SATA disk (BIOS, FAT32 report) and an NVMe
  disk (UEFI, exFAT report, user-space fsck + guest readback markers), both
  booted from the USB image attached writable (snapshot=on).
- `5f02e2f` BW-RR-LIVEMEDIA decision: boot line unchanged (boot-critical);
  manufacturing prefers RM=1 sticks, RM=0 parts need boot evidence on a PC
  with an internal ext4 disk.
- `e48d629`: Italian grammar/wording pass (UI and helper/it.html), FR/ES
  "test box" and "only one newly plugged-in report USB", DE sentence fix.
  1,091 locale/helper/claims/keyboard/UI-fit tests PASS.
- `d430f98` BW-FIN-PICK-ROW: dense Pick row and Compare after the disks on
  short windows; first row whole at 800x600/1024x600 in all languages.
- `a00168f`: QEMU gate extracted only three ISO files, so the pass-2
  initramfs microcode check and the new syslinux check would have failed
  every hosted run; it now extracts /live, /isolinux, /EFI/boot (regular
  files only). BW-FIN-SB-Q12 aid: gate records sbverify signers and PE .sbat
  of shim, GRUB and kernel in secure-boot-signers.txt.
- `d3ba776`: the one-kernel check counted the linux-image-6.12-amd64
  meta-package too (would have failed every image); fake-dpkg test, red on
  the old script.

### Decisions recorded (no change)

- BW-P2-RADIO-FILES — keep documented (no connection software, no customer
  effect).
- BW-P2-SOF-MTL, BW-FIN-VOICE — keep as documented limits. Sound and speech
  on 2024+ Intel laptops and non-English voices need Debian 13 firmware/UCM
  or locale work plus real-audio tests; the screen works without them.
- BW-RR-TRIXIE — still a planned migration; the LTS kernel removes its
  urgency (bookworm LTS runs to ~2028-06).
- BW-FIN-PR93 — not taken over (Codex's open PR, native GTK crash; its
  handoff needs a native backtrace on an admitted Linux worker). The
  investigation agent was stopped by the owner with no result. Whichever PR
  lands second rebases (conflict notes in BW-FIN-PR93 still apply).

### Open items (ID — acceptance, next action, blocker)

- BW-P3-WSL-DOWN — OWNER ACTION. At ~03:10 UTC 2026-10-29 the shared WSL
  distro `BeamoComboQualification-20261001` began failing every process start
  with EIO (getpwnam/getpwuid failed 5, /etc unreadable, also as root). Its
  dynamic VHDX (182.6 GB) is on C:, which had 3.3 GB free; most likely the
  VHDX could not grow. Not stopped or repaired (shared instance). Next: owner
  frees C: space and approves `wsl --terminate BeamoComboQualification-20261001`
  plus a filesystem check. Note `coordination/wsl-io-errors-claude-20261029.md`.
- BW-P3-FULL-LOCAL — NOT RUN. The full local suite on the final candidate
  could not start (WSL down). Every changed area passed its targeted tests
  (counts above and in the commit messages); the hosted gate's full suite is
  the full-suite evidence for this candidate.
- BW-P3-HOSTED — PENDING. First hosted run of every image change since
  0.2.14 (BW-FIN-HOSTED, BW-P2-HOSTED-NEW, BW-CU-HOSTED). Expect iteration:
  first SATA/NVMe/exFAT journeys, writable-stick boots, syslinux byte check,
  signer record, LTS kernel. Fix every failure; never weaken a check.
- BW-FIN-SB-Q12 — after a green hosted run, a person reviews
  secure-boot-signers.txt from that run's evidence against
  docs/secure-boot-acceptance.md and writes the Q12 receipt.
- Unchanged: BW-FIN-SHIM-BUILD (watch the first build log), BW-FIN-L10N-REVIEW
  (now incl. the Italian pass), BW-RR-PHYS, BW-RR-LEGAL, BW-RR-RELEASE,
  BW-RR-GPL-ARCHIVE, BW-RR-SIGNING/ENV, BW-RR-RESCAN-SCHEDULE,
  BW-RR-HIDPI-QEMU/PHYS, BW-RR-HOST-DISK (now urgent: it took WSL down),
  BW-CU-PHYS.

### Verification — 2026-10-28 (pass 3), targeted only

- WSL `BeamoComboQualification-20261001` as beamo-qual, private 72 DPI Xvfb,
  RAM /tmp: kernel/boot/hardware/docs 377+45; boot menus 31; PRNG and
  projection 721 (new test red 4/7 on old code); source plan 41; QEMU gate,
  publisher and inventory suites 974 then 61 and 13; locale/UI 1,091; pick
  row, ISO inspection, Secure Boot record and layout 832; kernel gate 12.
  All failures seen were in the known no-`.git` environment set.
- ruff 0.9.2 (src, tests, scripts), mypy 2.1.0 (54 files), shellcheck 0.9.0
  (qemu-verify, ci-hosted, inside-docker) PASS on `d3ba776`'s tree.
- Not run: full local suite (WSL down), ISO build, hosted CI/QEMU, native
  Windows, Orca/speech, anything physical.

## BW-PASS3-CI-UI-20261031 — HOSTED GATE ITERATING; UI REDESIGN COMMITTED; GREPTILE UNAVAILABLE; WSL STILL DOWN

- 2026-10-29..31 / Claude (Opus 5.5). Branch `fix/release-readiness-20261026`,
  clone `C:/Users/Jack/dev/BeamoTech/beamo-wipe-readiness-20261026`, PR #94.
  Continues BW-PASS3-20261028 (its open items stand unless updated here).

### Done (commit: what, evidence)

- Hosted CI iterations (Blacksmith `ci.yml`, paid gate authorised by the
  owner in pass 3): run 40811225589 → `6f638b5` (CodeQL tag regex),
  `ab8bfbd` (Greptile P1: SATA report identity, test), `33ea16e` (Tk callback
  traceback hook, Italian pin); run 40814724934 → `9aad14a` (Tk distances
  as Tcl objects on Debian 12 Python 3.11 / Tk 8.6.13, 284 failures);
  `6f21bed` (gitignore generated USB-root pages); run 40820524524 first
  reached QEMU, BIOS safe video failed → `05e52bb` (GRAPHICAL_FAILED marker,
  guest screendump); run 40824797788 → `e793841` (drop vga=788, gate rejects
  vga=); run 41232620234 BIOS safe video PASS, UEFI safe video FAIL →
  `27a4fce` (X failure classification); run 41237147966: fb0=1, no DRI,
  vesa error → `8697d65` (kiosk writes a one-session fbdev Device for
  nomodeset + fb0 + no DRM only; 7 tests PASS locally via Git sh).
- `383e6b7` UI redesign (owner request "modernize ... cleaner and
  simpler"): gray page #EEF2F6 with white surfaces, white header/footer
  bars, quiet footer tools, owner check above its notes (in view at all
  four sizes, five languages), Pick leads with disks, roomy review card;
  gallery and helper mirror it. Local (Windows harness, scratch
  `C:/Users/Jack/dev/beamo-wipe-pass3-scratch-20261028/per`):
  modern_layout+ui_polish 81 PASS, pick_row_fit 24, header_caption 98
  (+1 Tk-load flake), ui_fit 262, adaptive 91 (one test hangs on Windows
  on the frozen base too), gallery/helper/UI-system 215, ruff 0.9.2 and
  mypy 2.1.0 (--platform linux) PASS. Every other local failure also failed
  on the frozen base copy or is a Windows-only environment error (Tk
  library reads under concurrency, symlinks, POSIX paths, no desktop focus,
  DryRunRunner cannot reach WORKING, curses stub).

### Open items (ID — acceptance, next action, blocker)

- BW-P3-HOSTED — ITERATING. Next: hosted run on the pushed head with
  `8697d65` + `383e6b7`; expect UEFI safe video to pass, then the
  remaining QEMU stages (Secure Boot record, SATA/NVMe/exFAT journeys).
  Fix every failure; never weaken a check; push only after a run finishes
  (cancel-in-progress).
- BW-P3-GREPTILE — BLOCKED. Greptile reviewed only `f6719f3` (finding fixed
  in `ab8bfbd`); no review on later heads. Owner reports this month's credit
  is used up; not confirmable from repo/API evidence (cause: unknown, owner-
  reported credit exhaustion likely). No credits bought. An author-agent
  review of `f6719f3..HEAD` is recorded on PR #94 and is NOT independent.
  Acceptance: an independent review (a person, or Greptile when available)
  of the final diff against main, recorded on the PR per AGENTS.md.
- BW-P3-UI-VISUAL — owner looks at the after screenshots; native-speaker
  review (BW-FIN-L10N-REVIEW) should include the reordered owner screen.
- BW-P3-WSL-DOWN, BW-P3-FULL-LOCAL, BW-FIN-SB-Q12, BW-RR-PHYS and the rest
  of BW-PASS3-20261028's open list — unchanged.

### BW-PASS3-CI-UI-20261031 update — 2026-11-01 / Claude (Opus 5.5)

- BW-P3-HOSTED — DONE for head `a76ee5c` (pushed). Run 41275044269: CI gate,
  Linux image gate and Windows launcher tests success; QEMU summary every
  case pass (methods x2, bios/uefi/usb, secureboot_usb, speech BIOS/UEFI,
  troubleshoot BIOS/UEFI, sata_bios_usb, nvme_uefi_usb, exfat_report,
  writable_boot_usb, report_export). ISO 160f1c8d…5740d, USB image
  47391793…09220, nwipe 7303abba…71c0e. Evidence artifact
  ci-evidence-…-41275044269-1 includes secure-boot-signers.txt.
  Evidence binds to that exact SHA only; any later push needs a new run.
- UEFI safe-video root causes fixed: `0b8cfdd` (ProtectSystem=full blocked
  a runtime /etc write; shipped -config file), `f2b993a` (Linux 6.9+ PCI
  parent vs Xorg 21.1.7 fbdevhw; private-namespace class link; fixed
  upstream in Xorg 21.1.16 / Debian 13 — drop the workaround on the trixie
  move, BW-RR-TRIXIE), `a76ee5c` (GRUB gfxmode 800x600x32 first; X cannot
  use a 24bpp packed framebuffer). Gate: UEFI safe video runs last
  (`3ff10b7`, `63ad9fe`); fixed X/fbdev classes plus a QEMU-only (DMI
  vendor QEMU) geometry detail in private serial evidence (`5a17f01`,
  `c5fe630`).
- BW-P3-GREPTILE — still BLOCKED: no Greptile review after `f6719f3`;
  author-agent reviews (not independent) recorded on PR #94 for
  `f6719f3..0b5bf48` and `0b5bf48..a76ee5c`. Next: a person (or Greptile
  when available) reviews the final diff against main and records it on
  the PR per AGENTS.md.
- BW-P3-SB-Q12 next action: a person reviews secure-boot-signers.txt from
  run 41275044269 against docs/secure-boot-acceptance.md.
- Known limit: a firmware offering no 32-bit 800x600 mode still gets the
  keyboard text guide in safe video (24bpp fbdev unsupported by Xorg).
- This update is a LOCAL commit in the readiness clone, not pushed: a push
  would rerun the paid gate and move the PR head off the green SHA. Land
  it with the next necessary push or the merge.
- Unchanged: BW-P3-WSL-DOWN (owner action), BW-P3-FULL-LOCAL (hosted full
  suite passed on a76ee5c: covers it for this head), BW-FIN-L10N-REVIEW,
  BW-RR-PHYS, BW-RR-RELEASE, PR #93 ordering, owner merge decision.

### BW-PASS3-UI2-20261101 — second UI modernisation pass — 2026-11-01 / Claude (Opus 5.5)

Owner request: "It still needs a bit of modernization. Go ahead and run
another very thorough and comprehensive pass of this." Repo
`beamo-wipe`, branch `fix/release-readiness-20261026`, readiness clone
`C:/Users/Jack/dev/BeamoTech/beamo-wipe-readiness-20261026`.

- DONE locally (commit after this note on the same branch):
  - lighter secondary button edge (`BUTTON_EDGE`);
  - sound and "Erase another disk" actions are links;
  - no rule inside the footer;
  - soft selected-disk summary edge (`SUMMARY_EDGE`), with Show more in
    its caption row on Confirm, Method, Working and Done;
  - Pick help link and Show more on the inventory row;
  - storage-limits link inside the limits notice on roomy Method;
  - segmented text-size control;
  - one-column review screen: red erase callout (same words), countdown
    ring beside its caption, compact on 800x600 and 1024x600;
  - evidence warning on Working is a warn panel;
  - sans monospace fallback for Windows/macOS previews;
  - gallery mirrors tokens, review layout, segmented control and links.
  - Tests: `tests/test_modern_polish_20261101.py`; pass-1 review test
    updated; the gallery Node test pipes its program on stdin.
- Local evidence (Windows harness, not Linux):
  - new file plus pass-1 layout tests: 48 passed (one Tk file-read error);
  - review/countdown fit in every language at 800x600 and 1024x600,
    kiosk and preview: 51 passed. A first version overflowed by up to
    22 px in preview; fixed before commit;
  - `test_ui_fit_20261027` + `test_tk_runtime`: failure set identical to
    HEAD `1ba496c` (16 environmental each);
  - gallery files: only difference was the Node argv-length limit, now
    fixed (6 passed).
  - Not run here: Playwright browser tests; Linux/DejaVu 72 DPI fits;
    `test_reflow_large_text` last_chance, which hangs on this host for
    both trees.
- Host note: C: had about 0.95 GB free, and Tk library reads failed
  intermittently (BW-P3-WSL-DOWN owner action).
- NEXT: the hosted gate must pass on the new head before merge (any push
  reruns the paid full gate). Independent review (BW-P3-GREPTILE) must
  cover this diff too. Owner looks at the screenshots in the scratch
  `compare2/`.
- 2026-11-01 update (BW-PASS3-UI2-20261101): hosted gate GREEN on pushed
  head `9c16e13` (run 41300394923; merge ref `e4cb941` = main `58c677f` +
  `9c16e13`). CI gate, Linux image gate and Windows launcher tests
  succeeded; pytest 13997 passed / 0 failed / 15 skipped; every QEMU case
  passed. ISO 1008de9f…a81b, USB image 141fde94…5d1a, nwipe 1dbe27e2…2447.
  Still open: independent review of the final diff (BW-P3-GREPTILE), owner
  merge decision, BW-FIN-SB-Q12 (signers from this run), native-speaker
  review, PR #93 ordering, BW-RR-PHYS. This note is a LOCAL commit only.

## BW-UX-AUDIT-20261101 — UX improvement audit (proposals, nothing implemented)

- Status: OPEN, awaiting owner choice of which items to build. 2026-11-01,
  Claude. Repo `beamo-wipe`, branch `fix/release-readiness-20261026`, read
  at `0f8f5e0` (local). Source: screenshots in scratch
  `beamo-wipe-pass3-scratch-20261028/p2after{,-s}/` plus copy.py,
  outcomes.py, methods.py, progress.py, inventory.py, tk_wizard.py.
- Top items (full list was given in chat on 2026-11-01):
  1. Report without a second USB (e.g. on-screen QR summary); current
     route needs a separate FAT32/exFAT USB, plugged in only at the end.
  2. One strong erase warning per screen; the same consequence text repeats
     on Owner, Confirm (twice in one panel), Review (gray line + red callout).
  3. Confirm token is printed in the prompt; ask for the serial's last
     characters shown in the card instead (safety: commit + tests).
  4. Header stays on "1 Preparation" for 6+ screens; show sub-steps.
  5. Language comes after layout on the keyboard screen; put it first and
     suggest a layout from the language.
  6. Working: five unlabeled lines incl. "not reported" placeholders;
     show %, time left, step N of M; offer the finish sound up front.
  7. Result title "Erase completed; verification passed" -> plain words
     plus a what-next checklist; declutter the 6-control Done footer.
  8. Pick: show partition labels/filesystems (discovery has `label`),
     drop the duplicated serial "characters 1 to 14" line, compact rows,
     double-click to review, sort internal first.
  9. "Check disks again" (clears owner tick + confirmations) is a casual
     footer link on Confirm/Review; inconsistent utility sets per screen.
  10. Pre-boot: unsigned Windows launcher (SmartScreen), one-click
     "restart to boot options", detect Intel VMD/RST for the empty state.
- Constraints: any confirm-token, disk-selection or nwipe-flag change is a
  `safety:` commit with tests; claims per docs/claims.md; SSD
  sanitize/secure-erase is outside the current safety boundary (owner).
- NEXT: owner picks items; implement locally, then final hosted gate.

## BW-127-QR — Photo record (QR erase summary) on the result screen (IMPLEMENTED; HOSTED GATE, PHONE SCANS, MERGE PENDING)

- Status: implemented and committed as `adaaef1` on branch
  `feat/qr-erase-summary-127` (worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`). Base: PR #94
  head `9c16e13` plus local docs commits `0f8f5e0`, `fdaaa44`, `13322c1`.
  2026-11-02, Claude. NOT Done: the Linux/hosted gate, phone-camera scans
  and native-speaker review are open, and nothing is on main. It depends on
  PR #94, which is unmerged (owner decision).
- Owner decision (2026-11-01, in chat): "Go with all of the best options that
  optimize for user experience and convenience while also factoring in safety
  and ease of use. I approve all of that." Applied:
  - Fields: header "Beamo Wipe erase summary. Not a certificate."
    - Result: the exact on-screen outcome.
    - Disk, Capacity, and the identifier the disk card shows: the full Serial
      number, or Hardware ID when the disk reports no usable serial. Including
      Hardware ID is a judgment call so serial-less disks stay identifiable.
    - Method.
    - Started/Ended (clock not verified), when validated.
    - Elapsed, when known.
    - Report: saved to USB with the first 12 hex of the result.json checksum,
      saved (sharing copy), not saved, or could not be stored.
    - Software: Beamo Wipe version, 8-char build id, nwipe version.
    - Not included: URL, support code, path, warnings, logs.
  - Changed from the proposal:
    - No separate Verification line; Result already states it.
    - 4 px modules at every size, so no "Keep a record" button is needed.
    - The record is placed after the next steps and any check warnings, so it
      never pushes a "not a pass" warning down.
  - Encoding: plain UTF-8 text in the session language with RESULT.txt
    labels. QR uses ECC M, a 4-module quiet zone and a UTF-8 ECI (26) header.
  - Wording:
    - "Keep a record without a USB"
    - "Photograph this code to keep a record of this erase. It is a summary,
      not a certificate."
    - "Your phone's camera shows it as text. No app or internet is needed.
      The photo shows the disk's serial number."
  - Report help: 7 sections become 4, with "No second USB? Photograph the
    code" first. USB export is unchanged. The `REPORT_MEDIA_WHAT` Owner note,
    claims.md and the 5 helper pages now mention the photo option.
- Gating (never shown):
  - screen != DONE;
  - evidence still saving or finishing;
  - `stop_unconfirmed`;
  - a pinned nwipe may still run, or recovery is busy;
  - the result cannot be repeated exactly.

  Preview shows a sample with no disk identity. Nothing is written anywhere.
- Files:
  - `src/beamo_wipe/erase_record.py` (new);
  - `wizard.py`, `ui/tk_wizard.py`, `ui/accessible_wizard.py`,
    `ui/console_wizard.py`, `gallery.py`, `copy.py`, `lang.py`,
    `locales/{fr,de,es,it}.py`;
  - `helper/*.html`;
  - docs: `claims.md`, `screens.md`, `screen-reader.md`,
    `report-shutdown.md`, `development.md`;
  - `THIRD_PARTY.md` (python3-qrcode 7.4.2-2, BSD-3-Clause, already in the
    image; no new package);
  - package-list comment;
  - tests: `tests/test_erase_record_127.py` (new, 86 cases),
    `tests/test_accessible_runtime.py` (GTK record test, 4 cases),
    `tests/test_screen_hierarchy.py` (new headings).
- Checks run. Windows host only: WSL fails with I/O errors and may not be
  restarted. Used a scratch fcntl/realpath shim; see memory
  `windows-native-test-route`.
  - `test_erase_record_127.py`: 85 passed, 1 skipped (Windows Tk start-up
    flake). Decodes every outcome in all 5 languages (zxing-cpp), and covers
    evidence-save failure, gating, no truncation, the Tab cycle and 800x600
    clipping at 3 text sizes.
  - qrcode 7.4.2 and 8.2: 55/55 (5 languages × 11 outcomes) decode exactly,
    with ECI 26 present.
  - 12 rendered Tk screenshots: 12/12 decoded by zxing-cpp and by OpenCV
    Aruco. Sizes 800x600, 1280x820 and 1600x1000; large and extra text; fr
    and de; evidence error; preview.
  - ruff (full plus both S-selections): pass. mypy `--platform linux`: pass.
  - Baseline-diff of 106 UI, copy and wizard test files: only regressions
    found were Italian 800x600 clipping and a lost FAT32/exFAT sentence; both
    fixed. The 12 focused report, language and helper files now show the same
    failure set as baseline (Windows-only failures).
  - 5 Tk layout files time out on Windows in both trees: adaptive_layout,
    ui_fit, tk_runtime, reflow_large_text, header_caption_fit. NOT verified
    locally.
- Not run / open:
  - full Linux pytest at Xvfb 72 DPI, including the 5 files above;
  - GTK/Orca tests (no gi on Windows), including
    `test_accessible_done_reads_the_erase_record_as_text`;
  - `test_result_tab_order_reaches_report_without_shutdown` (Linux fixture);
  - CI decodes with pyzbar/zbar; its handling of ECI is unverified until it
    runs;
  - ISO build and QEMU on Blacksmith `ci.yml`. Not dispatched: the paid gate
    needs the owner's choice of route (below);
  - phone-camera scans with two apps against the screen and against a photo
    of it (needs a person with a phone);
  - native-speaker review of the new fr/de/es/it strings;
  - browser-preview screenshot (Windows demo disks are not eligible); its
    content is covered by `test_gallery_preview_shows_the_sample_record`.
- Screenshots (scratch, not committed):
  `C:\Users\Jack\dev\BeamoTech\qr127-scratch-20261101\shots-before\` and
  `shots-after\`.
- NEXT (owner chooses):
  1. Fold this commit into PR #94, or open it as a PR after #94 merges. The
     PR's hosted `ci.yml` run is the final gate.
  2. Or dispatch `ci.yml` on `feat/qr-erase-summary-127`.

  Then scan the result screen with two phone camera apps (iOS Camera and
  Android Camera / Google Lens) on a monitor and from a photo. Fix any
  failure and rerun. Merge to main only after all of these pass.

## BW-128-WARN — One erase warning per screen (IMPLEMENTED LOCALLY; HOSTED GATE, NATIVE REVIEW, MERGE PENDING)

- Status: implemented on branch `feat/single-erase-warning-128` (stacked on
  `feat/qr-erase-summary-127` at `2a79067`, which sits on PR #94 head `9c16e13`),
  worktree `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`.
  2026-11-02, Claude. NOT Done: the Linux 72 DPI suite, GTK/Orca runtime and
  ISO/QEMU gate have not run, the translations need native review, and
  nothing is on main (it depends on unmerged PR #94 and #127).
- Problem (UI review item 2): Owner said "Everything on that disk will be
  erased. You cannot get the files back." and then "erasing it also
  removes…"; Confirm's yellow box said "Every file … will be erased. You
  cannot get them back." and then "Erasing it also removes…"; Review showed
  a gray "This selected disk shows Windows partitions. Erasing it also
  removes…" line above the red "This will erase … You cannot get the files
  back." callout.
- Change (copy only; no disk-selection, token, countdown, method or nwipe
  change, so not a `safety:` commit):
  - `copy.py`: new shared `ERASE_EVERYTHING`, `ERASE_EVERYTHING_WINDOWS`,
    `ERASE_EVERYTHING_SYSTEM`, `ERASE_CANNOT_UNDO` and `erase_warning(disk,
    identity)`. Confirm = "Everything on <model>, <size> will be erased[,
    including Windows | including its operating system]. You cannot get it
    back." Review red callout = the same sentence with the serial/hardware
    ID. The system is named only when partitions show one (models.CONTENTS_*).
  - Owner `WHAT_BULLETS`: "Beamo Wipe erases everything on the disk you
    choose, including any Windows or Linux on it." / "Make sure you have
    copies of anything you want to keep." / platforms line (unchanged).
  - Removed: `PREPARE_WINDOWS/SYSTEM/DATA/UNKNOWN`, `CONFIRM_WARNING_TEXT`,
    `ERASE_NOW_TEXT`, `copy.prepare_selected`, `Wizard.prepare_text`, the
    gallery `prepare` field, and the Review gray line in Tk, GTK, curses and
    plain console. fr/de/es/it tables updated in the same key positions.
  - Helper pages (5 languages): "What this USB does" first paragraph now
    uses the Owner sentence, "You cannot get it back." and the backup line;
    the second paragraph no longer repeats the erase consequence.
  - Docs: `docs/screens.md` Owner/Confirm/Review rows; new strings added to
    the `docs/translations.md` native review checklist. `docs/claims.md`
    unchanged (no new claim).
- Warning inventory before the change (all surfaces, file:line at
  `2a79067`): copy.py:153-157 WHAT_BULLETS[0..1]; copy.py:184-199 PREPARE_*;
  copy.py:851 CONFIRM_WARNING_TEXT; copy.py:852 ERASE_NOW_TEXT; Owner
  tk_wizard.py:3347, accessible_wizard.py:433, console_wizard.py:836 and
  1358, gallery.py:561 (+ JS owner bullets); Confirm tk_wizard.py:4265,
  accessible_wizard.py:510, console_wizard.py:945 and 1510, gallery.py:164
  (+ JS `panel("warn", d.warning)`); Review gray line tk_wizard.py:4704,
  accessible_wizard.py:639, console_wizard.py:1028 and 1668, gallery.py:165
  (`prepare`, not rendered by the JS); Review red callout tk_wizard.py:4729,
  accessible_wizard.py:644, console_wizard.py:1030 and 1670, gallery JS
  `selected.eraseLabel`; helper/*.html:574-575.
- Tests: new `tests/test_single_erase_warning_128.py` (per-screen counts for
  Tk at 800x600 and 1280x820 x 3 text sizes, curses, plain console and the
  gallery; Review callout above the fold, bold red, the only red text, before
  the countdown, in all 5 languages x 3 text sizes; shared-sentence and
  retired-string checks in all languages). New GTK test
  `test_accessible_screen_reads_one_erase_warning_before_the_action` in
  `tests/test_accessible_runtime.py` (count, ALERT role, arrival focus,
  warning before the action). Updated: test_copy, test_prepare_aftercare,
  test_contents_efi_token_pass13, test_contents_os_layouts_20261028,
  test_accessibility_lowres, test_accessible_runtime, test_adaptive_layout,
  test_console_parity, test_console_enter_interleaved_pass25_ui,
  test_tk_runtime, and test_curses_review_page_pass18_ui (terminal 16 -> 14
  rows so the paged-warning safety scenario still starts below page one).
- Checks (Windows-native route; WSL still fails with I/O errors):
  - On the baseline tree the new file fails 51 cases (every rendered count,
    including all 12 Tk per-screen cases); on the change all non-extra cases
    pass.
  - ruff (all CI selections), compileall and `mypy --platform linux`: pass.
  - Per-file comparison of 213 related files (scratch
    `warn128-scratch-20261102/pf-{base,new}.txt`): new-only failures were
    test_curses_review_page_pass18_ui (fixed above), test_laptop_power_ui
    [size1-what] (passes on two reruns; flake) and test_usb_report_workflow
    (disk filled while both trees wrote its ~537 MB fake image at once; not
    rerun because C: has ~220 MB free; untouched code).
  - Final focused run of the 7 most affected files: exit 0.
  - Screenshots: `warn128-scratch-20261102/shots-{before,after}/` (Owner,
    Confirm, Review at 800x600/1280x820, large text, fr/de/es/it);
    console renders `console-{before,after}.txt`.
- Not run / blocked:
  - Tk at the Extra-large text size on Review: on this Windows host Tk's
    idle layout never settles (baseline and change alike; also with 72 DPI
    scaling). Linux CI covers it, including the new above-the-fold test.
  - GTK/Orca runtime tests (need Linux GTK), full `python3 -m pytest`,
    ISO build and QEMU: hosted `ci.yml` gate only.
  - Intermittent Windows Tcl start-up failures ("couldn't read file …
    No error") plus WSL I/O errors and a full C: suggest a host storage
    problem; owner should check the disk.
  - #180 and #181: not found in the repo, the backlog or GitHub issues (the
    full UX list was given only in chat); nothing changed for them.
- NEXT: owner chooses the hosted-gate route for #94 + #127 + #128 (fold into
  PR #94 or dispatch `ci.yml` on this branch); after a green gate and native
  review, merge in order #94 -> #127 -> #128. Do not push to main before that.

## BW-129-TOKEN — Confirm asks for marked serial characters (IMPLEMENTED LOCALLY; HOSTED GATE, NATIVE REVIEW, MERGE PENDING)

- Status: implemented on branch `feat/serial-suffix-token-129`, stacked on
  `feat/single-erase-warning-128` (`39316c9`) -> #127 -> PR #94 `9c16e13`;
  worktree `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`.
  2026-11-02, Claude. SAFETY change (confirmation token): `safety:` commit.
  NOT Done: Linux 72 DPI suite, GTK/Orca runtime, ISO build and the QEMU
  gate (whose guest helper derives the token) have not run; translations
  need native review; nothing is on main.
- Problem (UI review item 3): the prompt printed the answer ("Type these 4
  characters so we know it is the right disk: 3456"; most disks "…: 256"),
  so owners could copy it without reading the disk card.
- Rule (safety.confirm_spec, documented in docs/screens.md "Confirmation
  characters"): the last 4 characters of the identifier the card shows
  (serial; hardware ID/WWN as printed when no serial), more characters while
  another listed disk (incl. the protected Beamo USB) ends the same way or
  the ending equals another disk's size label, full ID or a kernel name;
  "whole serial/hardware ID" when every character is needed. ASCII letters
  and digits only. Missing, shorter than 4, or an ending with a space,
  punctuation or non-ASCII keeps the older rule (prompt prints size label /
  same-size suffix / full ID), else AMBIGUOUS_IDENTITY as before. The
  prompt names field and count, never the characters ("Type the last 4
  characters of the serial number shown above."); duplicates add "Another
  listed disk ends with the same last 4 characters, so more are needed."
- Comparison (#156 decision): unchanged `token_matches` — outer whitespace
  ignored, case-insensitive, nothing else (no inner spaces, no partial, no
  auto-fill). Launch still recomputes the token from the rediscovered list
  (assert_ready_to_wipe) after the identity check, so serial/size/WWN/path
  changes are rejected and a new lookalike disk makes the typed characters
  too short (TOKEN_MISMATCH). The token is never logged or exported.
- Marking: Tk keeps the whole serial in one label and places a boxed
  (1 px INK) and underlined (2 px bar) copy of the ending exactly over those
  characters (`_mark_token`, `CONFIRM_MARK_BG` fill); GTK identity text gets
  Pango double underline + bold + tint and is focusable/selectable on
  Confirm so Orca reads it by character, entry accessible name = full
  instruction; curses, plain console use `[brackets]`; web preview uses a
  `<mark>` with outline + underline. `DiskIdentityView.token_start/end`,
  `token_marked_id`; `copy.confirm_prompt(spec, console=)`.
- Files: safety.py, models.py (ConfirmSpec.in_card), identity.py, copy.py,
  locales fr/de/es/it (7 keys), ui/tk_wizard.py, ui/accessible_wizard.py,
  ui/console_wizard.py, gallery.py; docs/screens.md, runbook.md,
  accessibility-lowres-matrix.md, translations.md.
- Tests: new `tests/test_card_token_129.py` (normal serial, punctuation /
  space / non-ASCII endings, missing/short serial, WWN fallback, 4-char
  serial, duplicate endings incl. boot USB and size collisions, duplicate
  serials, pairwise "no disk accepts another's token" over mixed fleets,
  partial/padded input, #156 whitespace/case, no auto-fill, rediscovery:
  serial change keeping the ending, size/WWN/path change, new lookalike disk;
  curses, plain console, gallery, all languages, Tk mark position at 2 sizes
  x 2 text sizes). New GTK test in test_accessible_runtime.py. Updated
  old-rule expectations: test_confirm_token, test_compatibility_matrix,
  test_capacity_and_unknown_type (size-label fallback kept with no serial),
  test_contents_efi_token_pass13, test_identity,
  test_console_confirm_utility_tokens_pass34_ui (peer forces whole word),
  test_console_fallback_complete, test_security_hardening_new and
  test_serial_comparison (escaping of every serial slice),
  test_usb_report_workflow (QEMU guest token = numeric serial 0001; helper
  computation reproduced for serials 0001-0005 x 3 boot sizes).
- Checks (Windows-native route; WSL still broken): behaviour probe on the
  baseline fails 6/8, passes 8/8 on the change (scratch
  `token129-scratch-20261102/probe-results.txt`); ruff (all CI selections),
  compileall, mypy --platform linux pass; per-file comparison of 102
  token-related files (pf-base/pf-new1): every new-only failure was an
  old-rule expectation, now updated; Confirm-related Tk tests in
  tk_runtime/ui_fit/reflow/adaptive (6 sizes) pass. Screenshots
  `token129-scratch-20261102/shots-{before,after}/`, console diff
  `console-{before,after}.txt`.
- Not run here: test_usb_report_workflow (fixtures need ~2.6 GB; C: has
  ~150 MB), GTK/Orca tests, full pytest, ISO/QEMU. Related #148/#152/#156:
  not found in repo/backlog/issues; #156 comparison decision recorded above.
- NEXT: hosted gate with #94/#127/#128 (owner chooses route); native review;
  merge in order #94 -> #127 -> #128 -> #129.
- 2026-11-02 / Claude (Opus 5.5), hosted gate. Owner asked to use free CI
  allowances. Findings: repo is public, so GitHub standard runners are free
  (Oct runner minutes $0 net; Actions storage was billed $0.51 org-wide);
  ci.yml uses Blacksmith labels (switching would be a workflow change).
  Blacksmith free tier 3,000 2-vCPU min/month per org, overage billed;
  org estimate from GitHub job timings (dashboard not accessible): Oct
  ~36,700 (mostly beamo-flasher), Nov 1-2 ~1,100. GCP not used (legacy per
  this guide). One `workflow_dispatch` of ci.yml on
  `feat/serial-suffix-token-129` @ c313878: run 41493625767 FAILED (Linux
  image gate 201 failed / 14,025 passed; Windows launcher tests passed; ISO
  and QEMU not reached). Causes: (1) #129 `_mark_token` did float() on
  `cget("bd")`, a Tcl_Obj on Debian 12 Tk 8.6.13; the TypeError retired the
  wizard on every Confirm screen (as 9aad14a); (2) #127
  `test_erase_record_127._decode` imported numpy, absent in the CI image.
  Plus the intended negative-test failure. Fixed: distances via
  winfo_fpixels(str()), TypeError caught and the mark hidden; new test
  `test_tk_mark_survives_distances_returned_as_tcl_objects` (fails on the
  old code with TypeError, passes now); Pillow-only zbar canvas
  (pixel-identical to the numpy canvas, zxing decodes it). zbar decode with
  ECI UTF-8 still unverified locally (pyzbar DLL needs a missing VC++
  runtime). Local: test_card_token_129 and test_erase_record_127 pass; CI
  ruff selections and mypy pass. X11-only Tk files skip on Windows by
  design. Two #128 Tk cases at 800x600 extra text
  (LAST_CHANCE; review callout extra-en) hang locally on #128, #129 and the
  fix alike; they passed in the hosted run. If #127 merges alone it needs
  the numpy fix too.
- Run 41518189715 on 71f06f6 (5fa1633 numpy-free decode + 71f06f6 Tcl_Obj
  mark fix): source tests, ISO and most QEMU passed; FAILED at
  bios-quick_zero: "never emitted a new exact marker
  BEAMO_WIPE_CONFIRM_MATCHED". Cause (harness, not product): the BIOS
  method boots attach the ISO with -cdrom, QEMU's default IDE serial is
  QM00003, and the quick_zero target serial 0003 shared its last 4. The
  guest rightly listed both and fell back to the older rule; the host helper
  models the boot media with no serial and typed 0003. Fix: CD-ROM-booted
  targets now use 7001/7002/7003 (UEFI default 7001); USB journeys keep
  0004/0005 (boot media serial BEAMOBOOT). New test
  `test_cdrom_booted_targets_keep_their_own_confirm_characters` checks each
  target against QM00001..QM00012. Local QEMU-related test failures are
  identical to the baseline's 19 Windows-environment failures.
- Run 41528619370 on 4fa4c15: source tests, ISO, all six BIOS method
  journeys (every Confirm matched, erase, report export), bios/uefi-usb,
  troubleshoot, speech and Secure Boot boots passed. FAILED at
  bios-sata-usb after Erase now: "never emitted a new exact marker
  BEAMO_WIPE_KEY_RETURN_RELEASED" (qemu-verify.sh send_key_for_marker
  release wait, 20 s, key-up retried at 5 and 10). Guest serial evidence
  (artifact ci-evidence-4fa4c15...-41528619370-1): the SATA erase reached
  WORKING and DONE before any Return release was acknowledged, and none
  followed on DONE. In the green PR #94 run (41300394923) and in all six
  method journeys here, the release was acknowledged during WORKING,
  before DONE. Not a Confirm/#129 step; the stack did not change key
  bindings (root <KeyRelease-Return> -> after_idle _release_return ->
  arm_done_keyboard). Unproven whether this is a timing race (fast 64 MB
  AHCI erase) or a DONE-screen effect of #127's record drawing; if the
  release is lost, Done stays unarmed until the next Return press/release.
- NEXT (owner decision): either one more ci.yml run on 4fa4c15+ to test
  the race hypothesis, or first investigate DONE-screen release handling
  (#127) in a Linux X11 guest. Then native review and the merge order.

## BW-130-STEPS — Preparation sub-steps in the step bar (IMPLEMENTED LOCALLY; HOSTED GATE, NATIVE REVIEW, MERGE PENDING)

- 2026-11-02, Claude (Opus 5.5). Branch `feat/step-progress-130` (stacked on
  `feat/serial-suffix-token-129` @ 946c622), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`. Backlog #130
  (UI review item 4) with #138 (one set of names) and #166 (Review last
  before Erase); #138/#166 are not recorded in this repo.
- Owner decision (2026-11-02, in chat): sub-steps, keeping the three stages
  Preparation -> Erase -> Result; step names reuse the start-screen roadmap.
- What changed: `wizard.BACK_SCREENS` (Back now uses it), `PREPARATION_PATH`
  (Back chain from Review: keyboard, owner, pick, confirm, method, review),
  `STEP_VARIANTS` (WHAT->owner, PICK_EMPTY/PICK_BLOCKED->pick,
  CHECKING->review), `journey_step_for()` and `Wizard.journey_step`
  (detours keyboard/Advanced/report help follow where they were opened;
  disk help, limits follow Back). `copy`: STEP_NAME_* (Check keyboard,
  Confirm ownership, Choose a disk, Confirm its identity, Choose a method,
  Review and erase), STEP_CAPTION "Step {n} of {total} · {name}",
  STEP_SPOKEN, `journey_step_caption/short/announcement`, `splash_roadmap()`
  (replaces SPLASH_ROADMAP; now adds Choose a method). Tk header shows the
  caption right of the brand (stepper narrows to leave room, hides if the
  stage names would not fit; caption falls back to "Step N of 6", never
  cut); strip fills the Preparation segment by step. GTK heading ATK
  description "Preparation, step N of 6: <name>."; curses/plain console
  header carries the same text (80 cols full, narrower "Step N of 6", very
  narrow dropped as before to protect the 16-row pick view). Web preview
  gets per-screen captions/strip fill from the same Python tables. fr/de/
  es/it strings added (native review pending, docs/translations.md).
- Files: wizard.py, copy.py, gallery.py, locales/{fr,de,es,it}.py,
  ui/tk_wizard.py, ui/accessible_wizard.py, ui/console_wizard.py,
  docs/screens.md, docs/translations.md; tests: new
  tests/test_step_progress_130.py (path = Back chain, every screen classed
  once, distinct labels, variants/detours on the real wizard, empty/blocked
  scenarios, erase/result fallback, roadmap = step names in 5 languages,
  console, web preview, rendered Tk header at 800x600/1280x820 x 3 text
  sizes, 4 languages at 800x600 standard/extra, strip fill), GTK test in
  test_accessible_runtime.py; updated test_journey_stages.py,
  test_ui_polish_20261027.py, test_ui_system.py (old "Preparation only"
  header expectations; still no "of 8", no percent).
- Checks (Windows-native; WSL broken): new tests pass (non-Tk 32/32; all 15
  Tk cases individually; one full-file run had a local Tcl flake that
  passes alone). Per-file comparison of 155 related files vs the
  untouched branch head: new-only failures were the 4 old-header
  expectations (updated) and ROADMAP_ARROW in the translation sweep (made
  private); the rest pass alone or fail identically on the baseline
  (export worker st_rdev, canvas progress). ruff (CI selections), mypy
  --platform linux, compileall pass. Screenshots
  `C:\Users\Jack\dev\BeamoTech\step130-scratch-20261102\shots-{before,after}\`,
  console/GTK text `console-{before,after}.txt`.
- Not run here: GTK/Orca runtime test (no gi), full pytest on Linux at
  72 DPI, ISO/QEMU, web preview in a browser (payload checked by test).
  Review at 800x600 extra text is skipped on Windows only (pre-existing Tk
  idle-layout loop); Linux CI runs it.
- NEXT: hosted ci.yml on the stack (#94/#127/#128/#129/#130; also tests the
  open SATA release-ack question in BW-129-TOKEN); native translation
  review; merge in order #94 -> #127 -> #128 -> #129 -> #130.

## BW-131-LANG — Language first; its usual layout follows (IMPLEMENTED LOCALLY; HOSTED GATE, ORCA VOICE, NATIVE REVIEW, MERGE PENDING)

- 2026-11-02, Claude (Opus 5.5). Branch `feat/language-first-131` (stacked
  on `feat/step-progress-130` @ 979b5ff), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`. Backlog #131
  (UI review item 5); #139/#140/#155 are not recorded in this repo.
- What changed: `keyboard.LANGUAGE_LAYOUTS` (en->us, fr->fr, de->de,
  es->es, it->it; shipped layouts only) and `LANGUAGE_ALTERNATIVE_LAYOUTS`
  (en->gb, es->latam, named as the obvious alternative; nothing else
  guessed). `Wizard.choose_language()` (used by every language picker):
  applies the language; on the keyboard screen it also applies the mapped
  layout through `_apply_layout_locked` (the same OS-apply + authorization
  invalidation as a manual pick) unless the person picked a layout
  (`layout_chosen`, notice "kept") or owner tick / disk / typed confirmation
  / authorization exists (notice "stays", layout untouched). Failed apply:
  old layout kept, existing failure message. `set_language()` unchanged
  (never touches the layout). Notice text `copy.keyboard_layout_notice`
  ("Keyboard set to AZERTY (French) to match Français. Keys do not match?
  Choose your keyboard below."). `lang.LANGUAGE_PICKER_LABEL` ("Language ·
  Langue · Sprache · Idioma · Lingua", untranslated). Tk: picker above the
  title, first in focus (initial focus on the chosen language), Left/Right
  and Space choose, Enter continues (radio-group keys; QEMU's Return still
  reaches Owner), focus remembered across redraws (layout card / check
  box), notice above the layout cards, HINT_KEYBOARD now starts
  "Left/Right" (key caps added in Tk and web). GTK: picker right after the
  heading, arrival on the chosen language, notice before layouts. Curses:
  language line + notice under the header, always on screen (F2 cycles);
  plain console lists L1..L5 first. Web preview: language first, page
  starts on its language's layout with the notice; Confirm's keyboard line
  follows the layout.
- Files: keyboard.py, lang.py, wizard.py, copy.py, gallery.py,
  locales/{fr,de,es,it}.py, ui/tk_wizard.py, ui/accessible_wizard.py,
  ui/console_wizard.py, docs/screens.md, docs/translations.md; tests: new
  tests/test_language_first_131.py (mapping, own names, auto-pick per
  language, back to English + UK alternative, Spanish + Latin American,
  manual override sticks, progress keeps layout and answers, off-screen and
  programmatic changes never touch layout, failed apply, preview reset,
  token comparison after each auto layout incl. partial/inner-space/other
  disk rejected, later manual change still clears confirmation, curses,
  plain console, web preview x5 languages, Tk first on screen/focus at
  800x600/1280x820 x 3 text sizes, French re-render incl. header/footer/
  primary, arrows+Enter, layout focus kept, Tk confirm box token per
  layout); GTK test in test_accessible_runtime.py; updated
  test_keyboard_layout.py, test_tk_keyboard_option_pass23_ui.py,
  test_ui_system.py, test_language_selection.py (old order/focus/regex).
- Checks (Windows-native): #131 tests 26 non-Tk + 14 Tk pass. Per-file
  comparison of 123 related files vs 979b5ff: new-only failures were the 4
  intended expectation changes (updated, pass); others were Tcl start-up
  flakes (pass alone), Windows cp1252 source reads (pass with UTF-8, as on
  Linux) or the sparse checkout without docs/evidence (environment). ruff
  (CI selections), mypy --platform linux, compileall pass. Screenshots
  `C:\Users\Jack\dev\BeamoTech\lang131-scratch-20261102\shots-{before,after}\`,
  console `console-before.txt`.
- NOT DONE: Orca speaking in the chosen language. Bookworm's Orca 43 speaks
  with its configured voice; the live image has no locale data, and
  switching would need restarting/reconfiguring Orca mid-session, which
  cannot be verified here (needs a Linux X11 + Orca + espeak-ng run). GTK
  labels and names do switch immediately. Owner decision needed.
- Not run here: GTK/Orca runtime tests (no gi), full Linux pytest, ISO/QEMU,
  real setxkbmap/loadkeys on the live image, browser check of the web view.
- NEXT: hosted ci.yml on the stack; Orca-voice decision; native review;
  merge #94 -> #127 -> #128 -> #129 -> #130 -> #131.

## BW-132-WORKING — Working screen reads at a glance (IMPLEMENTED LOCALLY; HOSTED GATE, ORCA SPEECH, NATIVE REVIEW, MERGE PENDING)

- 2026-11-02, Claude (Opus 5.5). Branch `feat/working-screen-132` (stacked
  on `feat/language-first-131` @ e319a6c), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`. Backlog #132
  (UI review item 6). Ref #133/#167/#168 are not recorded in this repo; not
  implemented here (the sound toggle already sits on Working).
- What changed: shared `ProgressView` glance in progress.py
  (`glance_percent` clamped to 99% on Working, `glance_headline`
  Starting…/Stopping…/Finishing…, `glance_time` "About N left" only from the
  existing gated estimate via `time_left()` (same upward rounding) else
  "Running for N", `glance_step` "Step k of n: Overwriting / Overwriting
  (pass i of n) / Checking (verification)" or the mismatch warning,
  `glance_stale`, `glance_notes`, `stopping_text`, `spoken_summary`) and
  `ProgressAnnouncer` (milestones >=5 s apart, else <=1 per 60 s). No parser,
  estimate-gate, runner or completion change; timing_text/status_text kept.
  Tk: big percent / Starting… slot, time line, step line, stale warning band,
  small notes; hidden lines collapse; tighter card on short windows; bar
  capped below full. Stopping screen: step + elapsed. GTK: one focusable
  label (large first line) + Gtk.ProgressBar named "Erase progress", both
  changed only when the announcer fires. Curses: same lines first. Plain
  console: paced summary. Web preview: same glance. Locales fr/de/es/it.
- Files: progress.py, gallery.py, locales/{fr,de,es,it}.py,
  ui/tk_wizard.py, ui/accessible_wizard.py, ui/console_wizard.py,
  docs/screens.md, docs/progress-timing.md, docs/translations.md,
  docs/accessibility-lowres-matrix.md. Tests: new
  tests/test_working_glance_132.py (38 non-Tk: starting/unknown/overwriting/
  verifying/stale/stopping/quick zero/three overwrites/mismatch, never 100%,
  time-left rounding, no-estimate, live wizard model, announcer pacing incl.
  a 10-hour bound, 4 locales, curses lines, plain console pacing; 18
  rendered Tk: 5 states x 3 text sizes at 800x600 on the live window, Stop
  present, Stopping text, lines hide/collapse); GTK expectations in
  test_accessible_runtime.py; updated expectations in test_tk_runtime,
  test_ui_fit_20261027, test_slow_unusual_interactions, test_preview_parity,
  test_console_pick, test_hidden_failures_visible, test_wizard_flow,
  test_console_escape_repeat_20260924, test_accountable_audit_2026_09_03,
  test_progress_timing (plain console prints the glance),
  test_accessibility_lowres, test_gallery_working_focus_pass35_ui (stub).
  Constant named GLANCE_OVERWRITE_ROUND (CI ruff S105 flags "*_PASS").
- Checks (Windows-native, 2026-11-02/03): new file 38 + 18 pass; it fails
  on e319a6c (collection error: no glance API). Per-file comparison of 267
  related files vs e319a6c: every new-only failure was an intended
  expectation change (updated, pass); the remaining failures are identical
  on the baseline (native launch, environment). Both trees time out on
  test_adaptive_layout / test_reflow_large_text /
  test_single_erase_warning_128; run per test, only Windows Tk idle-loop
  hangs remain (Review extra 800x600; reflow[working-size0] hangs on the
  baseline too). ruff (CI selections incl. S rules), mypy
  --ignore-missing-imports (Linux platform), compileall and node --check of
  the web preview JS pass. Lab: doctor + plan --project wipe PASS
  (preparation level only; no adapter covers this branch). Screenshots in
  scratch work132-scratch-20261102 shots-before / shots-final (27 each,
  visible.txt; console.txt has curses frames).
- NOT VERIFIED: Orca actually speaking the paced summary or progress bar
  (no GTK/Orca here); GTK tests; full Linux pytest, including the Working
  tests that need a real fake-erase launch (test_canvas_layout progress
  card, test_slow_unusual delayed progress, test_operation_sequence,
  test_write_vs_completion); ISO/QEMU; 72-DPI Xvfb fit.
- Deferred by scope: Ref #133 (walk away + sound up front), #167
  (start/expected times), #168 (screen stays lit); not in this repo's
  backlog.
- NEXT: hosted ci.yml on the stack head (owner approval); Orca check on the
  image; native translation review of progress.GLANCE_*; merge order
  #94 -> #127 -> #128 -> #129 -> #130 -> #131 -> #132.

## BW-133-SOUND — Walk away; a sound when the result is ready (IMPLEMENTED LOCALLY; HOSTED GATE, REAL AUDIO/ORCA, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/finish-sound-133` (stacked on
  `feat/working-screen-132` @ d1ec2a3), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`. Backlog #133
  (UI review item 7). Ref #168 (screen stays lit) not in this repo; not done.
- Design: the existing design ties one session setting (`sounds_enabled`)
  to the outcome sound, so the Working toggle "Play a sound when it's
  finished" IS that setting (the result screen's Sounds on/off). Each erase
  (`_arm_running_wipe` -> `_begin_finish_sound_locked`) turns it on unless
  the person explicitly chose on/off earlier this session; the state carries
  to the result. Availability: `sound.output_status()` (live + unmuted
  output) runs on the audio worker as a new `background=True` submission
  that is skipped when the worker is busy and never cancels the sound
  dialog's or a person's request; checked when Working opens (retry 5 s
  while unknown) and every 60 s. Copy: beep promised only when available
  and on; otherwise "You can leave the computer and check back later." or
  "Sound isn't available on this computer — check back later." + reason;
  toggle greyed (Tk greyed _CheckRow, GTK insensitive + ATK description,
  curses no O key) and ignored by the model. Laptop advice POWER_KEEP
  follows the walk-away line once (Tk Working now shows it; GTK/curses
  already did). Sounds per outcome unchanged: finished only for
  "verified", attention for everything else incl. Quick zero. Repeats:
  every 60 s, max 5 plays, stop on any key/click/control (Tk _nav/_on_key/
  root ButtonPress, GTK button/key, curses key, plain typed answer), sounds
  off, or leaving the result. Bell fallback: curses `curses.beep()`, plain
  `\a` once (it blocks on input), only when no output was found.
- Files: audio_jobs.py, sound.py, copy.py, wizard.py, gallery.py,
  locales/{fr,de,es,it}.py, ui/tk_wizard.py, ui/accessible_wizard.py,
  ui/console_wizard.py, docs/screens.md, docs/screen-reader.md,
  docs/translations.md. Tests: new tests/test_finish_sound_133.py (36
  non-Tk + 6 Tk); GTK test in test_accessible_runtime.py; updated
  test_console_parity, test_console_pick (x2), test_tk_runtime (x2),
  test_gallery_working_focus_pass35_ui (intended: default on, new label,
  one redraw on first availability answer, switch button in web preview).
- Checks (Windows-native, 2026-11-03): new 42 pass; all fail on d1ec2a3.
  Per-file comparison of 290 related files vs d1ec2a3: new-only failures
  were intended expectation changes (updated, pass) or test doubles without
  the new API (UI calls now getattr-guarded; pass); two Tk results that
  flipped pass 3/3 on both trees (Windows Tk flakes). Timed-out files run
  per test: remaining failures identical on baseline (native launch, tmp
  permissions, KP_Enter keysym) or the known Windows Review-extra hangs.
  ruff (CI selections incl. S rules), mypy, compileall, node --check pass.
  Screenshots: scratch work133-scratch-20261103 shots-before /
  shots-final-{yes,no} / shots-after-checking (visible.txt, console.txt).
- NOT VERIFIED: real PulseAudio output/mute detection and playback on the
  image, Orca hearing the check box, GTK tests, terminal bell on real
  hardware, full Linux pytest, ISO/QEMU. Bell is best-effort, never promised.
- NEXT: hosted ci.yml on the stack head (owner approval); live audio check
  on the image; native review of the new strings; merge order #94 -> #127 ->
  #128 -> #129 -> #130 -> #131 -> #132 -> #133.

## BW-134-RESULT — Plain result headline and a short "What next" list (IMPLEMENTED LOCALLY; HOSTED GATE, GTK/ORCA, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/plain-result-134` (stacked on
  `feat/finish-sound-133` @ 572d35d), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`. Backlog #134
  (UI review item 8). Refs #170/#171/#172 are coordination only (not in this
  repo's backlog record; not done). Proposal recorded first (9ea6d68).
- OWNER APPROVAL (2026-11-03, in chat): "I approve it all, just do whatever is
  best for the overall user experience and convenience while also
  maintaining security and safety overall." Choices made under that: item 4
  verified = option A (the note above already carries the SSD limit);
  failure headlines = F2; Quick zero item 4 as proposed; item 1 reworded
  surface-neutral ("Shut down when you have finished." — the console has no
  button; Enter shuts down).
- APPROVED ENGLISH WORDING (as shipped, `outcomes.py`):
  - verified (Everyday, Three overwrites): "Done — this disk was erased and
    checked". Note: "The check read the disk back after the last overwrite.
    It covers the storage the disk shows; on an SSD, the drive's controller
    decides what remains. Other disks were not erased."
  - unverified (Quick zero only): "Done — this disk was overwritten with
    zeros (not checked)". Note: "Quick zero does not read the disk back, so
    nothing confirms the overwrite reached every part. On an SSD, the
    drive's controller decides what remains. Other disks were not erased."
  - What next: 1 "Shut down when you have finished." 2 "When the computer
    is off, remove the Beamo USB." 3 "Keeping this computer? If this was its
    main disk, install an operating system before you use it again." 4
    verified "Giving it away or selling it? This disk is ready to pass on." /
    Quick zero "Giving it away or selling it? Erase it again with Everyday
    first — it checks its work."
  - Failures: verification_failed "Not confirmed — the check after the erase
    failed"; engine_failed "Not finished — the disk reported an error";
    process_failed "Not finished — the erase ended with an error";
    completion_missing "Not confirmed — the erase may not have finished";
    indeterminate "Not confirmed — the result is unknown"; interrupted "Not
    finished — the erase was interrupted"; cancelled "Stopped — you stopped
    the erase before it finished"; occupied "Not finished — the disk was in
    use"; open_failed "Nothing erased — the disk could not be opened";
    geometry_unusable "Nothing erased — the disk could not be used safely";
    start_failed "Nothing erased — the erase could not start";
    stop_unconfirmed "Not confirmed — the erase may still be running".
    Preview unchanged.
- Design: `ResultView` (and `message`) unchanged, so evidence, sharing-copy
  validation, the saved report/README, RESULT.txt (QEMU check), the photo
  record and support codes are untouched. New `outcomes.PlainResult` /
  `plain_result()`, `Wizard.result_plain` (unsaved-evidence replaced
  messages map to their outcome's headline; a recovered session's notice
  leads the note) and `Wizard.result_technical`
  (`recovery.technical_status`: "<message>. Result code: <code>").
  Surfaces: Tk heading + note + What next above the support identity, the
  technical line behind Show more; GTK heading, focusable note/list (What
  next is an ATK heading), Technical details expander; curses title + list
  on the first 80x24 page, technical line in the tail; plain console
  headline, list, technical line; web preview stop screens use the
  headline. Finished outcomes no longer show the separate POST_ERASE_BOOT
  note or the AFTERCARE_SUCCESS paragraph (item 3 and the note say it once).
- Files: outcomes.py, wizard.py, recovery.py, gallery.py, locales/{fr,de,es,
  it}.py (22 strings each, drafts), ui/{tk_wizard,accessible_wizard,
  console_wizard}.py; docs screens.md, screen-reader.md, translations.md,
  runbook.md, storage-and-controller-limits.md, README.md. Tests: new
  tests/test_plain_result_134.py (42 non-Tk + 10 Tk); a GTK test added and
  5 GTK expectations updated in test_accessible_runtime.py; updated
  test_separate_footer_actions, test_console_parity, test_outcome_heading,
  test_post_erase_boot (x3), test_prepare_aftercare (x2),
  test_rendered_visible_behavior (x3), test_result_presentations (x2) —
  all intended wording changes (headline/list instead of message/next step).
- Checks (Windows-native, 2026-11-03): new tests 52 pass; all fail on 572d35d
  except the ResultView-fields guard (passes on both by design). Per-file
  comparison of 91 related + 14 doc-test files vs 572d35d: new-only failures
  were the intended expectations above (updated; pass), Tk Tcl/init
  glitches (pass individually), the sparse worktree's missing
  docs/evidence/ (physical_acceptance_111, secure_boot_expectations,
  usb_verification_docs; the archive baseline has it), and tmp
  PermissionError / symlink-privilege failures identical on the baseline.
  ruff (CI selections incl. S rules), mypy --platform linux, compileall,
  node --check of the gallery script and git diff --check pass.
  Screenshots: scratch work134-scratch-20261103 shots-before / shots-after /
  shots-after-de (visible.txt, console.txt).
- NOT VERIFIED: GTK/Orca tests and speech (no GTK on this host), full Linux
  pytest at 72 DPI, ISO/QEMU, native review of the FR/DE/ES/IT strings.
- NEXT: hosted ci.yml on the stack head (owner approval); native review;
  merge order #94 -> #127 -> ... -> #133 -> #134.

## BW-135-REPORT — Guided Save a report panel; two-action result footer (IMPLEMENTED LOCALLY; HOSTED GATE, GTK/ORCA, QEMU, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/report-panel-135` (stacked on
  `feat/plain-result-134` @ 1d69a67), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`. Backlog #135
  (UI review item 9). Refs #127/#145/#153/#175 coordination only.
- WHAT CHANGED: the result footer keeps two actions (Erase another disk,
  Shut down; preview: Close preview, Run again). Report saving is a
  "Save a report (optional)" panel (heading = `REPORT_STATUS_TITLE`, was
  "Report status") with five numbered steps: 1 insert a separate FAT32/exFAT
  stick; 2 live line ("Looking for a USB…", "Found: SanDisk Ultra, 16 GB
  (FAT32)", "More than one new USB stick…", "This USB is formatted NTFS — use
  a FAT32 or exFAT stick.", or the precise refusal + next step); 3 Save report
  to USB; 4 where it was saved + file names (existing receipt, Ref #35); 5
  remove the report USB. Save is greyed with "Save is available when one
  suitable USB is found." until exactly one eligible stick is found. Retry
  evidence save lives in the panel; on evidence failure the panel moves under
  the disk summary (Tk: Retry right after the warning headline) so it stays
  in the first 800x600 view (Ref #153). Greyed footer actions show a reason
  ("…come back when saving finishes" etc.) in the footer note.
- SOUNDS (Ref #175 not decided in this repo): Tk/gallery put Sounds: on/off
  and Hear again with the other settings utilities in the footer assist
  strip (Tab-reachable; focus kept on the toggle after pressing); curses
  keeps "O: Sounds … H: Hear again" as the settings line under the two-action
  line; plain console prints them after the report; GTK keeps the Sound check
  utility (it had no Done sound buttons). Relocate when #175 decides.
- SAFETY / DETECTION: `support_export.probe_report_usb` = one read-only
  `lsblk` scan through the export's own baseline (boot USB + erased target
  required) and `select_export_volume`; returns state + model/size label +
  filesystem name only (no path/serial). Never mounts, opens, writes or runs
  anything else (test patches subprocess/os.open/mkdir to fail). Wizard polls
  it on a background thread every 1.5 s only while a save is possible (Done,
  not preview, evidence gate ok, not exporting, not saved); redraw only on
  change; detection resets at each export claim (stick pulled mid-save is
  looked for again). Live probe only in the kiosk (dry_run=False, no injected
  exporter). Save still runs the unchanged export with its two scans; the
  evidence gate, exactly-one-new-USB rule, boot/target exclusion and
  FAT32/exFAT 1.0 support (confirmed in code: vfat FAT32 + exfat 1.0) are
  unchanged. No erase discovery, boot exclusion, nwipe argv, token, countdown
  or method change; commit uses `safety:` because report-USB discovery gained
  a new read-only caller.
- FILES: new `src/beamo_wipe/report_panel.py`; `support_export.py` (probe),
  `wizard.py` (probe wiring/polling, `report_panel`, `done_actions_reason`),
  `copy.py` (+27 strings; `REPORT_STATUS_TITLE`, `REPORT_HELP_STAGES` changed;
  `CON_DONE_SAVE`/`CON_DONE_RETRY` replaced by `CON_PANEL_*`), locales
  fr/de/es/it (drafts), `ui/tk_wizard.py`, `ui/accessible_wizard.py`,
  `ui/console_wizard.py`, `gallery.py`; docs screens.md, screen-reader.md,
  runbook.md, ADVANCED.md, README.md, translations.md.
- TESTS: new `tests/test_report_panel_135.py` (probe states incl. no USB, two
  USBs, NTFS/FAT16/ext4/HFS+/unknown, mounted/read-only/two partitions,
  protected disks, scan failure, read-only guarantee; every panel state incl.
  saving/saved/failed/removed mid-save/evidence/preview; wizard polling;
  Tk footer two actions in 9 states + preview, greyed-has-reason, two-Tab
  QEMU path, evidence Retry in first view, sounds by Tab + focus kept, live
  redraw keeps focus, text sizes; curses and plain console). GTK: one new
  test + export-stages test updated in test_accessible_runtime.py (not run
  here). Updated: test_rendered_visible_behavior, test_separate_report_status
  (+ the files listed under CHECKS).
- CHECKS: Windows-native (WSL down), 2026-11-03. New test file: 77 pass
  (53 non-Tk, 24 Tk run one by one); all fail on 1d69a67 (no report_panel
  module). Per-file comparison vs 1d69a67 of 294 related files plus 34
  doc/QEMU-script files: new-only failures were intended pins of the old
  footer/"Report status"/export-stage wording (updated: test_rendered_visible_
  behavior, test_separate_report_status, test_export_stages,
  test_erase_record_127, test_warning_success_differentiation,
  test_language_selection EXCLUDED probe states; ES "use" -> "utilice"), the
  #134 first-view and German 800x600 fits (fixed by putting the footer note
  beside the sound links), and environmental ones identical to the baseline
  or explained: tmp PermissionError (_done_wizard/write_evidence_atomic),
  Tcl init glitches (pass alone), WSL/gh 401, the sparse worktree's missing
  docs/evidence/. ruff (CI selections incl. S rules), mypy --platform linux,
  compileall, node --check of the gallery script (en, de), bash -n
  qemu-verify.sh and git diff --check pass. QEMU: qemu-verify.sh now waits
  for BEAMO_WIPE_REPORT_USB_FOUND (fixed state-name marker emitted by Tk)
  instead of a fixed 5 s sleep before Tab, Tab, Space.
- KNOWN DEBT: copy.report_aftercare / export_stage_lines / EXPORT_STAGE_*
  are no longer used by any surface (kept with their tests; remove and port
  those tests to report_panel in a follow-up).
- SCREENSHOTS: scratch `work135-scratch-20261103` shots-before (1d69a67),
  shots-after, shots-after-de (visible.txt), console.txt.
- NOT VERIFIED: GTK/Orca tests and speech (no GTK here), full Linux pytest at
  72 DPI (WSL down), ISO/QEMU (the qemu-verify Tab-Tab-Space save path now
  needs the live probe to find the hotplugged stick within its 5 s sleep;
  covered locally only by the Tk two-Tab test), real USB sticks, native
  review of FR/DE/ES/IT strings.
- NEXT: hosted ci.yml on the stack head (owner approval) incl. QEMU report
  save; native review; #175 decides the final sound-settings place; merge
  order #94 -> #127 -> ... -> #134 -> #135.

## BW-136-REFRESH — Check disks again cannot silently clear confirmations (IMPLEMENTED LOCALLY; HOSTED GATE, GTK/ORCA, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/refresh-guard-136` (stacked on
  `feat/report-panel-135` @ 05161a5), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-readiness-20261026`. Backlog #136
  (UI review item 10). Safety-adjacent: `safety:` commit.
- BASELINE (05161a5): the utility showed on What/Owner (no disk list); the
  Check disks again screen from Review/Confirm focused "Check disks again",
  so Enter or a second F5 cleared every confirmation; the Tk screen-reader
  switch (F8 / utility) rescanned directly from any screen, including
  Confirm/Review, with no question at all.
- CHOICE: guarded dialog, not hiding, on Confirm and Review (also Method,
  Advanced, Limits). Why: a person who replugs a disk at Review needs the
  rescan where they are; hiding would send them back through several
  screens to Pick, where the same reset happens anyway with less
  explanation. The guard keeps it reachable but deliberate: Cancel is the
  default and emphasised button, Enter/Esc keep the answers, a second F5
  does nothing, and only the outlined Check disks again button (curses C,
  plain console the typed words) clears them.
- WHAT CHANGED: wizard `REFRESH_DIRECT_SCREENS` (What, Owner, Pick,
  empty, blocked, disk help) and `REFRESH_OFFERED_SCREENS` (Pick family +
  Confirm, Method, Review, Advanced, Limits); `refresh_offered`,
  `refresh_guarded` (unknown origin fails closed), `open_refresh_confirm(
  then_reader=)` only on offered screens; `begin_refresh` refuses a direct
  scan from any non-direct screen (incl. report help opened after Owner), so
  no surface can skip the dialog. Accepting runs the unchanged
  begin/finish_refresh reset (same fields cleared, lands on Owner). Pick's
  dialog is unchanged (normal action). Tk, GTK, curses, plain console and the
  web preview follow; the Tk F8 reader switch opens the same guarded dialog
  on those screens and opens the reader after acceptance. Pre-launch
  rediscovery/identity comparison (`confirm_erase`) untouched.
- COPY: "Check disks again?" + "This clears your confirmations and you will
  start again from choosing a disk: you tick the ownership box again, then
  choose the disk." (the requested sentence, extended because a rescan
  lands on the ownership question before Pick); Cancel; hints; curses/plain
  keys. FR/DE/ES/IT drafts.
- FILES: wizard.py, copy.py, locales fr/de/es/it, ui/tk_wizard.py,
  ui/accessible_wizard.py, ui/console_wizard.py, gallery.py; docs
  screens.md, screen-reader.md, README.md, translations.md. Tests: new
  tests/test_refresh_guard_136.py; test_accessible_runtime.py (2 updated,
  1 added; GTK not run here).
- CHECKS: Windows-native (WSL down), 2026-11-03. New test file: 52 pass
  (41 non-Tk, 11 Tk run one by one); on 05161a5 all fail except the Pick-
  unchanged guard (passes on both by design). ruff (CI selections), mypy
  --platform linux, node --check of the gallery script and git diff --check
  pass. Per-file comparison of 264 related test files vs 05161a5 (finished):
  34 files had new failures; triaged one by one, none a product bug. Almost
  all exercised exactly what #136 changed (direct `refresh_disks()` from
  Review/Confirm, now refused; rescans from Owner, now not offered; a second
  F5 or Enter accepting from Review). Those tests were moved to the dialog or
  to Pick so each still checks its original property, and several now prove
  the guard (direct rescan from Review returns False and changes nothing; F5
  never accepts the guarded dialog in Tk, GTK fakes and the web preview; a
  fresh Enter in the curses guarded dialog cancels). Fakes gained
  refresh_offered/refresh_guarded. Web preview: REFRESH_OFFERED moved inside
  the sliced script region and inlined in draw(). Also fixed: ES/FR/DE/IT
  "clears" used the erase verb (c856f2b). After the fixes the remaining
  failures in those files match 05161a5 (Windows tmp PermissionError,
  sparse docs/evidence), and the Tk/Tcl ones pass one by one.
- SCREENSHOTS: scratch `work136-scratch-20261103` shots-before (05161a5) and
  shots-after (owner/pick/confirm/review/dialog-from-pick/dialog-from-
  review at 800x600 and 1280x820, visible.txt with focus).
- NOT VERIFIED: GTK/Orca tests and speech (no GTK here), full Linux pytest
  at 72 DPI (WSL down), ISO/QEMU, native review of FR/DE/ES/IT strings.
- NEXT: hosted ci.yml on the stack head (owner approval); native review;
  merge order #94 -> #127 -> ... -> #135 -> #136.

## BW-137-START — Start screen opening line (IMPLEMENTED, BRANCH PUSHED; HOSTED GATE, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/start-line-137` (stacked on
  `feat/refresh-guard-136` @ c856f2b), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-137-20261103`. Backlog #137 (UI
  review item 11); Refs #138/#181 coordination.
- WHAT CHANGED: `copy.SPLASH_TAGLINE` "You already started from this USB.
  Next you will pick a disk to erase." -> "Erase a disk in a few steps.
  Nothing is erased until you choose Erase now." Tighter than the suggested
  "until you confirm": the ownership tick and typed check are confirmations
  that erase nothing; only the separate Erase now (`BTN_ERASE`) starts it,
  so the line names that control. FR/DE/ES/IT drafts name the translated
  button. Tk, GTK (splash heading), curses, plain console and the web
  preview read the same string. Docs: screens.md Splash row,
  translations.md.
- TESTS: tests/test_copy.py — exact English line + names BTN_ERASE; every
  language names its BTN_ERASE; reading-level guard (2 sentences, <=10
  words each, words <=7 letters; Ref #181). The first five fail on c856f2b;
  the reading-level guard passes on both (the old line was short too).
- CHECKS: copy/intro/language/translation-consistency files 237 pass;
  ruff, diff --check. Screens: scratch work137-scratch-20261103
  shots-before/shots-after (en 800x600 standard/large/extra, 1280x820; de).
  Per-file comparison of 109 splash/gallery test files vs c856f2b
  (finished): no new failures from #137; the two new-only lines were
  environmental (docs/evidence absent in this worktree; a Tcl flake that
  passes alone).
- NOT VERIFIED: GTK/Orca speech, Linux pytest at 72 DPI, ISO/QEMU, native
  review.
- NEXT: finish comparison, push branch; hosted gate on the stack head
  (owner approval); merge after #136.

## BW-138-STAGES — One stage vocabulary for the start roadmap and header (IMPLEMENTED, BRANCH PUSHED; HOSTED GATE, GTK/ORCA, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/stage-names-138` (stacked on
  `feat/start-line-137` @ 57bac5a), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-138-20261103`. Backlog #138 (UI
  review item 12); decided with #130 (step bar) and #166 (Review last before
  Erase); #180 coordination only.
- BASELINE: header = stages Preparation/Erase/Result (stepper >=1000 px,
  progress strip) + "Step n of 6 · <step>"; start roadmap = 4 of the 6 step
  names ("Choose a disk → Confirm its identity → Choose a method → Review and
  erase"), no Erase/Result; last step "Review and erase" blurred into the
  Erase stage; GTK, curses and plain console showed no roadmap; offline
  helper still had the pre-#130 roadmap.
- DECISION (one vocabulary): stages Preparation → Erase → Result everywhere
  (stepper, strip, spoken stage, roadmap, helper); steps inside Preparation
  keep the #130 names except `STEP_NAME_REVIEW` "Review and erase" ->
  "Review" (FR Vérifier, DE Prüfen, ES Revisar, IT Controllare): Review is
  the step before the Erase stage (#166) and must not say erase.
- WHAT CHANGED: `copy.roadmap_parts(path)` = ("Preparation (6 steps)",
  "Erase", "Result") from `JOURNEY_LABELS` + `len(PREPARATION_PATH)` (the
  header's "Step n of N" total); `splash_roadmap` joins them; new
  `ROADMAP_STAGE_STEPS` "{stage} ({count} steps)" (4 drafts). Roadmap added
  to the GTK splash (focusable label), curses and plain console splash.
  helper/index.html card now "Preparation (6 steps) → Erase → Result.
  Nothing is erased until you choose Erase now." Docs screens.md,
  translations.md.
- TESTS: new tests/test_stage_names_138.py (roadmap = header stages; one
  source: patching JOURNEY_LABELS moves roadmap, header caption and spoken
  stage together, step count follows the path; Review has no erase verb in
  5 languages; web preview + helper; consoles + GTK source; Tk splash
  roadmap vs header stepper canvas text). Updated test_step_progress_130.py
  (3 pins) and test_journey_stages.py (comment). New tests fail on 57bac5a.
- CHECKS: stage/step/journey/language/translation files 258 pass non-Tk;
  Tk cases 22 pass one by one; ruff, mypy --platform linux. Screens:
  scratch work138-scratch-20261103 shots-before (57bac5a) / shots-after (en
  800x600 all sizes, 1280x820; de). Per-file comparison of 180 related
  files vs 57bac5a (finished): no new failures from #138; the two new-only
  lines were environmental (docs/evidence absent in this worktree; a Tcl
  flake that passes alone).
- NOT VERIFIED: GTK/Orca speech, Linux pytest at 72 DPI, ISO/QEMU, native
  review.
- NEXT: run the comparison, push; hosted gate on the stack head (owner
  approval); merge after #137.

## BW-139-SETUP — Setup screen order: language, text size, keyboard (IMPLEMENTED LOCALLY; COMPARISON, HOSTED GATE, GTK/ORCA, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/setup-order-139` (stacked on
  `feat/stage-names-138` @ 126bd2a), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-139-20261103`. Backlog #139 (UI
  review item 13); #131/#140/#141/#142 coordination only (not changed).
- BASELINE (126bd2a): Tk showed language picker, then the "Check your
  keyboard" heading, lead and limits, then text size, then layouts and the
  check. Tab order was already language -> size -> layouts -> check, but
  visually text size sat inside the keyboard part. 800x600 body 585 px in a
  457 px view (standard), 830/437 (extra): the screen scrolls.
- CHOICE: reorder in one screen, not split. A split adds a seventh
  Preparation step and an extra Continue for everyone, renumbers the #130
  step bar and #138 roadmap, and reworks the Keyboard-layout detour; the
  reorder gives each job its own labelled section with matching Tab order.
- WHAT CHANGED: Tk `_text_size_section` (bold "Text size", segmented
  choices, hint) between the language picker and the keyboard title;
  KEYBOARD_LIMITS moved under the layout cards it describes. GTK: Text size
  and keyboard lead become focusable ATK headings in that order; limits
  after the layouts. Curses/plain: text-size note (graphical only) before
  the keyboard part; the console no longer prints "Choose a size... You can
  change it later." (it cannot). Web preview: same three sections. No copy
  added or translated. Docs screens.md.
- TESTS: new tests/test_setup_order_139.py (plain, curses, web preview, GTK
  source order; Tk section positions, Tab order, 800x600 fit at all three
  sizes). On 126bd2a all fail except Tab order (already correct there).
- CHECKS: new tests 10 pass (4 non-Tk + 6 one by one); ruff, mypy
  --platform linux. Screens: scratch work139-scratch-20261103 shots-before /
  shots-after (800x600 standard/large/extra incl. -bottom, 1280x820;
  report.txt with body height and Tab order: after 613/457 standard,
  extra scrolls as before, footer intact). Per-file comparison of 52
  related files vs 126bd2a: PENDING (queued after #136-#138).
- NOT VERIFIED: GTK/Orca run and speech, Linux pytest at 72 DPI, ISO/QEMU.
- NEXT: comparison, push; hosted gate on the stack head (owner approval).

## BW-140-KEYCHECK — Guided keyboard check (IMPLEMENTED LOCALLY; COMPARISON, HOSTED GATE, GTK/ORCA, REAL X/CONSOLE KEYMAPS, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/keyboard-check-140` (stacked on
  `feat/setup-order-139` @ 9d93be5), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-140-20261103`. Backlog #140 (UI
  review item 14); #131/#139/#155 coordination only.
- DESIGN: "Optional check: press the key labelled Z here." The active
  layout turns that physical key into a character; Z sits in a different
  place on QWERTY (bottom row), QWERTZ (top row 6th) and AZERTY (top row
  2nd), so one key separates the shipped families (`keyboard.check_key`,
  table `_FAMILY_LETTERS` by US-key position). Within QWERTY (us, gb, es,
  latam, it) letters and unshifted digits are identical — what the typed
  confirmation needs — so the match line promises only "letters and
  numbers". Results: match; other (suggest de / fr / the language's usual
  QWERTY else us) with one-click switch; unclear (another letter). Not one
  letter (Shift, dead keys, digits) is not an answer. Advisory: never
  switches by itself, never blocks Continue; a failed switch keeps the
  layout and shows the existing failure message.
- SURFACES: Tk reads the X keysym on <KeyPress> in the check box, shows the
  result (green/amber) and a Switch button, focus stays in the box. GTK
  reads Gdk.keyval_name, names the box with the prompt, shows the result as
  an ALERT label that takes focus (Orca speaks it), then the Switch button.
  Curses compares the produced character (keymap from loadkeys); result in
  the footer, F3 switches. Plain console: a single letter is checked, SWITCH
  switches. Web preview: same rule table from Python, aria-live result.
  KEYBOARD_LEAD now says "Then press one key below to check it."
- FILES: keyboard.py, wizard.py, copy.py, locales fr/de/es/it (8 strings +
  2 changed + lead; drafts), ui/tk_wizard.py, ui/accessible_wizard.py,
  ui/console_wizard.py, gallery.py; docs screens.md, screen-reader.md,
  translations.md. Tests: new tests/test_keyboard_check_140.py.
- CHECKS: new tests 69 pass (55 non-Tk incl. 7 layouts x 3 families, 14 one
  by one incl. simulated Tk key events for us/fr/de/gb/it and mismatches,
  800x600 at all sizes); on 9d93be5: 66 fail, 2 general guards pass, 1
  skipped. translation/language/keyboard_layout files pass; ruff, mypy
  --platform linux, node --check (en, de). Screens: scratch
  work140-scratch-20261103/shots-after (Z match, Y mismatch; 800x600 all
  sizes, 1280x820). Related-file comparison vs 9d93be5: PENDING (queued).
- NOT VERIFIED: real X keysyms under setxkbmap and real console keymaps on
  the live ISO (simulated events only here), GTK/Orca speech, Linux pytest
  at 72 DPI, ISO/QEMU, native review.
- NEXT: comparison, push; live-ISO keyboard check per layout in the QEMU
  worker (owner approval for hosted gate).

## BW-141-FINEPRINT — Keyboard-layout fine print behind Show more (IMPLEMENTED LOCALLY; COMPARISON, HOSTED GATE, GTK/ORCA, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/keyboard-fineprint-141`
  (stacked on `feat/keyboard-check-140` @ 7865ea1), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-141-20261103`. Backlog #141 (UI
  review item 15); Ref #50 (shared Show more).
- WHAT CHANGED: `copy.KEYBOARD_LIMITS` (wording unchanged) is no longer in
  the keyboard screen's main view. Tk: behind the shared `_more_link` Show
  more control under the chosen layout's note (Tab: layouts -> Show more ->
  check box; focus stays on it when toggled). GTK: collapsed Gtk.Expander
  "Show more" with a focusable, selectable label (Orca: "Show more,
  collapsed"). Web preview: the same `moreLink` disclosure. Curses/plain
  console (no disclosure control): printed after the layout list instead of
  before it; curses first 80x24 page no longer shows it, Up/Down reaches it.
  Docs screens.md, screen-reader.md.
- MEASURED (800x600 body height, before -> after): standard 613 -> 623
  (+10: the Show more control is taller than the one-line text it hides),
  large 815 -> 809, extra 864 -> 855. Less text either way; nothing clipped.
- TESTS: new tests/test_keyboard_fineprint_141.py (wording unchanged; plain
  and curses order/paging; GTK expander source; web preview disclosure; Tk
  hidden, Show more reveals and keeps focus, Tab order, 800x600 open and
  closed at all sizes). On 7865ea1 all fail except the unchanged-wording
  guard.
- CHECKS: 10 pass (4 non-Tk + 6 one by one); ruff, mypy --platform linux,
  node --check. Screens: scratch work141-scratch-20261103 shots-before
  (7865ea1) / shots-after (+report.txt). Related-file comparison: PENDING.
- NOT VERIFIED: GTK/Orca run and speech, Linux pytest at 72 DPI, ISO/QEMU.
- NEXT: comparison, push after #140.

## BW-142-BADGES — Layout number badges only with keyboard focus (IMPLEMENTED LOCALLY; COMPARISON, HOSTED GATE, GTK/ORCA, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/layout-badges-142` (stacked on
  `feat/keyboard-fineprint-141` @ a27ea6f), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-142-20261103`. Backlog #142 (UI
  review item 16); Ref #174 (keyboard-shortcuts help) not built in this repo,
  so the shortcut is documented in the screen's key hint and docs.
- WHAT CHANGED: Tk builds a 1-7 key-cap per layout card but packs it only
  while a layout card has keyboard focus (FocusIn shows; FocusOut re-checks
  where focus went), or once Up/Down or a digit chose a layout on this
  visit; reset on the next visit. Toggled in place (no redraw); card height
  unchanged. Fixed in passing: the card's existing FocusOut binding lacked
  add="+", which would have replaced the new one. HINT_KEYBOARD: "Up/Down or
  1–7 chooses a layout" (4 language drafts; "1–7" renders as a key-cap).
  Shortcuts unchanged and always active (digits outside the check box).
  GTK button names keep "1 QWERTY (US) (selected)". Web preview: CSS hides
  `.kbd` until `.layout-cards:focus-within`. Consoles unchanged (their
  numbers are the typed commands). Docs screens.md.
- TESTS: new tests/test_layout_badges_142.py (hint in 5 languages; GTK name
  source; preview CSS; Tk hidden by default, shown on card focus and hidden
  when focus moves to the check box, no height jump, each digit 1-7 still
  selects and reveals, Up/Down reveals, reset next visit, 800x600 fit with
  and without at all sizes). On a27ea6f: 19 fail, 1 guard passes (GTK
  names), 2 skipped.
- CHECKS: 22 pass (6 non-Tk + 16 one by one); ruff, mypy --platform linux.
  Screens: scratch work142-scratch-20261103 shots-before / shots-after
  (default and focused; report.txt counts mapped badges). Related-file
  comparison: PENDING.
- NOT VERIFIED: GTK/Orca run, Linux pytest at 72 DPI, ISO/QEMU, native
  review of the hint.
- NEXT: comparison, push after #141.

## BW-143-OWNERREASON — Explain the greyed Choose a disk on Owner (IMPLEMENTED LOCALLY; COMPARISON, HOSTED GATE, GTK/ORCA, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/owner-reason-143` (stacked on
  `feat/layout-badges-142`), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-143-20261103`. Backlog #143 (UI
  review item 17). Ref #178 (improved disabled-button style) is not in this
  repo: the existing DISABLED_BG/FG style is kept; adopt #178 when it lands.
- WHAT CHANGED: new `copy.OWNER_CONTINUE_REASON` "Tick the box above to
  continue." (4 drafts). Tk: label in the footer's right cluster, left of
  the greyed Choose a disk, wraps at ~1/3 of the column; ticking redraws
  without it. GTK: focusable label after the box (hidden once ticked) and
  the button's ATK description, both synced in the toggle handler (no
  redraw). Curses: the line above the Owner footer keys while unticked. Web
  preview: span beside the button + aria-describedby. Gate unchanged.
  Docs screens.md.
- TESTS: new tests/test_owner_reason_143.py (copy, 4 languages, gate
  unchanged, curses footer, GTK source sync, web preview, Tk beside/left of
  the button, gone when ticked and back when cleared, 800x600 fit at all
  sizes). On 70ffcdc: 11 fail, 3 general guards pass.
- CHECKS: 15 pass (9 non-Tk + 6 one by one); ruff, mypy --platform linux.
  Screens: scratch work143-scratch-20261103 shots-before / shots-after
  (unticked/ticked; en all sizes + 1280x820; de).
- NOT VERIFIED: GTK/Orca run and speech, Linux pytest at 72 DPI, ISO/QEMU,
  native review.
- NEXT: related-file comparison, push after #142.

## BW-144-POWERBADGE — Power status as a header badge (IMPLEMENTED LOCALLY; EXISTING-TEST RUN, COMPARISON, HOSTED GATE, GTK/ORCA, REAL HARDWARE, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/power-badge-144` (stacked on
  `feat/owner-reason-143`), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-144-20261103`. Backlog #144 (UI
  review item 18); Ref #165/#183 (erase-time power warnings) unchanged;
  Ref #175 coordination only.
- WHAT CHANGED: `power.PowerStatus.badge` -> PowerBadge(kind, text) with
  display (✓ only when plugged in) and spoken ("Power: …"): ac True ->
  ok "Plugged in"; ac False with a battery -> warn "On battery — plug in";
  ac None, no battery, complete -> neutral "Mains power"; anything else ->
  neutral "Power: unknown" (never plugged in when unknown). 5 strings, 4
  language drafts. `Wizard.power_badge` reads the cached monitor status
  (existing worker; never blocks). Tk: rounded badge after the brand in the
  header canvas; step caption/stepper start after it; header redrawn only
  when the badge changes. GTK: focusable label above the page on every
  screen, ATK name "Power: …", CSS class per state, updated in
  update_status. Curses: "[text]" appended to the header line when it fits
  (falls back to the short step form, never a second row). Plain console
  Owner prints the spoken badge. Web preview: header badge from the fake
  power scenarios. Owner (Tk, GTK, curses, plain, web preview) no longer
  shows the long power sentence; Review/Checking/Working/Stopping keep
  POWER_KEEP + the sentence. Splash: no header, no badge.
- TESTS: new tests/test_power_badge_144.py (9 power states, never plugged
  when unknown, text/spoken, 4 languages, monitor transition plugged ->
  battery with a slow driver not blocking, stale -> unknown, wizard
  follows monitor, curses header 80 cols, curses/plain Owner, GTK source,
  web preview payload, Tk badge per state, on Pick/Confirm/Method/Review,
  live unplug, Owner drops sentence while Review keeps its warning, header
  fits 800x600 at all sizes).
- CHECKS: 39 pass (25 non-Tk + 14 one by one); ruff, mypy --platform linux,
  node --check. Screens: scratch work144-scratch-20261103 shots-before /
  shots-after (owner per state at 800x600 and 1280x820; battery at
  large/extra). Existing power-related test files: RUNNING at commit time.
- KNOWN (from #140): keyboard.CHECK_KEY trips test_language_selection's
  swept-surface check; fix on #140 (EXCLUDED) and restack.
- NOT VERIFIED: real /sys power_supply on laptops and desktops (fake
  readings only), GTK/Orca speech, Linux pytest at 72 DPI, ISO/QEMU, native
  review.
- NEXT: triage the existing-test run, comparison, push after #143.
- 2026-11-03 EXISTING-TEST RUN: the single run of 21 power-related files
  died part-way (no summary); redone per file, e6ff9c4 vs 159dbe4.
  One real difference: test_laptop_power_ui expected the long power
  sentence on WHAT/OWNER (Tk label, curses "12%"/"Low battery"); those
  screens now carry the header badge -> the WHAT/OWNER cases check the badge
  (Tk header text, header-only redraw keeps focus and draw generation;
  curses "[On battery — plug in]"); the lid/power reminder is still checked.
  30 native cases one by one + console cases pass. finish_sound Tk case:
  flaky on the base only.

## BW-145-TEASER — One-line report notice on Owner (IMPLEMENTED LOCALLY; COMPARISON, HOSTED GATE, GTK/ORCA, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/report-teaser-145` (stacked on
  `feat/power-badge-144` @ e6ff9c4), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-145-20261103`. Backlog #145 (UI
  review item 19); Ref #127 shipped (photo option leads), #135 panel;
  #25 confirm-before-discarding unchanged.
- WHAT CHANGED: `copy.REPORT_MEDIA_WHAT` (same key, new text): "Want a
  report? You can photograph a summary at the end, or save it to a second
  USB when asked." ("when asked" keeps the stick unplugged until the result
  screen; the full media rules stay in Need a report?). New LEARN_MORE,
  LEARN_MORE_REPORT_NAME, CON_REPORT_LEARN (4 drafts). Tk: one muted line in
  its own frame (no clipping at larger text) + ghost "Learn more" button
  opening the report help (Tab after the ownership box). GTK: label + body
  button "Learn more" named "Learn more about saving a report". Curses: the
  line + "R: learn more" (R already opens help on Owner). Web preview: line
  + link. Docs screens.md, translations.md.
- TESTS: new tests/test_report_teaser_145.py (exact copy, 4 languages,
  wanted report still confirms at shutdown, curses line and R, GTK source,
  web preview, Tk one line at 800x600 and 1280x820, Learn more by Tab +
  key opens help, fit at all sizes). Updated test_report_media_notice.py
  and test_report_usb_exfat_20261027.py: media rules now asserted in the
  report help, the Owner line asserts photo + "when asked". On e6ff9c4: 10
  fail; 4 general guards pass (#25 confirm, R opens help, fit large/extra).
- CHECKS: 15 pass (8 non-Tk + 7 one by one); ruff, mypy --platform linux,
  node --check. exFAT mount tests fail identically on e6ff9c4 (Windows:
  os.makedev, tmp perms). Screens: scratch work145-scratch-20261103
  shots-before / shots-after (en all sizes + 1280x820; de). Related-file
  comparison: PENDING.
- NOT VERIFIED: GTK/Orca run and speech, Linux pytest at 72 DPI, ISO/QEMU,
  native review.
- 2026-11-03 FOLLOW-UP: tests/test_translation_consistency_20261027.py
  paired REPORT_MEDIA_WHAT with REPORT_HELP_TITLE ("Need a report?"). The
  one-line text no longer cites that title (its Learn more link opens it,
  covered by test_report_teaser_145), so the pair is removed; 4 cases had
  failed on 7c0a793 (found by the #147 checks).

## BW-146-PLATFORMS — Platform bullet under Show more on Owner (IMPLEMENTED LOCALLY; COMPARISON, HOSTED GATE, GTK/ORCA, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/compat-showmore-146` (stacked
  on `feat/report-teaser-145` @ 7c0a793), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-146-20261103`. Backlog #146.
- WHY: in the live wizard the PC has already started from this USB, so
  "For 64-bit Intel/AMD Windows or Linux PCs that start from this USB. Not
  Apple Silicon Macs. Not Chromebooks." is pre-boot guidance. docs/claims.md
  checked: it is Amazon/pack listing copy (title + allowed bullet still say
  "Not Apple Silicon. Not Chromebooks."), with no rule placing it on any
  wizard screen; unchanged.
- WHAT CHANGED: copy.WHAT_BULLETS unchanged (still 3 items, still equals
  compat_story.PLATFORMS last, so translations/sweeps/helper injection are
  untouched). New render-time helpers copy.owner_bullets() (first two) and
  copy.owner_platforms_line() (the last), read at render time so a language
  switch follows. Tk: main box shows two bullets; the line leads the Show
  more panel's detail text. GTK: two-bullet label + a collapsed "Show more"
  Gtk.Expander with a focusable, selectable label (same pattern as #141).
  Curses/plain (no disclosure control): the line follows the supporting
  notes, just before "Check the box, then continue."; no longer a bullet.
  Web preview: payload `what` is two bullets, `platforms` leads Show more.
  Kept up front: helper/*.html (5 languages), desktop/web/index.html,
  desktop/main.go, desktop/readiness.go, docs/boot-card.md, README,
  docs/claims.md. Docs: screens.md row + Owner row; compatibility-matrix.md
  "every screen subtitle" corrected.
- TESTS: new tests/test_owner_platforms_146.py (split keeps all bullets and
  follows 4 languages; pre-boot pages/launchers/docs keep it; claims has no
  screen rule; curses + plain order; GTK expander source; web payload and
  Show more; Tk main view hides it at 800x600 and 1280x820, Show more by
  keyboard reveals it and keeps focus on the control, no clipping at all 3
  text sizes with Show more closed and open). Updated test_tk_runtime
  (min-size Owner: two bullets shown, platform line not) and
  test_accessible_runtime (bullet label text). On 7c0a793 the new file has
  9 failures (copy split, languages, consoles, web); pre-boot guards pass.
- CHECKS: new file 28 pass (18 non-Tk + 10 Tk one by one); ruff clean; mypy
  --platform linux: same 6 env-only errors as 7c0a793 (qrcode stubs, gi).
  Screens: scratch work146-scratch-20261103 shots-base / shots-new (en,
  800x600 standard/large/extra + 1280x820, main view and Show more scrolled).
  Related-file comparison (150 files vs 7c0a793): RUNNING
  (work146-scratch-20261103 pf-new-0x / pf-base-0x).
- NOT VERIFIED: GTK/Orca run and speech, Linux pytest at 72 DPI, ISO/QEMU,
  native translation review (no new strings).
- 2026-11-03 COMPARISON (150 files, aabf550 vs 7c0a793 archive): one real
  case, test_prepare_aftercare::test_console_what_wraps_prepare_bullets_at_
  80x24 (expected every WHAT_BULLETS word on curses page 1; the platform
  line now follows the notes) -> test now checks owner_bullets(). Reruns:
  modern_layout, ui_polish, language_first, owner_reason, last_chance pass
  on both (single-run Tk flakes). laptop_power_ui native redraw fails on
  both trees (inherited; see BW-144). physical_acceptance_111,
  secure_boot_expectations, evidence_tiers: worktree lacks docs/evidence
  files (environment, same as earlier tasks).

## BW-147-PARTNAMES — Partition names and file systems on Pick a disk (IMPLEMENTED LOCALLY, safety: commit; COMPARISON, HOSTED GATE, GTK/ORCA, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-03, Claude (Opus 5.5). Branch `feat/partition-names-147` (stacked
  on `feat/compat-showmore-146` @ aabf550), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-147-20261103`. Backlog #147 (UI
  review item 21); coordinates with #149 (one-line rows: the summary is one
  line) and #154 (BitLocker/LUKS named "BitLocker encrypted"/"LUKS
  encrypted"; nothing else of #154 implemented).
- WHY: cards said "Partition · 1 GB; Partition · 256 GB". lsblk already
  returns LABEL, PARTLABEL, FSTYPE, FSVER, PARTTYPE, PARTTYPENAME
  (LSBLK_COLUMNS unchanged), but only LABEL reached the screen.
- WHAT CHANGED (display only): models.VolumeFacts + ExcludedDevice.volume.
  discover.py: one kwarg, `node=node`, passed to inventory.excluded_device in
  the exclusion loop after selectable/eligible_paths are fixed (safety:
  commit). inventory: clean_volume_text (NFKC, drop C* incl. bidi/zero-width,
  whitespace -> space, quote marks -> ', <=2 stacked marks, 24-char cap with
  …), volume_facts, format_name, roles from PARTTYPE/PARTTYPENAME only (EFI
  system, Microsoft reserved, Recovery; PARTLABEL never a role; default GPT
  names ignored), "Windows" for the single unnamed NTFS/BitLocker partition
  beside MSR/WinRE, contents_summary (largest first, 2 shown + "+N more",
  3 shown when only one would hide, components with reasons never folded).
  card_nesting_text = intro + one summary line; Tk dense line likewise; GTK
  adds the summary to the disk button's accessible name (plain-text label
  kept, focusable); curses/plain via card_nesting_text; web preview payload
  key `contentsSummary` (escaped with esc(); payload "<" escaped). 8 new
  inventory strings, FR/DE/ES/IT drafts. Demo fixture demo_lsblk.json gains
  fstype/fsver/labels ("Work"/"Photos" NTFS, FAT32, ext4) that classify only
  as `data` (no visible contents hint or warning change). Docs: screens.md
  row, translations.md.
- TESTS: new tests/test_partition_names_147.py: fixtures with Windows
  (EFI/MSR/NTFS/WinRE) -> "Windows (NTFS) 237 GB · Recovery 1 GB · +2 more",
  BitLocker + LUKS, ext4/swap/EFI, unlabeled no-FS -> "Unknown format 32 GB",
  boot USB; every role/format; Windows only with evidence and one candidate;
  reasons never folded; FR/DE strings; 13 clean_volume_text cases; 8 hostile
  labels quoted and still a normal target; control/bidi labels still drop
  the disk as before; preview escaping; GTK plain text; display-only proofs
  (volume_facts blanked -> identical error/boot/selectable/disks/excluded
  reasons; labels/formats removed -> same targets; safety/identity/runner/
  wizard never read the facts; nested components never selectable);
  rendering runs no command and inventory has no mount/blkid/subprocess;
  curses (<=80 cols), plain console, GTK accessible name, preview payload,
  Tk at 800x600 + 1280x820 and fit at all 3 sizes. Updated
  test_group_partitions.py, test_pick_row_fit_20261028.py (pinned a line per
  partition). On aabf550 the new file errors at collection (VolumeFacts).
- CHECKS: new file 52 pass (45 non-Tk + 7 Tk one by one); group/pick-row/
  contents-hint/snapshot-language files pass; ruff clean; mypy --platform
  linux same 6 env-only errors as baseline; node --check on preview script.
  Eligibility probe (4 lsblk fields x 13 hostile/edge labels incl. bidi,
  zero-width, newline, imitation, 60-char, HTML) on aabf550 vs new with the
  same fixture: byte-identical (error, boot, selectable, disks, excluded
  reasons). Screens: scratch work147-scratch-20261103 shots-before (demo) /
  shots-after (demo + rich fixture with hostile label, 800x600 all sizes,
  1280x820, scrolled); curses-after.txt. Related-file comparison (370 files
  vs aabf550): QUEUED. test_language_selection CHECK_KEY failure is the
  known BW-140 item (same on aabf550). test_translation_consistency
  REPORT_MEDIA_WHAT/REPORT_HELP_TITLE fails on aabf550 too: a #145
  regression, fix pending on the #145 branch (see BW-145).
- NOT VERIFIED: GTK/Orca run and speech (no gi on this host), Linux pytest at
  72 DPI / DISPLAY=:99, ./preview --web in a browser, ISO/QEMU, real lsblk
  on hardware (root FSTYPE availability), native translation review.
- FOLLOW-UP (not done): a whole-disk file system with no partition table
  shows no line; the full partition list behind "+N more" is not offered
  elsewhere (coordinate with #149).
- 2026-11-04 COMPARISON (370 files, 1b17458 vs aabf550 archive): one real
  case, test_prepare_aftercare::test_demo_disks_without_fstype_stay_unknown
  (demo disks now carry file systems) -> now asserts demo disks are `data`
  with the plain warning, and the same disks with FSTYPE/labels stripped
  stay `unknown`. Reruns: compare_disks, finish_sound, language_first,
  tk_callback_ownership pass (single-run Tk/tmp flakes);
  release_asset hard-link test flips between runs on every tree (release
  code untouched); release_manifest strict fails on both. Worktrees are
  sparse checkouts without docs/evidence (core.sparseCheckout `!/docs/
  evidence/`), which explains physical_acceptance_111,
  usb_verification_docs and live_session_power receipt failures. The
  laptop_power_ui owner case is the #144 test fix (8693532), not yet in this
  tree until the restack.

## BW-139..147-STACK — Restack after comparisons; branches pushed (HOSTED GATE, GTK/ORCA, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Per-file comparisons (#139-#143 340
  files, #144 power 21, #145 report 35, #146 150, #147 370) found five
  stale tests, each fixed on the branch that caused it, then the stack was
  rebased (record conflicts resolved by keeping both entries):
  #139 95131db (test_text_size follows _text_size_section), #140 192be9f
  (CHECK_KEY excluded from the language sweep), #141 6498ec7, #142 7324be0,
  #143 8365e4e, #144 89ef7d7 (laptop_power_ui checks the badge on
  WHAT/OWNER), #145 14e57db (stale REPORT_MEDIA_WHAT/REPORT_HELP_TITLE pair
  dropped), #146 448b13a (80x24 check uses owner_bullets), #147 = this
  commit's parent 7059361 + this note (demo disks are data; bare stay
  unknown). Remaining comparison differences are environmental: worktrees
  are sparse checkouts without docs/evidence; Windows tmp PermissionError,
  os.makedev, Tcl init, fork limits; single-run Tk flakes pass on rerun.
- On the restacked head: the five fixed files, the nine task test files and
  group/pick-row files pass non-Tk; every Tk case of the task files,
  laptop_power_ui (30) and test_text_size run one by one pass; ruff clean.
- Branches feat/setup-order-139, feat/keyboard-check-140,
  feat/keyboard-fineprint-141, feat/layout-badges-142,
  feat/owner-reason-143, feat/power-badge-144, feat/report-teaser-145,
  feat/compat-showmore-146, feat/partition-names-147 pushed (feature
  branches; ci.yml runs only on PR/push to main, so no hosted job).
- PENDING (owner): hosted ci.yml on the stack head before merge; GTK/Orca
  and Linux 72 DPI runs (not available on this Windows host); native review
  of FR/DE/ES/IT drafts; merge order #94 -> ... -> #147; nothing released.
- HOST: C: had 0 MB free during this work; only my scratch baselines were
  removed (about 2.5 GB free after). The rest of the 487 GB volume is not
  mine to touch; the owner may want to review it.

## BW-148-SERIALONCE — Show the serial once on Pick a disk (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Branch `feat/serial-once-148` (stacked on
  `feat/partition-names-147` @ 1a2dc42), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-148-20261104`. Backlog #148 (UI
  review item 22). Ref #129 (token marks on Confirm) unchanged; #152 and
  #177 are not in the repo or backlog: the existing [bracket] comparison
  mark is kept as the distinguishing-characters highlight.
- WHY: the card showed the serial (the whole serial in [brackets] when the
  same-size serials shared nothing) and the note repeated the characters:
  "Compare serial number characters 1 to 14: S4EVNX0N123456. Check the full
  ID before choosing." (the demo's two 256 GB disks).
- WHAT CHANGED (display only): inventory.serial_comparison: the note names
  positions only, COMPARE_SERIAL = "Compare {position} with other disks of
  this size. {reminder}" (no {span}); when nothing is shared at either end
  there is nothing to mark: no brackets, no note (the same-size warning
  stays). curses/plain console cards show marked_id ([brackets]) like Tk and
  the web preview. The plain console no longer prints the whole Compare
  disks list (which repeats every serial) before the cards: it prints
  "Compare disks (C): read only." and shows the list on C, like curses, Tk
  and GTK. GTK/Orca: the disk button name has the plain serial once; the
  character-by-character reader stays in the Compare disks expander.
  FR/DE/ES/IT COMPARE_SERIAL drafts without {span}. Docs: screens.md row,
  translations.md.
- TESTS: new tests/test_serial_once_148.py (22): fixture with shared-prefix
  pair, nothing-shared pair (review case), 55-char serials differing in the
  middle; note never prints the characters; no brackets/note when nothing
  is shared; announcement reads the serial once; every language's template
  has only {position}/{reminder}; display-only proofs (identity fields,
  confirm token, targets identical with/without comparison; only identity/
  inventory call serial_comparison; marked text never accepted as the
  token; countdown 5); curses at 40/80 cols, plain console once + C on
  request, preview payload, GTK source check; Tk at 800x600 x 3 text sizes
  and 1280x820 (serial once, wraps, no clipping). 13 fail on 1a2dc42.
  Updated test_serial_comparison.py (whole-span case), test_console_
  fallback_complete.py, test_console_parity.py (2) and
  test_slow_unusual_interactions.py (1) (curses search ignores the marks).
- CHECKS (Windows-native route): new file 22/22 (Tk one by one); ruff clean;
  mypy --platform linux same 6 env-only errors; related-file comparison 419
  files vs 1a2dc42 (scratch work148-scratch-20261104 pf-new/pf-base,
  cmp.txt, rerun.txt): the only real differences were the three console
  tests above (fixed, pass); every other new-only failure passed on rerun
  (Tk/Tcl flakes) or fails on 1a2dc42 too (sparse docs/evidence, Windows
  tmp permissions, release_manifest). Screens: shots-before/shots-after
  (demo + lookalike fixture with a 55-char serial, 800x600 x 3 sizes,
  1280x820), text-before/text-after.txt (console, GTK names, Tk text, EN/FR),
  console-after.txt (curses 80/40 cols, plain console with C).
- NOT VERIFIED: GTK/Orca runtime and speech (no gi here), Linux 72 DPI on
  DISPLAY=:99, ISO/QEMU, hosted ci.yml, native FR/DE/ES/IT review.
- FOLLOW-UP (not done, for #152): the span is computed over the whole
  same-size group, so one unrelated same-size serial removes the mark for a
  lookalike pair (e.g. S4EVNX0N123456 / S4EVNX0N123999 / WXYZ12 at 500 GB).
  A pairwise distinguishing span is #152's scope.

## BW-149-COMPACTROWS — One-line disk rows that expand when selected (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA, LINUX 72 DPI, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Branch `feat/compact-rows-149` (stacked on
  `feat/serial-once-148` @ 0b54fa4), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-149-20261104`. Backlog #149 (UI
  review item 23). Coordinates with #147 (summary on the collapsed row),
  #148 (serial once, on the expanded card); #150/#151 not implemented.
- WHY: at 800x600 only about 1.5 disk cards were visible (six-disk fake
  fixture: 1 of 6 whole at every text size; 2 at 1280x820).
- WHAT CHANGED: Tk `_compact_disk_row`: an unselected eligible disk is one
  line (radio, model, "kind · connection · contents hint · contents summary",
  capacity), labels wrap to their grid cell and never clip (no label
  border/padding; long tokens soft-broken). `_disk_row` keeps the full card
  for the selected disk and the protected Beamo USB (banner unchanged,
  Ref #61). The selected card gains a Compare disks link on its heading line
  when another eligible disk has the same displayed size; it opens the
  existing read-only comparison (`_comparison_opener`) and focuses its first
  reader. `_disk_heading` returns (row, model column). Selection logic is
  unchanged (wizard.select_disk / move_selection by path; rows in path
  order). Web preview: `compactDiskRow` for unselected disks and Up/Down on
  Pick moving the selection by path (its hint already showed the arrows).
  Status tags: the protected USB keeps its banner; not-selectable devices
  stay in Other detected devices with their reasons (no new strings).
  GTK/Orca and curses/plain consoles unchanged: every disk keeps its full
  identity (Orca reads one button at a time; the console pages), same
  path-based selection. Docs: screens.md #149 row (visible-row numbers),
  #148 row now says the serial is on the selected card.
- VISIBLE WHOLE ROWS (six eligible + same-size warning, nothing selected):
  800x600 Standard 6, Large 5, Extra large 4 (FR 6/4/2); 1280x820 6 at every
  size (FR Extra large 5). Selected at 800x600 Standard: 4-5; the fullest
  card (same-size note, hint, partitions, link) still leaves 3 while the
  warning is in view.
- TESTS: new tests/test_compact_rows_149.py (16): collapsed rows without
  serial; expanded card with serial/notes/partitions; protected USB full
  card; Down/Up select and expand; selection follows the disk after the
  discovery order is reversed, Down goes to the next path; click selects;
  boot USB never chosen; Compare link only with a same-size peer and opens
  the reader by keyboard; 6 rows visible / >=4 with a typical selection;
  long model wraps without clipping at 800x600 x 3 sizes and 1280x820;
  web preview source checks. 7 fail on 717322e (the other 9 are guards that
  also hold before). Updated: test_serial_once_148 (Tk), test_pick_row_fit
  (arrival = compact facts, roomy row = selected), test_ui_fit (first disk,
  contents hint), test_tk_runtime (serial marks/label on the selected card),
  test_design_runtime (identity on the expanded row; compact model wraps),
  test_group_partitions (partitions on the selected card),
  test_adaptive_layout helper (links inside the scrolling Pick list are
  exempt like the scrolling body; footer actions still checked).
- CHECKS (Windows-native route): new file 16/16 one by one; every changed
  Tk case one by one (ui_fit 50, pick_row_fit 24, serial_once 4, tk_runtime
  7, canvas_layout 1, group_partitions 1, design_runtime 2); per-case Pick
  subsets of adaptive_layout (42 pass), reflow (2 hangs on Last chance/
  Working, the known local hang), ui_fit, tk_runtime; 20 focused Pick files
  and 30 further Pick-touching files compared with #148: no difference
  (tk_input_scroll_pass13, warning_success, ui_polish also identical but
  one Tcl init glitch on a Method case);
  preview files: failures identical on #148/#147 (symlink, macOS, tmp
  permissions, hosted JS gate path); node --check on the preview script;
  ruff clean. CORRECTION (2026-11-04, found during #150): c3117cb added
  28 mypy arg-type errors (untyped **flat options to tk.Label in
  _compact_disk_row); the earlier "mypy same 6" was wrong. Fixed by the
  typing-only follow-up commit on this branch (flat: dict[str, Any]);
  mypy --platform linux is back to the same 6 env-only errors (gi,
  qrcode stubs). Environmental, fail on #148 too:
  tk_runtime pick_list_keeps_scroll_position_on_click (restore window
  closes before the canvas has a height on this loaded host),
  canvas_layout progress/modern_polish links (flow stops at Last chance),
  design_runtime result tab order (tmp PermissionError), ui_rework review,
  accessibility_lowres (2). Screens: scratch work149-scratch-20261104
  shots-before / shots-before-sel / shots-after (demo + six-disk fixture,
  nothing selected and nvme0n1/sda/sdc selected, 800x600 x 3 sizes,
  1280x820, FR) with visible.txt counts; web/ (headless Chrome 900x1100,
  before/after, nothing selected and first disk selected).
- NOT VERIFIED: Linux 72 DPI on DISPLAY=:99, GTK/Orca runtime, ISO/QEMU,
  hosted ci.yml, a browser keyboard run of the preview's Up/Down.
- FOLLOW-UP (not done): curses could use the same collapsed rows at 80x24;
  the preview's "ConnectionNVMe" (missing gap between label and value) is
  pre-existing (same on #148); with the selected card in view, Tk's
  ensure-visible can scroll earlier rows out (by design).

## BW-150-REVIEWACTIVATE — Double-click or Enter on a disk opens Review this disk (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Branch `feat/review-on-activate-150`
  (stacked on `feat/compact-rows-149` @ 54f8c81), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-150-20261104`. Backlog #150 (UI
  review item 24). Ref #149 (compact rows: the row a double-click starts on
  expands, so the second press is matched by disk, not by position).
- BASELINE: Tk Enter with a disk selected already ran continue_pick
  (focus lands on Review this disk); Tk double-click only selected (second
  and third press stayed on Pick); GTK disk buttons already did
  select_disk + continue_pick on activation (its "row-activated"); curses
  Enter and the plain console's number already reviewed; web preview Enter
  on a card only selected. HINT_PICK already says "Enter reviews this
  disk"; no copy changed (no translation or footer-fit churn).
- WHAT CHANGED (safety:, 7ade9ee; guard fix fbc4b44):
  - Tk: rows call `_press_disk(path, event)`. Two presses on the same disk
    (by path), within DOUBLE_CLICK_MS 500 and 8 px, where the first press
    selected it, call `_review_disk`, which runs the footer primary's own
    command (`_nav(wizard.continue_pick)`) only if that button is enabled.
    A second press on another disk (rows move when one expands) is a plain
    click on that disk. After the review opens Confirm, `_pointer_quiet`
    makes `_Button._press` and `_CheckRow._press` ignore presses for 500 ms
    (event time; monotonic fallback), so the rest of the double-click or a
    quick third click cannot press Back / Show more / any Confirm control.
  - GTK: `_select` (disk button activation) unchanged in effect; after a
    pointer activation that left Pick it sets `_pointer_quiet_until`, and
    every `button()` click ignores pointer clicks inside that window
    (Gtk.get_current_event type/time). Key and AT-SPI activations are never
    ignored.
  - Web preview: `reviewDisk(pointer)` is the footer action; Enter on a
    card reviews (repeat ignored), Space only selects, a click pair on the
    same card path within 500 ms / 8 px reviews; capture-phase listeners
    swallow mousedown/mouseup/click/dblclick for 500 ms after.
  - Unchanged gates: continue_pick clears the token and authorization;
    unconfirmable identity stays on Pick with AMBIGUOUS_IDENTITY; boot USB
    card and Other detected devices never chosen; Enter in that reader is
    swallowed.
  - Docs: screens.md #150 row; accessibility-lowres-matrix Pick row.
- ALSO (#149 defect found here, 54f8c81 on feat/compact-rows-149): c3117cb's
  untyped `**flat` Label options caused 28 mypy arg-type errors; typed as
  dict[str, Any]; BW-149's "mypy same 6" corrected in its entry.
- TESTS: new tests/test_review_on_activate_150.py (22): Tk double-click at
  800x600 and 1280x820 opens Confirm only (empty token, no authorization,
  no erase, Confirm continue still refused); typed token never carried
  over after Back; second press on another disk only selects; slow / moved
  presses are two clicks; double-click is the footer action (disabled
  button = nothing); tail of the double-click cannot press Back or Show
  more, both work after 500 ms; unconfirmable disk shows the reason; boot
  card never chosen; Enter reviews once, X11 repeat pair cannot act again;
  Enter on unconfirmable shows reason; Enter in Other detected devices does
  nothing. GTK via fake gi (real button()/_select): pointer click reviews,
  sets the window, tail click ignored, key/AT-SPI never ignored, later
  clicks work, token reset, unconfirmable stays with reason. curses: Down +
  Enter reviews, held Enter cannot act again; unconfirmable shows reason.
  Plain console: number = review. Preview: source checks and a Playwright
  run (Enter, Space, double-click; skips without Playwright/Chrome).
  8 fail on 02f2e74 (5 Tk, 2 GTK, 1 preview); the other 14 guard
  behaviour that already held.
- CHECKS (Windows-native route): new file 22/22 one by one (Playwright 2
  skipped: not installed here; hosted ci-hosted.sh installs it); ruff
  clean; mypy --platform linux 6 env-only errors (gi, qrcode stubs);
  node --check on the preview script; headless Chrome probe of the real
  preview page (web-probe-after.txt): Space selects, repeated Enter
  ignored, Enter -> confirm with empty token, double-click by path ->
  confirm, tail click on Back swallowed, click pair on two disks / moved
  8+ px / 700 ms apart only selects, Back works after the window.
  RELATED-FILE COMPARISON: 210 related files (scratch related-files.txt)
  run per file on 7ade9ee and 54f8c81 (pf-new.txt / pf-base.txt,
  cmp.txt): 13 failures only on #150, each rerun on both trees
  (rerun.txt). 3 were real: test_audit_20260908_wizard click tests built
  a fake _Button with no Tk, and the new guard caught only TclError
  (AttributeError). Fixed in fbc4b44 (safety:): the guard returns False
  unless a live wizard answers exactly True; the audit file and the #150
  Tk tests pass again. The other 10 fail the same way on #149 (Windows
  tmp PermissionError, Last chance timing on this loaded host) or pass on
  rerun (canvas_layout, modern_layout).
- SCREENS: scratch work150-scratch-20261104 before/ and after/ (demo, Tk
  800x600 and 1280x820 x Standard/Large/Extra large: pick-*, dblclick-*
  (before: still Pick; after: Confirm, empty token, button disabled),
  enter-*; probe.txt per state).
- NOT VERIFIED: GTK/Orca runtime and speech (no gi here; fake-gi test
  only), Linux 72 DPI on DISPLAY=:99 with a real X server double-click,
  ISO/QEMU, hosted ci.yml (Playwright cases), a real-mouse double-click in a
  browser (synthetic events only).
- FOLLOW-UP (not done; separate safety item, needs owner decision): a fast
  double-click on a footer button can also press the next screen's button
  under the pointer. Verified on Tk at 800x600 (scratch footer_dbl.py, same
  on 54f8c81): Confirm (token typed) "Choose erase method" double-click went
  CONFIRM -> METHOD -> LAST_CHANCE, skipping the Method screen; the 5 s
  countdown still held (Erase now disabled). Pre-existing, every screen;
  GTK likely similar (not run). The #150 pointer guard could be applied to
  every screen-changing pointer activation; not done here because it
  changes all footer buttons and many existing flow tests.

## BW-151-DISKORDER — Disks listed internal first, then external, stable order (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Branch `feat/disk-order-151` (stacked on
  `feat/review-on-activate-150`), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-151-20261104`. Backlog #151 (UI
  review item 25). Ref #149 (compact rows; Up/Down by disk identity).
- BASELINE: every view sorted eligible disks by device path (Tk rows,
  GTK buttons, curses blocks, plain console numbers, Compare disks "Disk
  N", wizard Up/Down, web preview JS). Mixed fixture (scratch
  fixture-mixed.json): NVMe SK hynix, USB WD Elements (/dev/sda), SATA
  Samsung, hot-plug SATA Toshiba, USB SanDisk: the USB backup drive was
  second, ahead of the internal SATA SSD.
- WHAT CHANGED (safety:, 1b14bdd; test follow-ups b370508, a4f9db0): new src/beamo_wipe/disk_order.py
  pick_order/pick_sort_key/location_group. Groups: 0 NVMe/SATA/SAS/virtio
  not removable/hot-plug; 1 the same transports hot-plug (dock, enclosure,
  hot-swap bay; location not guessed); 2 other eligible transports; 3 USB.
  Within: bus rank, model (casefold), serial, WWN, capacity, path. Used by
  Wizard.move_selection, Tk _pick, GTK pick buttons, curses _pick_blocks,
  plain console numbering, inventory.comparison_entries numbering, and the
  web preview (payload "order"; JS sorts by it). Selection, token and
  authorization unchanged: select_disk by path; _operation_key uses sorted
  identities (order-independent). Protected Beamo USB keeps its place.
  #149/#150 tests that assumed path order now use pick_order.
  Docs: screens.md #151 row; #149 row "device order" -> shown order.
  After (mixed fixture): NVMe SK hynix, SATA Samsung, hot-plug SATA
  Toshiba, USB SanDisk, USB WD Elements, identical in Tk (all sizes),
  curses, plain console, Compare numbers and Up/Down; same with lsblk
  order reversed. Demo: nvme0n1, sdd, sda (was nvme0n1, sda, sdd).
- TESTS: new tests/test_disk_order_151.py (28): mixed fixture order;
  location groups (12 cases); within-group key incl. ties to path; all 720
  permutations of the lsblk order give the same list; never adds/drops a
  disk; Check disks again with the same disks in reverse order keeps the
  order (and returns to Owner with no selection); re-sorting the list
  cannot change the chosen disk, its token or Confirm target; Up/Down step
  from the chosen disk in the shown order; a rescan in another order keeps
  the target and authorization key, countdown still governs Erase now;
  Compare "Disk N", curses (protected first), plain console numbers and
  number 5 choosing that disk; GTK loop and source checks; preview payload
  order and JS sort; Tk rows top-down at 800x600 and 1280x820, Down and
  click select by disk, protected card still after the list. With only the
  new module copied to 7ade9ee, 10 fail (all view/wizard order tests);
  without it all 28 fail at import.
- CHECKS (Windows-native route): new file 28/28 one by one; updated
  test_compact_rows_149 / test_review_on_activate_150 one by one: 16/16 and 22/22;
  ruff clean; mypy --platform linux 6 env-only errors (a loop variable in
  the plain console was renamed: the typed pick_order made mypy see a
  reused name); node --check; headless Chrome preview: cards, disks() and
  ArrowDown all nvme0n1, sdd, sda (web-order-after.txt).
  RELATED-FILE COMPARISON: 185 related files (related-151.txt) on #151
  against #150 (124 shared with the #150 run; 22 more run on #150 for a
  baseline, pf-base-extra.txt). Real: seven older tests assumed path order
  (test_zero_serial_identity_pass5, test_wizard_flow, test_compare_disks,
  test_slow_unusual_interactions x3, test_tk_runtime); they now take the
  order from pick_order (b370508, a4f9db0) and pass. Not caused by #151:
  test_audio_responsiveness timing limits (fails on #150 too / passes on
  one of three reruns on this loaded host), install-cloud-triggers bash
  10 s timeout, release_manifest (no ISO here), the #150 GTK fake-gi test
  (passes on rerun).
- SCREENS: scratch work151-scratch-20261104 before/ and after/ (mixed
  fixture, Tk 800x600 and 1280x820 x Standard/Large/Extra large) with
  order.txt (every view's order, reversed-lsblk check).
- NOT VERIFIED: GTK/Orca runtime and speech order (no gi here; source and
  fake-gi checks only), Linux 72 DPI on DISPLAY=:99, ISO/QEMU, hosted
  ci.yml, real hardware transports (eMMC/MMC, Thunderbolt, SAS) beyond
  fake lsblk.
- RISKS / NOTES: grouping trusts lsblk TRAN and RM/HOTPLUG (untrusted
  metadata); it only affects order, never eligibility, identity or
  authorization. A hot-plug SATA/NVMe bay inside the PC is listed after
  fixed internal disks (location is not guessed). eMMC (TRAN "mmc", bus
  "MMC") is group 2, after hot-plug internal transports and before USB.

## BW-152-SERIALDIFF — Bold and underline the serial characters that tell look-alike disks apart (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Branch `feat/serial-diff-152` (stacked on
  `feat/disk-order-151`), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-152-20261104`. Backlog #152 (UI
  review item 26). Ref #66 (distinguishing logic), #129 (Confirm token marks,
  unchanged), #148 (serial once; this closes its pairwise follow-up).
- BASELINE (scratch work152-scratch-20261104/before, fixture-lookalike.json):
  one contiguous [bracket] span from the group's common prefix/suffix:
  512 GB pair MX500A1B2C3/MX500A7B2C9 marked "1B2C3" (7-11) though only 7
  and 11 differ; 2 TB look-alikes ZFL0ABCD/ZFL0ABXD lost every mark because
  an unrelated Y7Q9KLMN had the same size; Tk drew brackets in an all-bold
  serial; note "Compare characters 11 to 14 with other disks of this size."
- WHAT CHANGED (safety:, 963c95c; test follow-up df97b81): inventory.serial_differences (replaces
  serial_comparison): pairwise against every same-size disk; strip shared
  prefix/suffix (per-character casefold, offsets preserved); same remaining
  length -> only differing characters, else the whole remainder; a peer
  sharing nothing is not a look-alike and adds no mark; union over
  look-alikes; shorter contained serial keeps SERIAL_LONGER; duplicates/
  missing/case-only unchanged (no marks). DiskIdentityView.comparison_marks
  (runs) with derived comparison_start/end, comparison_segments, marked_id
  ([brackets] per run). Tk: regular mono serial + bold copies with a 2 px
  underline placed over each run (wrap-aware; any text/height mismatch hides
  all marks). Web preview: <b class="diff"> (bold + underline) on a regular
  serial; payload serialMarks. GTK: Pango <b><u> on the disk button label;
  accessible name stays plain and includes the note. curses/plain console:
  [brackets] per run (terminal bold/underline can render as colour only).
  Note (visible + Orca): "Differs from the other 512 GB disk at characters
  7 and 11. Check the full ID before choosing." / "the similar 256 GB
  disk(s)". New keys COMPARE_SERIAL_OTHER, _SIMILAR_ONE, _SIMILAR_MANY,
  POSITION_MANY, POSITION_ITEM_RANGE, POSITION_AND; FR/DE/ES/IT drafts.
  Docs: screens.md #152 row (+ #148 row pointer), translations.md.
- TESTS: new tests/test_serial_diff_152.py (47): marks for 2, 3 and 4
  similar disks, two separate characters, different lengths (longer marks
  what the shorter lacks; inserted/longer middle), case-only, nothing
  shared; unrelated same-size serial no longer hides look-alike marks;
  exact notes (other / similar one / similar many, positions with runs);
  duplicates/missing/boot/other sizes unmarked; display only (id, token,
  confirmable unchanged; Confirm has token marks, no compare marks); every
  language's templates and placeholders; curses + plain console brackets;
  preview payload/CSS/markup; GTK markup via fake gi (escaped, bold+underline
  runs, plain text identical, note in the spoken text); Tk at 800x600 x 3
  text sizes and 1280x820 for a 2-run, 1-run and wrapped 55-character
  serial: marks sit on the right characters, label is the plain serial in
  regular weight, a changed label text hides all marks; unmarked serial
  stays bold. 45 fail on d53f40f (2 guards pass). Updated:
  test_serial_comparison (multi-run, wording, preview), test_serial_once_148
  (wording, templates, function name), test_security_hardening_new (escaped
  pieces, span class).
- CHECKS (Windows-native route): new file 47/47 (GTK/Tk cases one by one);
  updated files pass except test_as_int_logs_on_malformed (Windows tmp
  PermissionError, environmental); ruff clean; mypy 6 env-only errors;
  node --check; headless Chrome DOM probe (web-probe-after.txt): marks
  ["1","3"] / ["3456"] / ["C"] / ["7"], weight 700, underline, base 400;
  unmarked serial stays 700.
  RELATED-FILE COMPARISON: 92 related files (related-152b.txt) on #152
  against #151 (81 shared with the #151 run; 11 more run on #151,
  pf-base-extra.txt). Real: test_canvas_layout's overlap check flagged the
  drawn mark copies (pick, 5 sizes) and test_serial_once_148 expected the
  bracketed serial in the Tk label (3 sizes); both updated in df97b81 and
  pass one by one. test_zero_serial_identity_pass5 was the #151 order
  test (fixed on #151). Flakes that pass on rerun: pick_row_fit
  en-800x600-selected, owner_reason_143 fit, power_badge_144 Confirm/
  Method/Last chance header.
- SCREENS: scratch before/ and after/ (Tk: nvme0n1 at 800x600 x 3 sizes and
  1280x820; sda, sdc, sdd, sde at 800x600), zoom-serial.png (before/after
  crops), web-after-sda.png, text.txt per run (EN/FR notes, curses lines).
- NOT VERIFIED: GTK/Orca runtime and speech (no gi; fake-gi markup test
  only), Linux 72 DPI with DejaVu Sans Mono (bold/regular advance assumed
  equal, as for the #129 mark), ISO/QEMU, hosted ci.yml, native review of
  the FR/DE/ES/IT drafts.
- NOTES: when two look-alikes' remaining parts differ in length the whole
  remainder is marked (e.g. A9B2C3D8 vs A1B2C3D4X marks 2-8); the
  same-size warning text ("Two disks are the same size") is pre-existing
  and unchanged with several same-size groups.

## BW-153-KEYHINTS — Arrow key-caps in ink, no stray period in hints (IMPLEMENTED LOCALLY; HOSTED GATE, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Branch `fix/key-hints-153` (stacked on
  `feat/serial-diff-152`), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-153-20261104`. Backlog #153 (UI
  review item 27). Ref #174 (not implemented here).
- BASELINE (scratch work153-scratch-20261104/before, web-before-*.png,
  web-hint-before-zoom.png): Tk (roomy windows) and the web preview render
  hint key names as caps. The ↑ ↓ caps used a font glyph: the UI font lacks
  it and the fallback came out thin and tinted orange (CSS colour was ink;
  Tk fg INK), unlike the bold ink Enter/Esc caps. HINT_PICK "Click a disk,
  or use Up/Down.  Enter ..." left a period 4 px after the ↓ cap in Tk ("use
  ↑ ↓ ."); HINT_CONFIRM "... then Enter." had the same. The scan of every
  HINT_* plus the other Tk footer texts in all five languages found only
  these two.
- WHAT CHANGED (696af15, not safety: copy/styling only): Tk _kbd draws
  arrow caps (↑ ↓ ← →) on a canvas in INK, height matched to a letter cap's
  label; _hint_bar packs a cap followed by punctuation with 1 px instead of
  4 px. Web preview renderHint draws arrow caps as currentColor SVG (role
  img, aria-label = the arrow) and marks a cap followed by punctuation
  kbd-hug (no margin). Copy: HINT_PICK "Click a disk, or use Up/Down to
  choose one.  Enter reviews this disk.  Esc goes back.", HINT_CONFIRM
  "Type exactly what we ask for, then press Enter to continue."; FR/DE/ES/IT
  drafts with no sentence ending on a key. GTK and consoles show key names
  as text (unchanged). Docs: screens.md #153 row; translations.md note.
- TESTS: new tests/test_key_hints_153.py (13): every language's hints and
  footer texts never put punctuation right after a key name; exact EN copy;
  Tk arrow caps are drawn canvases filled INK, letter caps INK, no typed
  arrow, equal cap heights; Keyboard hint draws left/right/up/down; Pick
  hint has no piece starting with "."; punctuation after a cap sits within
  1 px, a word keeps its gap; preview source (paths, currentColor, aria,
  hug, CSS); Playwright run (skips here). 11 fail on 33a324f (the 2
  Playwright cases skip).
- CHECKS (Windows-native route): new file 13/13 one by one (2 skipped);
  ruff clean; mypy 6 env-only errors; node --check; headless Chrome DOM
  probe: after, ↑ ↓ are SVG caps, same computed colour as Enter/Esc, no
  text node starting with "." after a cap.
  RELATED-FILE COMPARISON: 13 hint/footer/keyboard test files
  (related-153c.txt) per file on #153 and #152: identical results (no
  failure only on #153); failures common to both are environmental (see
  pf-new.txt / pf-base.txt). test_ui_fit_20261027 and test_adaptive_layout
  timed out as whole files on both trees, so they were run case by case on
  #153 (each-fit.txt): ui_fit 262/262; adaptive_layout 93/94, the one case
  (test_extra_large_text_keeps_actions_at_800x600) hangs on #152 too (the
  known local Last chance/Working hang), not from #153.
- SCREENS: before/ and after/ (Tk 1280x820 EN/FR Owner, Pick, Confirm,
  Method + zoomed hint crops, hints.txt piece lists for all languages),
  web-before/after-pick|confirm|keyboard.png, web-hint-before-zoom.png.
- NOT VERIFIED: Linux 72 DPI with DejaVu (the Tk arrows no longer depend on
  the font), hosted ci.yml (Playwright), native review of the FR/DE/ES/IT
  hint drafts, keyboard hint at 800x600 (plain text there, by design).
- PRE-EXISTING (not from #153): test_keyboard_layout::test_keyboard_hints_
  name_every_layout_shortcut fails on #149 54f8c81, #152, #153, #154 and
  #155 alike ("1–" in HINT_KEYBOARD, the language-neutral 1–7 cap). Needs
  its own item: either the test or the hint is out of date.

## BW-154-ENCTAG — Tag disks 'BitLocker (Windows encryption)' / 'Encrypted (LUKS)' (IMPLEMENTED LOCALLY; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Branch `feat/encrypted-tag-154` (stacked on
  `fix/key-hints-153`), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-154-20261104`. Backlog #154 (UI
  review item 28). Ref #147 (contents line, FORMAT_BITLOCKER/FORMAT_LUKS).
- BASELINE (scratch work154-scratch-20261104/before, fixture154.py): no
  view tagged encryption; only the #147 summary said "Windows (BitLocker
  encrypted) 510 GB" / "LUKS encrypted 998 GB". Observed, unchanged: a USB
  stick with only a BitLocker To Go partition is classified "Windows found
  on this disk" (discovery treats BitLocker as a Windows mark; pre-existing).
- WHAT CHANGED (ea575f5, test follow-up 65d77ac; feat: display only; no discovery, selection or
  identity change): inventory.encryption_tags(children) from the
  VolumeFacts.fstype lsblk already gave for partitions and opened volumes
  (any depth): "bitlocker" -> TAG_BITLOCKER "BitLocker (Windows
  encryption)", "crypto_luks" -> TAG_LUKS "Encrypted (LUKS)", both when
  both. Tk: in the compact row details after the connection; on the
  expanded card an outlined (1 px border, ink bold) tag row above the
  contents hint. GTK: label under the disk button and in its spoken name.
  curses + plain console: own line under the serial. Web preview: payload
  encryptionTags; compact details and .enc-tag pills on the card. FR/DE/ES/
  IT drafts. Docs: screens.md #154 row; translations.md note.
- DESIGN NOTE: a whole-disk file system (LUKS on the raw disk, no
  partition table) has no nested component and is not tagged. Tagging it
  needs the disk's own FSTYPE on Disk, which session_recovery serialises
  with an exact field set; left as a follow-up rather than widen this
  display item into discovery/recovery.
- TESTS: new tests/test_encrypted_tag_154.py (14): fixture with BitLocker
  (Windows), LUKS (Linux), plain NTFS, ext4, whole-disk LUKS, BitLocker To
  Go USB, and a disk with an opened LUKS volume plus BitLocker: exact tags;
  display only (same eligible set and tokens with FSTYPE stripped; only
  presentation modules read the tags); copy in every language keeps the
  product name and has no unlock/key/password/recovery words; curses +
  plain console lines; GTK source; preview payload/markup/CSS; Tk rows and
  card tags at 800x600 Standard/Extra large (EN, FR) and 1280x820, not
  clipped, no tag on an untagged card. All 14 fail on 5958278.
- CHECKS (Windows-native route): 14/14 (Tk cases one by one); ruff clean;
  mypy 6 env-only errors; node --check; headless Chrome DOM probe (web-probe-after.txt): rows for nvme0n1/sdd carry the BitLocker tag, nvme1n1 the LUKS tag, sda/sdb/sdc none; the selected card shows one enc-tag; web-after-pick.png shows both.
  RELATED-FILE COMPARISON: 20 related files (related-154.txt) per file on
  #154 and #153: test_partition_names_147's GTK source check expected the
  spoken-name line without the tag (updated in 65d77ac); its Tk summary
  case passes on rerun; test_design_runtime timed out as a whole file and
  per case is 56/57 with the known Windows tmp-permission result-tab case.
  The Confirm-related 109-file run (#156 vs #154) adds nothing new.
- SCREENS: before/ and after/ (Tk: nothing selected 800x600 Standard/Extra
  large and 1280x820; nvme0n1 selected 800x600 x 3 sizes and 1280x820;
  nvme1n1 selected), text.txt (tags, summaries, curses blocks EN/FR),
  web-after-pick.png.
- NOT VERIFIED: GTK/Orca runtime and speech, Linux 72 DPI, real lsblk
  output for BitLocker/LUKS on hardware (fake lsblk only), ISO/QEMU, hosted
  ci.yml, native review of the drafts.

## BW-155-LAYOUTHINT — Confirm shows keyboard help only after a wrong entry (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Branch `feat/confirm-layout-hint-155`
  (stacked on `feat/encrypted-tag-154`), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-155-20261104`. Backlog #155 (UI
  review item 29). Ref #140 (keyboard check), #156 (token comparison, not
  changed here).
- BASELINE (scratch work155-scratch-20261104/before): Confirm always showed
  "Keyboard: QWERTY (US) · Language: English" (every view, every state). A
  layout change from Confirm cleared the owner tick, the chosen disk and the
  entry and sent the owner back to Owner (_invalidate_after_layout_change_
  locked), which #155 asks not to do unless required. Curses Confirm had no
  way to open the layouts (K is typed into the token).
- WHAT CHANGED (safety:, 9ca6e1a):
  - Wizard: _confirm_mismatch, set by a complete non-matching entry
    (set_confirm_input) or continue_confirm on a non-matching non-empty
    entry; reset on each continue_pick. confirm_layout_hint = on Confirm,
    seen, and not matching. Display only.
  - Layout change opened from Confirm (_keyboard_from == CONFIRM): owner
    tick and selected disk kept, token unchanged (from the disk), a
    non-matching entry cleared, no authorization (none exists before
    Method), Esc/Continue return to Confirm. From any other screen: the
    previous full reset (Method/Last chance included; the apply/erase-claim
    race test still holds).
  - Tk: line removed; hint row (wrapping sentence + ghost "Change" button
    under it) packed only while confirm_layout_hint, synced on each
    keystroke and on Enter; Enter on Confirm now calls continue_confirm in
    every case (it moves only on a match); new _reveal_in_body scrolls the
    hint into view on short windows/large text (refactored the focus reveal
    into _apply_body_reveal; focus reveal behaviour unchanged).
  - GTK: hint label (focusable) + Change button, hidden (no_show_all) until
    a wrong entry; Enter in the entry records a wrong entry (never moves).
  - curses: hint + "F2: Change" after a wrong entry; F2 opens the layouts;
    Enter on a wrong entry records it. Plain console: hint after a wrong
    answer; K (already printed) opens the layouts.
  - Web preview: hint + Change (returns to Confirm), same keep/clear rule
    via layoutChanged(); the suggestion switch now resets like the wizard.
  - Copy: CONFIRM_KEYBOARD_LINE removed; CONFIRM_LAYOUT_HINT,
    CONFIRM_LAYOUT_CHANGE, CON_CONFIRM_LAYOUT_KEY + FR/DE/ES/IT drafts.
    Docs: screens.md #155 row; translations.md.
- TESTS: new tests/test_confirm_layout_hint_155.py (21): hidden while
  typing the right characters, shown after a complete wrong entry, stays
  while editing, hidden on a match; Enter/Continue on a short wrong entry
  counts and never advances; a new visit starts hidden; copy and every
  language; layout change from Confirm keeps owner/disk/token, clears a
  wrong entry, returns to Confirm and every later gate still applies
  (token, method, countdown, no erase); Esc returns to Confirm; a failed
  apply changes nothing; changes from Method/Last chance still start over;
  plain console and curses (hint, F2 opens layouts); GTK and preview source;
  Tk hidden/shown/hidden at 800x600 Standard/Extra large and 1280x820,
  Change opens the layouts, Enter on a short wrong entry shows it. 19 fail
  on 008ef12 (2 guards pass). Updated: test_language_first_131 (from
  Confirm keeps; new test: from Method still clears), test_language_
  selection (hint in every view).
- CHECKS (Windows-native route): new file 21/21 (Tk one by one); related
  keyboard files per case on #155 and #154: test_keyboard_check_140 69/69
  on both (an earlier fr-z-match failure was a flake); test_keyboard_layout
  88/89 on both, the same failure (test_keyboard_hints_name_every_layout_
  shortcut: "1–" found in HINT_KEYBOARD) which also fails on #149 54f8c81,
  i.e. pre-existing and not from #150-#156; ruff clean; mypy 6 env-only errors; node
  --check.
  RELATED-FILE COMPARISON: 109 Confirm-related files (work156-scratch
  related-156.txt) per file on #156 (which contains #155) and #154: the
  only failure only on #156 is a #152 Tk mark case that passes on rerun.
  Six files timed out as whole files on both trees; their Confirm cases
  run one by one on #156: ui_fit 42/42, reflow_large_text 2/2,
  single_erase_warning_128 33/33, adaptive_layout has none, tk_runtime
  18/19 with test_graphical_refresh_restarts_full_authorization[confirm]
  failing identically on #154 and #149 (refresh from Confirm now opens the
  guarded dialog first; pre-existing, not from #150-#156).
- SCREENS: before/ and after/ (Tk Confirm empty / complete wrong / short
  wrong + Enter at 800x600 Standard, Large, Extra large and 1280x820; FR
  Extra large) with text.txt.
- NOT VERIFIED: GTK/Orca runtime and speech, Linux 72 DPI, a real X
  keyboard-layout switch (fake applier only), ISO/QEMU, hosted ci.yml,
  native review of the drafts.

## BW-156-TOKENFEEDBACK — Show which typed confirmation character is wrong (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-04, Claude (Opus 5.5). Branch `feat/token-feedback-156` (stacked
  on `feat/confirm-layout-hint-155` @ 9e94fc7), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-156-20261104`. Backlog #156 (UI
  review item 30). Ref #129 (card token), #155 (timing of the help).
- RULE (documented in docs/screens.md "Comparison (#156)", decided with
  #129 and unchanged here): safety.token_matches strips leading/trailing
  whitespace and compares case-insensitively; inner spaces count; no
  partial match; another disk's token never matches.
- BASELINE: after a wrong entry Confirm showed only the #155 keyboard hint
  (work155-scratch-20261104/after); no per-character feedback anywhere.
- WHAT CHANGED (safety:, 10e06dc; written as 8d0e09f on the pre-rebase stack): new src/beamo_wipe/token_feedback.py
  (display only): marks typed characters that differ from the token at the
  same position (spaces set aside and marked on their own), counts
  missing/extra, never prints an expected character. Wizard.confirm_feedback
  (#155 timing). Tk: typed value (mono, [brackets]) and problem line above
  the keyboard sentence, refreshed per keystroke. GTK: focusable label,
  spoken name without brackets. curses/plain console: two lines. Web
  preview: JS port (parity 72/72 with Python, parity.txt). Copy TOKEN_*
  + FR/DE/ES/IT drafts. Docs: screens.md, translations.md.
- TESTS: new tests/test_token_feedback_156.py (40): gate re-asserted (outer
  spaces accepted x5, inner spaces rejected x4, case rule, wrong/missing/
  extra rejected, another disk's token rejected); each of 4 wrong
  positions reported; several/missing/extra; stray space; match/empty ->
  none; never reveals expected characters (6 inputs); every language's
  placeholders; wizard timing; Enter on a short wrong entry explains and
  never advances; countdown 5 and separate Erase now unchanged; only the
  wizard imports the module and token_ok never consults it; plain console,
  curses, GTK source, preview source; Tk at 800x600 Standard/Extra large
  and 1280x820. The file fails at import on #155 (9ca6e1a; 05aba30 before the rebase), the module being new.
- CHECKS (Windows-native route): 40/40 one by one; test_card_token_129,
  test_confirm_layout_hint_155, test_console_confirm_repeat pass;
  test_wizard_flow happy_path fails on #150 too (Windows tmp
  PermissionError); its path-order test was a #151 leftover, fixed on
  feat/disk-order-151 (b370508); ruff clean; mypy 6 env-only; node --check;
  Python/JS parity 72/72.
  RELATED-FILE COMPARISON: 109 Confirm-related files (related-156.txt)
  per file on #156 and #154 (cmp.txt): the only failure only on #156 is
  test_serial_diff_152 Tk mark [sda, Large], which passes on rerun. Six
  files timed out as whole files on both trees; their Confirm cases one by
  one on #156 (each-confirm.txt): ui_fit 42/42, reflow 2/2,
  single_erase_warning_128 33/33, tk_runtime 18/19 with the pre-existing
  refresh-from-Confirm case (fails on #154 and #149 too);
  test_keyboard_layout per case 88/89 on #155 and #154 (pre-existing
  hint-shortcut case, fails on #149 too).
- SCREENS: work156-scratch-20261104/after (Tk Confirm empty / wrong /
  short + Enter at 800x600 x 3 sizes and 1280x820; FR Extra large).
- NOT VERIFIED: GTK/Orca runtime and speech, Linux 72 DPI, ISO/QEMU,
  hosted ci.yml, native review of the drafts.

## BW-157-CONFIRMSPACE — Balance Confirm and keep its card and warning in view (IMPLEMENTED LOCALLY; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `fix/confirm-spacing-157` (stacked
  on `feat/token-feedback-156` @ 5680c3e), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-157-20261104`. Backlog #157 (UI
  review item 31). Ref #128 (warning), #155 (help after a wrong entry),
  #156 (feedback).
- BASELINE (work157-scratch-20261104/before, metrics.txt): on roomy windows
  Confirm's block sat at the top with a large empty area under the entry
  (gap under the status 190 px at 1280x820, 391 px at 1920x1080, 16 px above
  the title); at 800x600 Extra large a wrong entry scrolled the #155 help
  into view and the #128 warning out of it.
- WHAT CHANGED (Tk only; no token, countdown, gate or copy change):
  Confirm centres its block on roomy windows with a spacer measured as if
  the wrong-entry help were showing, so nothing moves when it appears; short
  windows and larger text use tighter gaps (the warning keeps its full-size
  text); the #156 feedback moved into the status line right under the entry
  (a "!" mark and warning outline, not colour alone); the #155 reveal never
  scrolls the disk card or the warning out of view (`_reveal_in_body(keep=)`).
  Commit d55220e. FOLLOW-UP COMMIT (a123294): the status line kept a wrap
  length at the zone's full width although its pill shrinks to the text;
  test_reflow_large_text's card-wrap check failed on both Confirm sizes
  (passes on #156). It now wraps only when the text is wider than the room
  beside the icon.
- FILES: src/beamo_wipe/ui/tk_wizard.py, tests/test_confirm_spacing_157.py
  (new, 15 cases; 12 fail on 5680c3e), tests/test_token_feedback_156.py (Tk
  case reads the status line), docs/screens.md.
- CHECKS (Windows-native route): test_confirm_spacing_157 15/15;
  test_token_feedback_156, test_confirm_layout_hint_155 pass; ruff clean;
  mypy --platform linux clean. RELATED-FILE COMPARISON (#157 vs #156, 32
  files whole plus the Confirm cases of 6 big files, work157-scratch-20261104
  pf-*.txt / each-*.txt): only-on-#157 failures were
  test_card_token_129 Tcl-mark and test_refresh_guard_136 pick dialog (both
  pass alone), test_ui_rework review safe default (also fails alone on #156:
  the 5 s countdown ends during the slow test under load) and
  test_reflow_large_text Confirm x2 (real; fixed by the follow-up, which
  passes the reflow case plus #155/#156/#157 files; with the fix, Confirm
  cases one by one: ui_fit 42/42, reflow 2/2, single_erase_warning_128
  33/33, card_token_129 2/2, tk_runtime 18/19 with the pre-existing
  refresh-from-Confirm case; work159-scratch-20261105/fix157-each.txt).
  Pre-existing on both: tk_runtime refresh-from-Confirm.
- KNOWN, NOT CAUSED HERE: on this Windows host Review before erasing at
  800x600 Extra large never settles in Tk's idle loop (draws in 0.4 s, then
  root.update() does not return) on #156 and #157 alike — the recorded
  "Windows Tk idle-loop hangs (Review extra 800x600)". Linux 72 DPI not
  checked here.
- SCREENS: work157-scratch-20261104/before and after (Confirm empty / wrong
  at 800x600 x3 text sizes, 1024x600, 1024x768, 1280x720, 1280x820 x3,
  1280x1024, 1920x1080), metrics.txt.
- NOT VERIFIED: GTK/Orca runtime, Linux 72 DPI, ISO/QEMU, hosted ci.yml.
  Not pushed to main; merge order #94 -> ... -> #156 -> #157.

## BW-158-LIMITSLINE — One-line SSD limits under the method cards (PROPOSAL ONLY — OWNER DECISION REQUIRED; NOTHING IMPLEMENTED)

- 2026-11-05, Claude (Opus 5.5). Backlog #158 (UI review item 32). Branch
  `feat/method-limits-line-158` (no commits; @ d55220e), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-158-20261105` (clean; the
  measurement prototype was reverted). Scratch:
  `work158-scratch-20261105` (shots158.py; before/, opt-base/, opt-A/,
  opt-B/, opt-C/ with metrics.txt and screenshots).
- STATUS: the task requires explicit owner approval before implementing or
  merging anything that depends on the decision. No approval was available
  in the session, so it stopped at the proposal. Coordinate with #159
  (implemented after, below), #160, #161, #186.
- FINDING: the two acceptance criteria conflict on today's cards. At 800x600
  the title block and disk card take ~190 px and each method card was
  140–180 px, so no placement of the limits text alone puts all three cards
  above the fold. Baseline: the limits panel is already below the fold on
  every short window (800x600, 1024x600, 1280x720) and Quick zero was never
  fully visible at any measured size.
- OPTIONS MEASURED (SSD, Tk, before #159):
  A. As worded: one line directly under the cards. The line is never visible
     without scrolling at any size (fails Ref #18).
  B. One line between the disk card and the cards. Always visible at every
     size and text size; cards no better than today at 800x600.
  C. B plus compact unselected cards (title and sentence only). Line always
     visible; all three cards fully visible at 1280x720 and 1280x820, still
     not at 800x600 or 1024x768.
  D. Keep today's panel.
  #159 (title, sentence, time line) now shrinks the cards to 102–125 px,
  which is the prerequisite for any "all three cards above the fold" goal;
  B or C must be re-measured on top of #159 once chosen.
- RECOMMENDATION: B (line above the cards, full text under its Show more
  and "Storage limits (L)"), re-measured after #159; it is the only option
  that keeps the limits visible without scrolling at 800x600 and largest
  text (Ref #18).
- CLAIMS CHECK (for owner sign-off): the line "On SSDs, overwriting may not
  reach every hidden area." stays within docs/claims.md ("SSD results depend
  on the drive's controller"; "overwrites the storage the drive exposes"; no
  sanitize/secure-erase claim). The full storage.OVERWRITE_LIMITS text stays
  one action away. Open owner questions: is a one-line summary prominent
  enough for docs/method-and-storage-wording-validation.md's "prominent SSD
  limits"; HDD and unknown disks show a notice today too — keep a line for
  them ("Hidden or remapped sectors may remain.") or SSD/NVMe only.
- NEXT ACTION: owner picks A/B/C/D and confirms the claims wording; then
  implement on `feat/method-limits-line-158` rebased onto the #159 branch,
  with a `safety:`-free UI commit, tests and before/after screenshots.

## BW-159-METHODCARDS — Method cards show title, one sentence and a time line (IMPLEMENTED LOCALLY; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `feat/method-cards-159` (stacked
  on `fix/confirm-spacing-157` @ 595224a; commits 741e417 feat, 2a0fa29
  fix), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-159-20261105`. Backlog #159 (UI
  review item 33). Ref #158 (above), #160, #161.
- BASELINE (work159-scratch-20261105/before, metrics.txt): each card had
  five to seven lines (sentence, overwrite count, check, rough guide, extra
  note, Everyday limits note): 140–231 px tall. When the size was unknown
  the time guide was hidden, so cards could not be compared on time.
- WHAT CHANGED (presentation only; METHODS, argv, verification, gates and
  copy of existing strings unchanged; not a `safety:` change):
  * copy.method_time_line(method, disk): the existing cautious guide
    (progress.time_guide ranges, "not promised"), or the new
    TIME_GUIDE_UNKNOWN "Time depends on the disk." (FR/DE/ES/IT drafts).
  * Tk card: title + chip (Recommended / More overwrites / No check), the
    one sentence (Quick zero's says it does not check the result), and a
    clock + time line with that card's own Show more on the same row. The
    counts, check sentence, Three overwrites note and Everyday limits note
    open under it. Show more never chooses a method (Enter, Space or click;
    focus stays on it after the rebuild; opened details scroll into view
    without moving the card's top away). Clicking the card or 1/2/3 still
    chooses. Last chance still states the exact counts.
  * Web preview: same card; the choice (role=button) and the toggle are
    siblings, never nested; per-disk `methodTimes` in the payload.
  * GTK, curses, plain console: layouts unchanged; every method now has
    its time line (Orca name and visible line), unknown size included.
  * Docs: screens.md, progress-timing.md, accessibility-lowres-matrix.md,
    translations.md.
- RESULT (Tk 800x600..1280x820, all text sizes): cards 102–125 px (from
  140–231); at 800x600 Standard Everyday and Three overwrites are fully
  visible (was Everyday only), at 1280x720 all three.
- TESTS: new tests/test_method_cards_159.py (23): time line = guide when
  known; "Time depends on the disk." for 4 unknown-size cases, no disk and
  no estimate; translated, no digits; method mapping unchanged; Tk cards
  show only title/sentence/time for HDD, SSD and unknown; cards <= 120 px at
  800x600; Show more opens only its card, never chooses, keeps focus,
  closes; Enter and Space on it never advance; details scroll into view
  (Standard, Extra large); card click still chooses, gates unchanged; no
  clipping at 3 sizes with details open; plain console and curses show the
  unknown line; preview payload, sibling toggle, handler never sets the
  method. OLD-CODE: on d55220e 19 of the 21 cases then in the file failed
  (pf-base.txt; the mapping check passes by design); the two later cases
  (keyboard toggle, details scroll) need the new toggle. Updated:
  test_tk_runtime (method facts and the Everyday limits-note fit open the
  card's Show more first); test_ui_polish unknown-size case now expects
  "Time depends on the disk." with a clock on every card (2a0fa29).
- CHECKS (Windows-native route): test_method_cards_159 23/23 (Tk cases one
  by one); ruff clean; mypy --platform linux clean. RELATED-FILE
  COMPARISON (79 files whole, #159 vs #157 base d55220e, pf-new/pf-base
  .txt; Method cases of 4 big files, each-new.txt): only-on-#159 were
  test_ui_polish unknown-size (intended, updated), test_slow_unusual
  refresh loop (REAL: Check disks again called .clear() on the open-details
  set, which a partially built app lacks; fixed in 2a0fa29 by assignment,
  failure set of that file now identical to base), power_badge and
  step_progress header (pass alone), test_time_guide_other_views
  collection error (passes on rerun). Big files: ui_fit Method 20/20,
  reflow 2/2, tk_runtime 28/29 with refresh-from-Method failing on base too
  (with Confirm and Last chance). Post-rebase stack check on the #161 tip:
  new files of #157/#159/#160/#161 pass, reflow 4/4, ui_polish Method
  25/25; only the pre-existing test_ui_system selector failure (#144
  `.powerbadge`, see BW-160).
- SCREENS: work159-scratch-20261105/before, after (Tk Method for SSD, HDD,
  unknown size at 800x600 x3 text sizes, 1024x600, 1024x768, 1280x720,
  1280x820 x3; metrics.txt; cmpshots.py), web-before-*/web-after-*
  (preview 800x600 and 1280x900, closed and with Quick zero open),
  web-probe-after.txt, curses-unknown.txt.
- NOT VERIFIED: GTK/Orca runtime and speech, Linux 72 DPI, ISO/QEMU,
  hosted ci.yml, native review of TIME_GUIDE_UNKNOWN drafts. Not pushed to
  main; merge order #94 -> ... -> #157 -> #159.

## BW-160-EVERYDAYCAVEAT — Everyday 'checks only exposed storage' caveat off the main card (IMPLEMENTED LOCALLY; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `feat/everyday-caveat-160`
  (stacked on `feat/method-cards-159` @ 0205571; commit 18cfe5a), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-160-20261105`. Backlog #160 (UI
  review item 34). Ref #158 (proposal, owner decision pending), #159.
- CLAIMS CHECK: docs/claims.md and docs/storage-and-controller-limits.md do
  not require copy.EVERYDAY_LIMITS ("This checks only storage the disk
  exposes. It does not promise how long it will take. A saved report is not
  extra proof of hidden areas.") on the card. The method-selection warning
  they do require (storage_limits.OVERWRITE_LIMITS via the storage limits
  notice and "Storage limits (L)") stays on the Method screen, unchanged
  (#158's subject). A test pins both facts.
- BASELINE: original code — the caveat was the last paragraph of the
  Everyday card (work159-scratch-20261105/before/method-*-800x600.png);
  GTK showed it as a focusable label on the Method screen; the plain
  console appended it to Everyday's line (work160-scratch-20261105/
  console-before.txt); curses paged it after the choices. #159 had already
  moved it under the Everyday card's Show more in Tk and the web preview.
- WHAT CHANGED (presentation only; wording, METHODS, argv and gates
  unchanged): GTK puts it in a collapsed Show more expander (pattern of
  #141/#146) named "Show more: Everyday", label focusable and selectable;
  plain console prints "Everyday: <caveat>" after the three choices instead
  of inside Everyday's line. Curses unchanged (already paged after the
  choices, Up/Down to read more). docs/screens.md row.
- FILES: src/beamo_wipe/ui/accessible_wizard.py,
  src/beamo_wipe/ui/console_wizard.py, tests/test_everyday_caveat_160.py
  (new, 9), tests/test_accessible_runtime.py (expander asserted),
  docs/screens.md.
- TESTS: wording and claims facts; storage limits notice still on the
  Method screen; plain console line order; curses 80x25 first page keeps
  the choices and the caveat follows them; GTK source expander; preview
  caveat only in opened details; Tk caveat hidden until Show more at
  800x600 Standard and 1280x820 Large, method unchanged. OLD-CODE: on the
  original code (d55220e) the preview and both Tk cases fail; on #159
  (e270780) the plain console and GTK cases fail
  (work160-scratch-20261105/oldcode-*.txt).
- CHECKS (Windows-native route): 9/9 (Tk cases one by one); ruff clean;
  mypy --platform linux clean; console/copy/ui_system/language/method
  files pass except pre-existing failures that also fail on the original
  code: test_method_operation_copy evidence/report cases (Windows temp
  files) and test_ui_system::test_gallery_identity_selectors_cannot_clip
  (the #144 `.powerbadge` nowrap rule; FOLLOW-UP, not caused here: the
  gallery's identity selectors must either avoid nowrap or the test must
  exempt the header badge — decide with #144's owner).
- SCREENS: work160-scratch-20261105/after (Tk Method 800x600 Standard and
  Extra large, 1280x820: closed and Everyday open; metrics.txt says the
  caveat is hidden closed and shown open), console-before/after.txt.
- NOT VERIFIED: GTK/Orca runtime (gi unavailable on this host; the
  expander and its spoken name are untested at runtime), Linux 72 DPI,
  ISO/QEMU, hosted ci.yml. Not pushed to main; merge order ... #157 ->
  #159 -> #160.

## BW-161-RARELYNEEDED — Three overwrites tagged 'Rarely needed' with a Show more reason (IMPLEMENTED LOCALLY — COPY AWAITS OWNER SIGN-OFF; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `feat/rarely-needed-161` (stacked
  on `feat/everyday-caveat-160` @ cec9ecf; commit a8f2a2c), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-161-20261105`. Backlog #161 (UI
  review item 35). Ref #159.
- OWNER SIGN-OFF REQUIRED (task requirement; not yet given): the English
  copy below. Do not merge #161 until the owner approves it or supplies
  replacement wording; translations are drafts for native review.
  * Chip (replaces "More overwrites", which only repeated the title):
    "Rarely needed".
  * Show more explanation (methods.EXTRA_WORK_DOD): "Three times the
    overwrites of Everyday, so it takes longer. Extra passes do not reach
    hidden storage. Everyday is the usual choice. This is not a DoD
    certificate."
- CLAIMS CHECK: within docs/claims.md and docs/storage-and-controller-
  limits.md — "Extra passes do not reach hidden storage" is the existing
  approved sentence ("Additional overwrite passes do not fix these
  limitations"); "takes longer" is factual (4 full-disk passes vs 2);
  "This is not a DoD certificate." is docs/ADVANCED.md's wording (kept as
  required); no "DoD certified", certification, guarantee or
  unrecoverability claim. ES/IT first drafts "No es un certificado DoD" /
  "Non è un certificato DoD" read as "DoD certified" and failed
  test_language_selection; reworded to "El patrón DoD no supone ningún
  certificado." / "Il modello DoD non comporta alcun certificato."
- BASELINE: work161-scratch-20261105/before (Tk Method closed and with
  Three overwrites open: EN 800x600 Standard/Extra large, 1280x820, DE
  800x600, FR 1280x820 Large; metrics.txt), console-before.txt.
- WHAT CHANGED (copy and placement only; dodshort, rounds=1, verify=last,
  noblank, argv unchanged): methods.MARK_MORE_OVERWRITES ->
  MARK_RARELY_NEEDED; EXTRA_WORK_DOD reworded (EN + FR/DE/ES/IT drafts).
  Tk and preview show the neutral chip (not the warning colour) and the
  reason under the card's Show more (#159). GTK: the explanation left the
  radio label for that method's Show more expander ("Show more: Three
  overwrites", #160 pattern). Plain console: "[Rarely needed]" on the
  choice, "Three overwrites: <reason>" after the choices; curses: the
  paged note is prefixed with the method name. Docs: screens.md,
  translations.md.
- TESTS: new tests/test_rarely_needed_161.py (10): tag and wording;
  claims (ADVANCED.md sentence, "DoD" kept, Everyday named, forbidden
  phrases incl. ES/IT/FR/DE forms, every language); method mapping
  unchanged; plain console; curses first page and paged reason; GTK source
  (not in the radio label, in the expander); preview payload; Tk chip
  visible, neutral colour, reason only after Show more, no clipping (EN
  Standard/Extra large, DE). OLD-CODE (#160 @ 3910f41): 9/10 fail (the
  mapping check passes by design). Updated: test_ui_system chip text.
- CHECKS (Windows-native route): 10/10 (Tk cases one by one); ruff
  clean; mypy --platform linux clean; console, copy, ui_system,
  language (incl. ES/IT forbidden-claim checks), translation, gallery and
  method files pass except pre-existing failures that also fail on #160:
  test_ui_system selector (#144), test_export_worker_locale and
  test_language_snapshot (Windows subprocess/environment). Post-rebase
  stack check (all #157–#161 files) passes.
- SCREENS: work161-scratch-20261105/after (same states as before),
  console-after.txt; preview work159-scratch-20261105/web-after161-*.png.
- NOT VERIFIED: owner copy sign-off, GTK/Orca runtime, Linux 72 DPI,
  ISO/QEMU, hosted ci.yml, native review of the drafts.

## BW-162-COUNTDOWNCOPY — Review lead: 'Erasing starts only when you press Erase now' (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `fix/countdown-copy-162` (stacked
  on `feat/rarely-needed-161` @ bae2823; commit beab555 safety:), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-162-20261105`. Backlog #162 (UI
  review item 36). Ref #163 (not implemented here).
- BASELINE: copy.LAST_LEAD "Check the selected disk and method. The
  countdown never starts erasure." (FR/DE/ES/IT equivalents), read by Tk,
  GTK, curses, the plain console and the web preview payload
  (work162-scratch-20261105/before: Tk Review before erasing counting and
  at zero, EN 800x600 Standard/Large, 1280x820 Standard/Extra large, DE
  800x600, FR 1280x820 Large; metrics.txt).
- WHAT CHANGED (copy only; countdown, Erase now gate, argv unchanged):
  LAST_LEAD = "Check the selected disk and method. Erasing starts only
  when you press Erase now."; FR/DE/ES/IT drafts name each language's own
  Erase now label (Effacer maintenant / Jetzt löschen / Borrar ahora /
  Cancella ora). The helper page already says "Nothing is erased until you
  choose Erase now" (unchanged). Docs: screens.md, translations.md.
- FILES: src/beamo_wipe/copy.py, locales/{fr,de,es,it}.py,
  tests/test_countdown_copy_162.py (new, 13), tests/test_console_parity.py,
  tests/test_design_runtime.py, tests/test_tk_runtime.py (pinned the old
  sentence), docs/screens.md, docs/translations.md.
- TESTS: exact English lead; every language names its own BTN_ERASE and
  drops the old sentence; gate unchanged (zero enables Erase now, runner
  not started, still on Review); plain console; curses; GTK source and
  preview payload (EN, DE); Tk at 800x600 Standard/Large and 1280x820
  Extra large: lead shown unclipped, zero enables Erase now, nothing
  starts. OLD-CODE (#161 @ 5fa619c): 9/10 non-Tk cases fail (the gate check
  passes by design).
- CHECKS (Windows-native route): 13/13 (Tk cases one by one);
  test_design_runtime countdown, tk_runtime review/countdown (6),
  console_parity Last chance (4) pass one by one; ruff clean; mypy
  --platform linux clean; copy, ui_system, language, translation, gallery,
  confirmation-gate and curses erase-gate files pass except the
  pre-existing test_ui_system selector failure (#144, see BW-160).
- KNOWN, NOT CAUSED HERE: Review before erasing at 800x600 Extra large
  never settles in Tk's idle loop on this Windows host (recorded "Windows
  Tk idle-loop hangs (Review extra 800x600)"; reproduced on #156 and #157
  with the old copy). That state is left out of the new test and the
  screenshots; Linux 72 DPI still unchecked.
- SCREENS: work162-scratch-20261105/before and after (same states).
- NOT VERIFIED: GTK/Orca runtime and speech, Linux 72 DPI, ISO/QEMU,
  hosted ci.yml, native review of the drafts. Not pushed to main; merge
  order ... #157 -> #159 -> #160 -> #161 (after copy sign-off) -> #162.

## BW-163-COUNTDOWNREADY — Review ring shows a check mark and 'Ready', not '0' (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `feat/countdown-ready-163`
  (stacked on `fix/countdown-copy-162` @ f798714; commit e7d7e06 safety:),
  worktree `C:\Users\Jack\dev\BeamoTech\beamo-wipe-163-20261105`. Backlog
  #163 (UI review item 37). Ref #162.
- BASELINE (work163-scratch-20261105/before, metrics.txt): at zero the Tk
  ring showed "0" (PRIMARY) with COUNTDOWN_READY beside it; GTK only
  changed a plain label's text (no announcement); curses footer "Enter to
  erase."; plain console went straight to its ERASE prompt; preview ring
  "0".
- WHAT CHANGED (presentation only; countdown, gate, argv unchanged):
  copy.COUNTDOWN_READY_WORD "Ready", copy.COUNTDOWN_AVAILABLE "Erase now is
  available." (+ FR/DE/ES/IT drafts naming each BTN_ERASE). Tk: check mark
  drawn in the full ring, the number's window item hidden, "Ready" (bold,
  PRIMARY) packed above the caption only when ready and removed if the
  countdown restarts. GTK: an ALERT label "Ready. Erase now is available."
  hidden (no_show_all) until erase_enabled, then shown — no grab_focus, so
  focus stays on Back. curses footer "Ready. Enter to erase."; plain console
  prints "Ready. Erase now is available." before "Type ERASE to start".
  Preview: SVG check, "Ready" word, sr-only role=status line (best effort:
  the preview redraws each second). translation consistency now also
  checks COUNTDOWN_AVAILABLE and LAST_LEAD name BTN_ERASE. Docs:
  screens.md, translations.md.
- FILES: src/beamo_wipe/{copy,gallery}.py, locales/{fr,de,es,it}.py,
  ui/{tk_wizard,accessible_wizard,console_wizard}.py,
  tests/test_countdown_ready_163.py (new, 11), tests/test_design_runtime.py
  (was '0'), tests/test_translation_consistency_20261027.py,
  docs/screens.md, docs/translations.md.
- TESTS: copy in every language; gate unchanged; curses footer only when
  enabled; plain console line; GTK source (alert, no focus move, toggled by
  erase_enabled); preview payload/markup; rendered Tk ready state at
  800x600 Standard/Large, 1280x820 Extra large, DE 800x600 (check mark,
  hidden number, Ready above caption in view, no clipping, nothing
  started); restarted countdown removes Ready and the check mark.
  OLD-CODE (#162 @ f798714): 10/11 fail (the gate check passes by design).
- CHECKS (Windows-native route): 11/11 (Tk one by one); ruff clean; mypy
  --platform linux clean (a create_line overload error found and fixed
  before commit); related non-Tk files: failure set identical to #162 (9
  pre-existing export/cancel/evidence cases in
  test_accountable_audit_2026_09_03 and the #144 selector case); Tk:
  design_runtime countdown, ui_fit 40/40, review_visible, #162 Tk cases
  pass; tk_runtime 23/26 with refresh-from-Last-chance and both KP_Enter
  cases failing on #162 too; single_erase_warning_128 42/44 with the two
  800x600 Extra large Review cases hanging (known Windows Tk idle-loop
  hang, BW-162).
- SCREENS: work163-scratch-20261105/before and after (counting and ready:
  EN 800x600 Standard/Large, 1280x820 Standard/Extra large, DE 800x600,
  FR 1280x820 Large).
- NOT VERIFIED: Orca actually speaking the alert (GTK unavailable here),
  Linux 72 DPI, ISO/QEMU, hosted ci.yml, native review of the drafts.

## BW-164-REVIEWMETHODONCE — Review describes the method once (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `fix/review-method-once-164`
  (stacked on `feat/countdown-ready-163` @ 3beb2c2; commit d0415be safety:),
  worktree `C:\Users\Jack\dev\BeamoTech\beamo-wipe-164-20261105`. Backlog
  #164 (UI review item 38). Keeps #33's operation summaries intact.
- BASELINE (work164-scratch-20261105/before, console-before.txt): Review
  showed "One overwrite, followed by verification." and "Everyday: 1
  overwrite pass: random data. Then we check the last overwrite." on Tk
  (bold + muted; below the countdown when stacked), GTK, curses, the plain
  console and the web preview.
- WHAT CHANGED (presentation only; METHODS, argv, verification, gates
  unchanged): copy.REVIEW_METHOD_LINE "{method}: {operation}" (FR
  "{method} : {operation}"; DE/ES/IT drafts), Wizard.review_method_line =
  method title + #33's operation summary, e.g. "Everyday: One overwrite,
  followed by verification." / "Quick zero: One overwrite. Verification is
  not performed." Review shows only that line on every surface; Working and
  Done keep their method lines. Preview payload `reviewLine`.
- FILES: src/beamo_wipe/{copy,wizard,gallery}.py, locales/{fr,de,es,it}.py,
  ui/{tk_wizard,accessible_wizard,console_wizard}.py,
  tests/test_review_method_once_164.py (new, 18), test_console_parity,
  test_method_operation_copy, test_tk_runtime (method facts on Review),
  test_ui_rework, test_console_enter_interleaved_pass25_ui (mock gains
  review_method_line), docs/screens.md, docs/translations.md.
- TESTS: line per method incl. verification yes/no and no "verified" for
  Quick zero; every language keeps name + operation; plain console and
  curses show it once and no pass detail; GTK source; preview markup; Tk
  at 800x600, 1280x820, 1280x820 Extra large for Everyday and Quick zero:
  exactly one method line, no clipping, nothing enabled or started.
  OLD-CODE (#163 @ 3beb2c2): 18/18 fail.
- CHECKS (Windows-native route): 18/18 (Tk one by one); ruff clean; mypy
  --platform linux clean; non-Tk related files vs #163: only new failure
  was the pass25 mock lacking review_method_line (fixed); remaining
  failures identical to #163 (Windows /tmp/beamo-wipe permission cases in
  test_last_chance_operation / test_operation_identity, evidence and
  export cases). Tk one by one: ui_fit Review 124/124, single_erase_128
  Review (not Extra 800x600) 37/37, #163 Tk 6/6, ui_rework review 1/1,
  tk_runtime 27/30 with refresh-from-Last-chance and both KP_Enter cases
  failing on #163 too.
- SCREENS: work164-scratch-20261105/before and after (Review counting and
  ready, EN 800x600 Standard/Large, 1280x820 Standard/Extra large, DE
  800x600, FR 1280x820 Large), console-before/after.txt.
- NOT VERIFIED: GTK/Orca runtime, Linux 72 DPI, ISO/QEMU, hosted ci.yml,
  native review of REVIEW_METHOD_LINE drafts.
- QUEUE AT THIS POINT (owner prompts received, in order; each gets its own
  branch stacked on the previous): #165 curses Review focus (edit script
  ready in work165-scratch-20261105/edit_curses.py), #166 step name "Final
  check" (work166-scratch-20261105/edit_step.py), #167 Working start/finish
  times (owner question: the wall clock is never trusted today, so only the
  relative form would show), #168 keep the screen on during an erase
  (xset s off around nwipe via the SleepInhibit pattern; QEMU check
  blocked without an authorized isolated VM).

## BW-165-REVIEWENTERFOCUS — Enter on Review presses only the focused button on every surface (IMPLEMENTED LOCALLY, safety: commit; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, REAL TERMINAL, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `safety/review-enter-focus-165`
  (stacked on `fix/review-method-once-164` @ dbe5793; commit 1603a08 safety:),
  worktree `C:\Users\Jack\dev\BeamoTech\beamo-wipe-165-20261105`. Backlog
  #165 (UI review item 39), SAFETY-SENSITIVE. Ref #49 (Enter activates only
  the focused control), #162.
- CURRENT BEHAVIOUR DOCUMENTED (before):
  * Tk: Enter runs only the focused _Button's command; Review focuses Back;
    Erase now has takefocus=0 until enabled, then Tab reaches it; Enter on
    a focused disabled Erase now does nothing; with no button focused Enter
    does nothing; held/X11-repeat Return is claimed once.
  * GTK: on Review, Enter clicks only a focused, sensitive registered
    action; arrival focus is the warning label (no-op); Erase now is
    insensitive during the countdown; held Return/KP_Enter/Space repeats
    (same server timestamp) are swallowed.
  * curses: no focus. Once the ready frame was painted, a single Enter on
    Review called confirm_erase() (_handle); during the countdown Enter was
    ignored; held/repeated Enter needed a 1 s quiet gap. Footer "Ready.
    Enter to erase."
  * plain console: after the countdown it asks "Type ERASE to start:";
    anything else goes back.
- WHAT CHANGED (curses only; the wizard gate is unchanged): Review shows
  `[> Back <]    [ Erase now ]` (focus marked with > <, not colour only)
  and Tk's hint "Esc goes back. Tab to Erase now, then Enter after the
  countdown." Focus starts on Back and returns there on arrival, on leaving
  and whenever Erase now is not enabled (restarted countdown); Tab,
  Shift-Tab, Left and Right move it; Erase now takes it only on a painted
  ready frame. Enter presses the highlighted button: Back goes back (also
  during the countdown, as Tk/GTK), Erase now calls confirm_erase() only on
  a painted, enabled frame. _handle no longer erases on a bare Enter (fail
  closed). copy.CON_LAST_ERASE ("Enter to erase.") removed with its locale
  entries; the ready line is #163's "Ready. Erase now is available." Docs:
  screens.md, compatibility-matrix.md KB-07.
- FILES: src/beamo_wipe/ui/console_wizard.py, src/beamo_wipe/copy.py,
  locales/{fr,de,es,it}.py, tests/test_review_enter_focus_165.py (new, 16),
  tests/test_countdown_ready_163.py, tests/test_separate_footer_actions.py,
  docs/screens.md, docs/compatibility-matrix.md.
- TESTS: curses scripted loop (fake terminal, fake monotonic clock, erase
  starts recorded): Enter during the countdown -> back; Enter right after
  the countdown on default focus -> back; Tab then Enter -> one erase start;
  Shift-Tab/Left/Right likewise; Tab twice -> back; Tab during the
  countdown cannot reach Erase now; restarted countdown returns focus to
  Back; _handle never erases on 10/13/KEY_ENTER; footer text; plain console
  still needs ERASE. Tk: Enter during and right after the countdown ->
  back, Erase now not focusable while counting, Tab-focused Erase now +
  Enter -> erase. GTK (skips without gi): Enter on the warning or an
  insensitive Erase now does nothing; on a sensitive focused Erase now it
  starts. OLD-CODE (#164 @ dbe5793): the 8 curses behaviour cases fail
  (incl. the fail-closed _handle case); BTAB/LEFT/RIGHT, plain console and
  the Tk cases pass there by design (Tk/plain behaviour was already right).
- UPDATED EXISTING GATE TESTS (guarantees kept, key sequence adds Tab
  before the erasing Enter): test_curses_rendered_erase_gate_pass18 (the
  two launch arrivals; the early/crossing arrivals still launch nothing),
  test_curses_review_page_pass18_ui, test_curses_review_paint_pass6,
  test_console_key_origin_pass5 (S-after-start cases), test_preview (Review
  hint), test_countdown_ready_163 and test_separate_footer_actions
  (footer). Removed unused copy.HINT_LAST_CHANCE and CON_LAST_ERASE.
- CHECKS (Windows-native route): 16/16 (Tk/GTK one by one; GTK skips
  without gi); ruff clean; mypy --platform linux clean; 46 console/review/
  footer/gate files vs #164: no #165-only failure after the updates above
  (one test_keyboard_layout DE fit case failed under load and passes 20/20
  alone); Tk one by one: tk_runtime Review 23/26 with the same three
  pre-existing cases as #163/#164, separate_footer 3/3, #163 Tk 6/6.
- SCREENS: console-before.txt / console-after.txt (curses Review frame).
  The Tk/GTK Review is unchanged.
- NOT VERIFIED: GTK runtime (gi unavailable here), a real terminal's
  KEY_BTAB/Left/Right codes, Linux 72 DPI, ISO/QEMU, hosted ci.yml.

## BW-166-FINALCHECKSTEP — Header names Review as the final check (IMPLEMENTED LOCALLY; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `fix/final-check-step-166`
  (stacked on `safety/review-enter-focus-165` @ 2e1c48a; commit ef88356),
  worktree `C:\Users\Jack\dev\BeamoTech\beamo-wipe-166-20261105`. Backlog
  #166 (UI review item 40). Ref #130, #138.
- BASELINE (work164-scratch-20261105/before/last-en-standard-1280x820-*):
  the header said "Step 6 of 6 · Review" beside the stepper with
  Preparation highlighted.
- DECISION: "Final check", not the example "Final check before erasing":
  #138 decided (and test_stage_names_138 pins) that step names never use
  the erase verb because Review comes before the Erase stage. "Final check"
  says it is the last step; the stage stepper keeps Preparation (Review is
  still preparation per #130/#138). Owner may override the wording.
- WHAT CHANGED (copy only): copy.STEP_NAME_REVIEW "Final check" (FR
  "Dernière vérification", DE "Letzte Prüfung", ES "Última comprobación",
  IT "Controllo finale"; drafts). Header "Step 6 of 6 · Final check",
  spoken "Preparation, step 6 of 6: Final check.", same in curses, the
  plain console and the web preview (one source). Long translations still
  fall back to "Step 6 of 6" when they do not fit (existing rule).
- FILES: src/beamo_wipe/copy.py, locales/{fr,de,es,it}.py,
  tests/test_final_check_step_166.py (new, 10), tests/test_stage_names_138,
  test_step_progress_130, test_journey_stages, docs/screens.md,
  docs/translations.md.
- CHECKS (Windows-native route): 10/10 (Tk one by one); stage/journey/step
  files pass except test_journey_stages curses 80x24 Pick (fails on #160
  and #165 too); ruff clean; mypy --platform linux clean; language, ui_system,
  console files pass except the known #144 selector case; Tk step-bar
  header 9/17 with test_tk_long_translations_fit_at_800x600 x8 failing on
  #165 too (the #144 power badge's header text is not in that test's
  allowed list; FOLLOW-UP with #144).
- SCREENS: work166-scratch-20261105/after (Review header, same states as
  BW-163/164).
- NOT VERIFIED: Orca speech, Linux 72 DPI, ISO/QEMU, hosted ci.yml, native
  review of the drafts.

## BW-167-WORKINGTIMES — Working says when it started and when to come back (IMPLEMENTED LOCALLY; OWNER QUESTION OPEN; HOSTED GATE, GTK/ORCA RUNTIME, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `feat/working-times-167` (stacked
  on `fix/final-check-step-166` @ 4c3465b; commit 2d5bde9), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-167-20261105`. Backlog #167 (UI
  review item 41). Ref #36 (clock confidence), #132 (glance), #133.
- OWNER QUESTION (asked 2026-11-05, unanswered): may the OS clock ever be
  treated as trusted for Working's clock times? Existing logic never trusts
  it (evidence.wall_timestamps records os_utc/injected as "unverified"; no
  "verified" source exists). So the live USB shows the relative wording;
  the clock-time wording is implemented and tested behind
  Wizard.wall_clock_trusted (False; only an explicit True enables it).
- BASELINE (work167-scratch-20261105/before): the large time line was
  "About 50 minutes left" (validated estimate) or "Running for 12 minutes";
  an "Elapsed: …" note appeared with an estimate.
- WHAT CHANGED (presentation only; estimate gates, completion, evidence
  unchanged): ProgressView gains wall_now / wall_trusted; glance_time is
  untrusted: "Started 12 minutes ago · about 50 minutes left" (or just
  "Started 12 minutes ago" without an estimate, "· less than 1 minute
  left" under a minute); trusted: "Started 2:02 PM · expected around 3:05
  PM" (finish rounded up to 5 min; FR/DE/ES/IT 24-hour). Invalid monotonic
  clock hides the started part; unusable wall time falls back to relative.
  The Elapsed note is removed. One source for Tk (font_size_big), GTK
  (glance + paced Orca summary), curses, the plain console and the web
  preview. progress.GLANCE_RUNNING removed. Docs: progress-timing.md,
  translations.md.
- FILES: src/beamo_wipe/{progress,wizard}.py, locales/{fr,de,es,it}.py,
  tests/test_working_times_167.py (new, 9), test_working_glance_132,
  test_progress_timing, test_tk_runtime, docs/progress-timing.md,
  docs/translations.md.
- TESTS: untrusted with/without estimate and under a minute; trusted
  times, 5-minute rounding at and past the mark; unknown/broken clocks;
  no Elapsed note; DE/FR wording and every language complete; the live
  wizard never claims trust (and only True enables it) next to the
  evidence confidence logic; preview payload; Tk line in the large font for
  both. OLD-CODE (#166 @ 4c3465b): 9/9 fail.
- CHECKS (Windows-native route): 9/9 (Tk one by one); ruff clean; mypy
  --platform linux clean; glance/progress/language/console files pass
  except pre-existing failures that also fail on #166:
  test_progress_timing freeze-evidence and real-runner ETA cases (Windows
  tmp / SIGUSR1), test_gallery_working_focus_pass35_ui (renderPowerBadge
  missing from the extracted script, #144), test_ui_system selector (#144),
  tk_runtime keyboard_only_flow_reaches_working (needs a real start). Tk:
  working_glance_132 18/18, tk_runtime Working/timing 11/12.
- SCREENS: work167-scratch-20261105/before, after (untrusted), and
  after-trusted (flag set): EN 1280x820 with/without estimate, 800x600
  Standard/Large, DE 800x600, FR 1280x820 Large.
- NOT VERIFIED: Orca speech of the new line, Linux 72 DPI, ISO/QEMU,
  hosted ci.yml, native review of the drafts.
- QUEUE (owner prompts received, in order): #168 keep the screen on during
  an erase, #169 result-screen key hints, #170 report-status line only on
  failure, #171 compact result summary card.

## BW-168-SCREENAWAKE — Keep the screen lit while erasing (IMPLEMENTED LOCALLY; QEMU / LIVE X CHECK BLOCKED; HOSTED GATE, ISO BUILD, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `feat/screen-awake-168` (stacked
  on `feat/working-times-167` @ f3e6b72; commit 33a7278), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-168-20261105`. Backlog #168 (UI
  review item 42). Ref #39 (SleepInhibit), #132, #133.
- WHERE BLANKING COMES FROM: packaging/live/.../etc/X11/xorg.conf.d/
  10-beamo.conf (ServerFlags BlankTime 10, Standby/Suspend/OffTime 0) and
  the launcher usr/local/bin/beamo-wipe (`xset s 600 s blank s on`, `xset
  dpms 0 0 0`). DPMS never powers the panel down; the screensaver blanks.
- WHAT CHANGED: sleep_inhibit.SleepInhibit (the existing power helper the
  real NwipeRunner starts/stops around nwipe) now also runs `xset s off`
  when the erase starts and `xset s 600 s blank s on` (the launcher policy)
  when it stops, only if it turned blanking off. Live USB only, never dry
  run or preview, never without DISPLAY or /usr/bin/xset; DISPLAY and
  XAUTHORITY are passed explicitly into the clean subprocess env; timeout
  5 s; failures logged (power/display_blanking_change_failed) and never
  block the erase. DPMS, lid, suspend, power-button handling untouched.
  The "screen may go dark" note left Tk and GTK Owner and the web preview;
  curses and the plain console keep it (X settings cannot keep a Linux
  console lit). The offline helper keeps its sentence (blanking still
  applies outside an erase). OLED burn-in: considered; the Working screen
  changes over time (percentage, bar), and dimming is not available via
  xset, so no dim mode was added.
- FILES: src/beamo_wipe/sleep_inhibit.py, ui/tk_wizard.py,
  ui/accessible_wizard.py, gallery.py, copy.py (comment),
  tests/test_screen_awake_168.py (new, 11), tests/test_tk_runtime.py (Owner
  no longer shows the note), docs/live-session-power.md, docs/screens.md.
- TESTS: start runs `xset s off` with DISPLAY, stop restores the launcher
  policy once; argv only touches the screensaver; never runs when not
  live, in dry run, without DISPLAY or xset; xset OSError/timeout/non-zero
  never block the erase and nothing is restored; the note only in the
  console fallbacks and not in the preview; Tk Owner shows the power
  reminder without the note. OLD-CODE (#167 @ f3e6b72): 7/11 fail (the 4
  "never runs" cases pass by design).
- CHECKS (Windows-native route): 11/11 (Tk one by one); ruff clean; mypy
  --platform linux clean (a log_diag argument type error found and fixed);
  power/copy/language/console files pass except pre-existing failures also
  on #167 (test_live_session_power spawn case: Windows tmp; receipts case:
  docs/evidence excluded from this sparse checkout) and the #144 selector
  case; tk_runtime Owner 9/9.
- BLOCKED / NOT VERIFIED: the acceptance check "screen stays on during a
  long fake erase; blanking restored afterwards" needs a real X session in
  an isolated x86_64 Linux VM with a disposable target (no host-disk
  passthrough) and the CI image build; no isolated guest is authorized on
  this host (AGENTS.md), so it is pending. Hosted ci.yml not run.
- SCREENS: work168-scratch-20261105/before and after (Owner at 800x600,
  1280x820, 1280x820 Large; metrics.txt shows the note before/after).

## BW-169-RESULTHINTS — Result-screen key hints say exactly what happens (IMPLEMENTED LOCALLY; HOSTED GATE, LINUX 72 DPI, NATIVE REVIEW, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `fix/result-hints-169` (stacked on
  `feat/screen-awake-168` @ eb07f50; commit 58ef52d), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-169-20261105`. Backlog #169 (UI
  review item 43). Ref #174.
- BEHAVIOUR DOCUMENTED (before): Tk preview result: Enter runs the preview
  again (accept_done_keyboard -> reset_for_preview), Esc does nothing
  (back() is a no-op on DONE), hint "Enter continues. Esc goes back."; Tk
  live: Enter requests shutdown, Esc nothing, hint "Enter requests
  shutdown."; web preview result: default hint, Enter did nothing unless a
  button had focus; curses: "Enter: run again    C: close" (preview) /
  "Enter: shut down" (live), Esc nothing; GTK shows no key hints.
- WHAT CHANGED: copy.HINT_DONE_PREVIEW "Enter runs the preview again."
  (FR/DE/ES/IT drafts); Tk preview result uses it; the web preview result
  shows it and Enter (not on a focused control) runs the preview again,
  like its Run again button and the Tk preview; the stopped preview screen
  keeps its own hint. Live unchanged. No result screen offers Esc or a way
  back into a completed erase. Docs: screens.md.
- FILES: src/beamo_wipe/{copy,gallery}.py, locales/{fr,de,es,it}.py,
  ui/tk_wizard.py, tests/test_result_hints_169.py (new, 8), docs/screens.md.
- TESTS: copy in every language starts with Enter and never mentions Esc;
  back() is a no-op on a result (preview and live); preview Enter runs
  again, live Enter requests shutdown; curses footers; web preview hint and
  Enter handler (ignores focused controls); Tk preview/live hint rendered.
  OLD-CODE (#168 @ eb07f50): 3/8 fail (copy, web, Tk preview); the others
  pin behaviour that was already right.
- CHECKS (Windows-native route): 8/8 (Tk one by one); ruff clean; mypy
  --platform linux clean; preview/gallery/translation/language/ui_system/
  console/result/erase-another files: failure set identical to #168 (36
  pre-existing Windows/env cases).
- SCREENS: work169-scratch-20261105/before and after (Tk result screen,
  preview and live, 1280x820; metrics.txt has the hint text).
- NOT VERIFIED: Linux 72 DPI, hosted ci.yml, native review of the drafts.

## BW-170-REPORTNOTICE — 'Saving a report does not change the result' only after a failed save (IMPLEMENTED LOCALLY; HOSTED GATE, LINUX 72 DPI, MERGE PENDING)

- 2026-11-05, Claude (Opus 5.5). Branch `fix/report-notice-170` (stacked on
  `fix/result-hints-169` @ 0db2331; commit 4c6213a), worktree
  `C:\Users\Jack\dev\BeamoTech\beamo-wipe-170-20261105`. Backlog #170 (UI
  review item 44). Ref #96 (separation), #135 (report panel).
- BASELINE (work170-scratch-20261105/before): every report panel state
  (ready, failed/unavailable, saved) showed "Saving or checking a report
  does not change the erase result." (plus the unsaved-report warning when
  not saved); the web preview's report panel showed it too.
- DECISION: show it only after a failed save (report export or evidence
  save), where it reassures, rather than under Show more: it is one line
  and only useful at that moment. Not shown twice when the failure text
  (recovery.MEANING_REPORT_ONLY) already says it.
- WHAT CHANGED: report_panel.build_report_panel composes the notice: the
  reassurance only for failed / evidence / unavailable-after-error panels
  without that sentence already, the unsaved-report warning whenever not
  saved. Tk, GTK and curses already render panel.notice, so all follow; the
  web preview drops the line. Erase result and report panel stay separate.
- FILES: src/beamo_wipe/{report_panel,gallery}.py,
  tests/test_report_notice_170.py (new, 9),
  tests/test_separate_report_status.py (now expects the line only after a
  failed save).
- TESTS: absent from ready/saving/saved/unavailable views; the unsaved
  warning kept except when saved; after a failed report save (with and
  without Save offered) and an evidence failure it is said exactly once;
  preview panel has no notice; every surface renders panel.notice. OLD-CODE
  (#169 @ 0db2331): 7/9 fail.
- CHECKS (Windows-native route): 9/9; ruff clean; mypy --platform linux
  clean; test_separate_report_status passes except
  test_export_failure_then_retry_preserves_erase (Windows tmp
  PermissionError, pre-existing).
- SCREENS: work170-scratch-20261105/before and after (verified result,
  report idle / failed / saved, 800x600 and 1280x820; metrics.txt).
- NOT VERIFIED: Orca reading of the failure panel, Linux 72 DPI, hosted
  ci.yml.
