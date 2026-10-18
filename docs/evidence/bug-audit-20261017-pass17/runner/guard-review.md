# Independent pass17 fallback guard source review

2026-10-17 / Codex `pass17_runner`. This child inspected source and metadata only:
no gcloud CLI, credential operation, runtime probe, process signal or network
request was executed. Product/test bytes were not changed for this review.

All eight installed private guard files match every path/digest pair in
`/tmp/pass17-primary/guard-manifest.json`, independently recomputed by sha256sum.
The copied manifest is `reviewed-guard-manifest.json`; all reviewed exact bytes
are authenticated by `guard-review-sha256.txt`. The directory and eight regular
files are UID0/mode0700. The no-space interpreter alias resolves to the existing
repository virtual environment; no interpreter installation is performed.

Seven guards (aws,curl,docker,gh,losetup,qemu-system-x86_64,sudo) consist only of
a bounded guard-path log, rejection message and exit97. Their common SHA256 is
`cba41168ef00df7373f4415f3de107c7b0ab47927121235609e4e5749c97c051`.
None forwards to a real executable. The gcloud wrapper SHA256 is
`a91cacf1cb44f2d32e58062682b1c33ce58ff8d3e808dc1162ae0de06a1603ec`.

The wrapper's sole permitted argv is exactly three arguments:
`meta list-files-for-upload <canonical-owned-pytest-upload-directory>`. It
requires an absolute upload argument equal to its resolved path beneath the
resolved `/tmp/pytest-of-root`, owned by the current UID, named `upload`, with a
regular nonsymlink .gcloudignore. Its fixture parent must be owned/private with
no group/other permission bits. CLOUDSDK_CONFIG must equal that canonical
parent's exact `gcloud-config` sibling and must not lexist, including broken
symlinks. All other command families, argument counts and paths reject before
exec. This is the same corrected authority boundary reviewed in pass16.

On that branch the wrapper itself disables credentials, update checks, usage
reporting and prompts; removes GOOGLE_APPLICATION_CREDENTIALS and Cloud SDK
credential-file, token and impersonation overrides; and pins CLOUDSDK_PYTHON to
the no-space alias. It then execs the absolute installed `/usr/bin/gcloud` with
only the already checked argv. The freshly absent private config prevents
reading the ordinary session's gcloud configuration. No auth/login, upload,
Cloud Build or hosted verification operation is allowed.

Installed primary source was independently read: surface/meta/
list_files_for_upload.py Run only selects local files via GetFileChooserForDir
with write_on_disk=False and GetIncludedFiles with include_dirs=False. The
reviewed chooser reads local ignore files and walks local paths; this command
does not perform API requests. SDK properties.py defines auth.disable_credentials
and maps it to CLOUDSDK_AUTH_DISABLE_CREDENTIALS; optional token/credential-info
accessors return early when set. The exact repository fixture writes ordinary
inert paths and .gcloudignore/.gitignore into its private upload directory and
sets the fresh sibling config. The chooser can follow local symlinks generally;
this reviewed fixture creates none, so the review is bounded to that layout.

The reviewed probe program intercepts os.execv and wrapper log opens; it checks
12 authority variants without allowing the actual CLI to execute. This review
does not invent a probe run result. The primary owns runtime receipts and final
forbidden-attempt logs. run-gates.py prefixes the no-space interpreter, then
these guards, retains GOTOOLCHAIN=local and BEAMO_GATE_CHILD=1, and selects only
the nine applicable local phases. Final JUnit paths are removed before that
phase so previous reports cannot supply a false pass. This is reviewed test
orchestration, not a universal OS network/device sandbox.

No source objection to this exact bounded configuration. Root must still
authenticate observed outcomes, source/config identity and guard receipts.
