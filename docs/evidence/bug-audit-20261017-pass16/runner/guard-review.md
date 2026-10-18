# Pass16 fallback guard source review

2026-10-17; Codex delegate `/root/pass16_runner`; source-only orchestration review.
No CLI invocation, network call, credential read, process signal, product/test
edit or runtime campaign was performed. Product-source approval remains separate.
Initial exact hashes are in guard-initial-review-hashes.json.

## Offline command and guard scope

Installed `/usr/lib/google-cloud-sdk/lib/surface/meta/list_files_for_upload.py`
implements `Run` only by calling `gcloudignore.GetFileChooserForDir` with
`write_on_disk=False`, then yielding local paths from `GetIncludedFiles` with
`include_dirs=False`. The reviewed chooser reads local ignore files and walks
local directories; no API client, auth/login, upload, Cloud Build or remote
request is performed by that command. This is local ignore-rule acceptance,
not hosted CI or a publication operation. The command name's upload wording
must not be mistaken for actually uploading bytes.

The wrapper permits exactly three arguments, with exact first two tokens
`meta list-files-for-upload`. Extra flags, auth/config/compute/build/storage or
other remote commands are rejected before exec, with exit97 and a bounded log.
On the permitted branch it disables component update checks, usage reporting
and prompts, pins CLOUDSDK_PYTHON to the task's no-space interpreter alias and
execs absolute `/usr/bin/gcloud`. The retained wrapper and installed guard bytes
match. The seven other guards log their own path and exit97 unconditionally;
none forwards to the real curl/sudo/losetup/docker/qemu/gh/aws command.

run-gates.py prepends the private interpreter directory and then guard directory
to PATH, preserving pinned local Go. BEAMO_GATE_CHILD prevents dependency
installation; the selected nine phases contain no ISO/QEMU/native inventory,
hosted dispatch or publication phase. The unchanged repo test exercises only
this exact local file-listing command, sets CLOUDSDK_CONFIG to the sibling
`gcloud-config` fixture and creates inert files under pytest tmp_path/upload.

## Initial narrow guard objection

Initial wrapper proves only a lexical upload prefix plus sibling config parent
and name. It does not reject `..` escaping the canonical pytest root, or an
existing `gcloud-config` symlink pointing outside the private fixture. Therefore
that version does not itself establish the stated owned/private fixture-only
invariant, even though the intended unchanged test creates ordinary owned paths.
Root was notified before source approval. Required narrow correction: canonical
upload under the owned pytest root; private owned fixture parent; and absent or
private owned nonsymlink config at exactly the canonical sibling path. No
production source change is needed or proposed by this review.

## Execution history boundary

The retained attributed interrupt record identifies owned pytest PID36787,
start ticks751847/cwd/command, initial ignored SIGINT disposition, explicit
SIGTERM at2026-10-17T03:22:25.187569+00:00 and final owned-process cleanup.
No fresh main JUnit was produced and old main JUnit was rejected. That interrupted
run is not a pass and does not attribute the older pass8 event. Parent owns
subsequent runtime validation and receipts. Earlier interpreter-space fallback
attempts remain failure history; this source review does not relabel them.

## Final corrected guard approval

Root corrected the objection before restarting the full gate. Reviewed final
wrapper requires the upload argument to equal its canonical resolved path under
the resolved pytest root; the fixture parent must be owned by the current UID
and have no group/other permission bits. The upload is an owned directory with
an ordinary nonsymlink .gcloudignore. CLOUDSDK_CONFIG must equal exactly that
canonical parent's gcloud-config path and must not lexist: existing directories,
files and symlinks are all refused. Thus the permitted invocation starts from a
fresh private sibling config rather than reading an ambient credential store.
The unchanged fixture creates exactly this layout. The earlier guard objection
is resolved; initial hashes/history remain retained separately.

Final wrapper also sets CLOUDSDK_AUTH_DISABLE_CREDENTIALS=true in its own child
process environment and clears GOOGLE_APPLICATION_CREDENTIALS,
CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE,CLOUDSDK_AUTH_ACCESS_TOKEN and
CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT before exec. This changes no parent
session credentials/configuration. Installed SDK properties.py defines the
boolean auth.disable_credentials property; EnvironmentName maps it to exactly
CLOUDSDK_AUTH_DISABLE_CREDENTIALS. Reviewed optional credential-store accessors
and GetCredentialInfo return disabled before credential loading when this flag
is true. The allowed installed meta command itself has no credential/API call.
Update checks, usage and prompts remain disabled; the exact offline-only argv
allowlist and unconditional other-command rejection remain unchanged.

**No source-level objection to this exact guard/orchestration configuration.**
Final wrapper equals the installed guard byte-for-byte and the manifest
hashes all eight installed guards. guard-review-hashes.json authenticates final
wrapper, manifest, run-gates, seven deny guards, installed command/helper and
credential-property source inspected. This approval is bounded source evidence;
root owns positive/negative fixture traces, actual final gate outcomes and any
network/effect receipts. This delegate invoked no CLI, runtime or network and
changed only its review artifacts. Product-source bytes remain unchanged.
