# Release-note link correction — #121

2026-09-29, Codex. **Source correction prepared; public edit awaits approval.**
No push, hosted CI, tag change, publication or release-asset mutation occurred.

## Verified identity and cause

The affected public description is [Beamo Wipe v0.2.11](https://github.com/BeamoTech/beamo-wipe/releases/tag/v0.2.11),
numeric release ID `397823407`, published `2026-09-27T21:44:27Z`.
The annotated tag object is `6462d04d7706fdc53e2ab114ce48350388786ecd`;
both GitHub's tag API and local Git resolve it to
`662cf470f9fcedf710d897591560267575745fea`.
The latest release is v0.2.12; its two documentation links already use
v0.2.12 URLs and are outside this correction.

The public v0.2.11 body exactly matches the tagged and pre-edit working-tree
[`docs/release-0.2.11.md`](../../release-0.2.11.md). Its SHA-256 is
`40adde10ed3a63b31e91a85b36cfad5f8db014a8121a8330bed2cc3cd42021c0`.
[`publish-release-blacksmith.sh`](../../../scripts/publish-release-blacksmith.sh)
passes `docs/release-${BEAMO_WIPE_VERSION}.md` directly to `gh release create
--notes-file`; no link conversion is performed. It refuses replacement of
already-public releases and does not refresh the notes on an existing draft.

The same Markdown has two rendering bases. Repository rendering resolves
relative links beneath `docs/`; the public release renderer rewrites them
relative to the **tagged repository root**. Actual public HTML confirmed:

| Label, unchanged | Original Markdown destination | Public destination observed | HTTP |
| --- | --- | --- | --- |
| storage and controller limits | `storage-and-controller-limits.md` | `https://github.com/BeamoTech/beamo-wipe/blob/v0.2.11/storage-and-controller-limits.md` | 404 |
| release verification | `release-verification.md` | `https://github.com/BeamoTech/beamo-wipe/blob/v0.2.11/release-verification.md` | 404 |

## Exact correction

Only these two destinations change in the release-note source:

- [storage and controller limits](https://github.com/BeamoTech/beamo-wipe/blob/662cf470f9fcedf710d897591560267575745fea/docs/storage-and-controller-limits.md)
- [release verification](https://github.com/BeamoTech/beamo-wipe/blob/662cf470f9fcedf710d897591560267575745fea/docs/release-verification.md)

These canonical GitHub HTTPS URLs pin the matching release commit, avoiding
both default-branch drift and possible future tag movement. Neither original
link had an anchor; no anchor or label was added, removed or renamed. A
script reconstructed the corrected body by replacing exactly the two hrefs
and asserted byte-for-byte equality with the edited source. The proposed body
SHA-256 is `a9f5c891534f98d496c5868ef8aa2b75878be2bc6dedc66d1e1e5d050ff805c6`.

[The exact public-description patch](published-description.patch) is ready
for review. The complete proposed body is the source file linked above.
No other relative Markdown links exist in this release-note source or the
published body. There is no separate generated release-note copy/template.
The build's staged documentation is NOTICE/LICENSE/THIRD_PARTY/SOURCE;
release notes are not the offline USB guide. Local documentation files and
their own links remain unchanged and available offline in the checkout.

## Validation

[Scripted HTTP/rendering results](link-results.json) record every tested URL,
status, final URL, redirect history and document identity. Checks used bounded
HTTP GETs (10-second connection / 20-second read timeouts), HTML link parsing,
URL resolution and exact byte comparison with `git show v0.2.11:docs/<file>`.

- Public release page and original repository note rendering: HTTP 200.
  Both observed public links independently returned HTTP 404, no redirects.
- Both replacement GitHub document pages: **HTTP 200, no redirects**.
  Their raw GitHub contents are byte-identical to the tagged documents.
  The storage document's historical heading still says 0.2.10 in this tag;
  this task preserves that released document rather than rewriting history.
- Local `markdown-it` rendering and GitHub's non-publishing `POST /markdown`
  renderer produced identical target hrefs. Resolving each against both
  repository and release page URLs yields the same commit-pinned target.
  This is a faithful rendering check, not a claim that public text changed.
- `BEAMO_WIPE_DRY_RUN=1 python3 -m pytest -p no:cacheprovider -o addopts='' -q
  tests/test_release_signing.py tests/test_blacksmith_release.py
  tests/test_release_manifest.py`: **52 passed, 12 skipped in 2.27 s**.
  Skips are environment/artifact-dependent; no image build or full hosted
  qualification is claimed for this two-link documentation change.
- `git diff --check` passes. Final note diff has two changed lines only.
  Signed artifact bytes, checksums, tags, destination documents and workflow
  implementation are untouched.

[Release identity snapshot](release-identity.json) records body hashes and
asset IDs/digests. A second read confirmed the public body and every asset's
recorded metadata remained unchanged. No binary assets were downloaded.

Local base: `7e8603d588502fedce9206a735f924398d59b260`.
Branch: `codex/release-note-links-121`. The local commit containing this
receipt identifies the source correction (`git log -1 --format=%H --
docs/evidence/release-note-links-121/README.md`). Prior #120 work remains
on its own branch; the primary checkout's unrelated edits were preserved.

## Approval boundary

The user's #121 request explicitly requires approval before changing already
published text. The pending action is **only** replacing the body of release
`397823407` / `v0.2.11` with the reviewed source body above. It does not
authorize editing assets, tags, title, publication state or other releases.
Before applying, re-read the public body and require the original hash above;
if it changed, reconcile and re-review instead of overwriting new content.
After approval/application, re-fetch the public page and verify both rendered
hrefs and the proposed body hash. The local source correction alone does not
repair the already-published page.
