# Pull-request review enforcement audit — 2026-09-28

This is a dated, read-only audit of `BeamoTech/beamo-wipe` at `main`
`e986419379f512f8088f5982ee02a51dc91a9dae`. It does not assert that a
review requirement has been enabled. The policy is [CI and branch policy](../ci.md)
and [contribution guidance](../../CONTRIBUTING.md).

## Before settings

The repository default branch is `main`. The authenticated administrator was
`BeamoINT` (GitHub user ID `122241124`). Classic branch protection was present
and no repository or inherited ruleset applied to `main`. Read-only REST
`GET /repos/BeamoTech/beamo-wipe/branches/main/protection` returned the
following settings.

The 2026-09-28 15:14 UTC JSON response was also saved locally as
`/private/tmp/beamo-wipe-118-protection-before.json` (SHA-256
`f936ba9b57375d5b03db6a1b2349aec2d3378beac0a2bdb8d8e25759735c4bdc`).
The table is the durable settings record; the temporary copy may be cleaned up.

| Setting | Observed value |
| --- | --- |
| Required status checks | strict/up-to-date `true`; exact context `CI gate`, GitHub Actions app ID `15368` |
| Administrator enforcement | enabled |
| Required conversation resolution | disabled |
| Force pushes and deletion | both disabled |
| Required linear history; signed commits | both disabled |
| Required pull-request reviews | absent from the parent protection response |

GraphQL `branchProtectionRules` independently reported
`requiresApprovingReviews: false` and `requiredApprovingReviewCount: null`.
The review subresource `GET` returned default-looking fields including
`required_approving_review_count: 1`, but this does **not** establish an active
requirement: it conflicts with the parent protection response and GraphQL's
effective rule. No settings were changed in this audit.

The repository permits merge, squash, and rebase merges; auto-merge is enabled.
These settings are outside the proposed review change. The release workflow
and its separate publication authorization are also outside scope.

## Eligibility and policy gap

Read-only collaborator, organization-member, team, outside-collaborator, and
pending-invitation queries found only `BeamoINT` with repository write/admin
access, no teams, and no pending invitations. GitHub does not count an author's
approval of their own PR. Recent merged PRs, including #79, were authored by
`BeamoINT`; #78–#75 had bot `COMMENTED` reviews rather than approvals. Thus an
approval requirement with administrator enforcement and no eligible second
reviewer would stop the ordinary merge path.

The written policy required pull-request review but specified no count,
CODEOWNERS requirement, stale-review dismissal, last-push approval, bypass
actor, or emergency repository-change path. On 2026-09-28, the operator
confirmed one independent approval, retaining administrator enforcement and
the existing CI gate, with no new CODEOWNERS, stale-review, last-push, or
bypass rule. This decision is reflected in the local policy edit, but is not
yet active on GitHub. The operator requested a different approved review
process instead of naming an independent reviewer; that process and its
qualifying GitHub identity remain unspecified. On clarification, the operator
was unsure what alternative process to use. Do not enable the rule until a
write-capable non-author reviewer or an explicitly approved alternative
that GitHub can enforce is available. Do not weaken the existing `CI gate` or
administrator enforcement to work around reviewer eligibility. Draft PRs
cannot satisfy merge requirements until made ready.

## Alternative review paths checked

- The available Codex GitHub connector authenticated as `BeamoINT`, the same
  identity that authored the recent PRs; it cannot independently approve those
  PRs. Having a bot merely open a PR containing `BeamoINT`'s own changes would
  change GitHub's displayed PR author without providing independent review.
- The installed `greptile-apps` GitHub App has pull-request and contents write
  permissions, but its observed #78–#75 reviews were `COMMENTED`, not
  `APPROVED`. [Greptile's auto-approval beta](https://www.greptile.com/changelog)
  is limited to clean, low-risk PRs and excludes critical CI, infrastructure,
  security and similar changes; it cannot provide the sole qualifying path
  for every change in this safety-critical repository. No such approval
  configuration was changed here.
- [GitHub Copilot approvals](https://docs.github.com/en/copilot/concepts/agents/code-review)
  can count if explicitly enabled, but are a public-preview feature and off by
  default. The organization reported a Copilot Business plan with zero assigned
  seats; [unlicensed organization review](https://docs.github.com/en/copilot/concepts/agents/code-review#copilot-code-review-without-a-copilot-license)
  requires enabling paid AI-credit usage and additional policies. No current
  entitlement or approved sole-AI-review policy was established, so this is
  not an existing usable merge path.

An independent trusted reviewer with write access remains the narrowest
reliable path for the approved one-approval rule. Do not silently substitute
paid or automated approval for the operator's review-policy decision.

### Sole-maintainer clarification

The operator identified themself as `BeamoINT` and offered to be the trusted
reviewer of agent-proposed changes. Current `gh` authentication and the Codex
GitHub connector both use `BeamoINT`; local commits and recent PRs also carry
that account. GitHub therefore treats PRs opened through the available tools
as `BeamoINT` PRs, whose approval by `BeamoINT` cannot satisfy the rule.
Repository Actions settings report `default_workflow_permissions: read` and
`can_approve_pull_request_reviews: false`. No independent PR-authoring identity
or existing bot workflow was found.

Creating a workflow to open `BeamoINT`'s existing changes as a bot would require
changing the Actions PR-creation setting and would not establish independent
review of human-authored code. It would broaden the solution beyond the narrow
review setting and risk turning the author check into a naming formality.
[GitHub also says](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/review-copilot-output)
that the person who assigned a Copilot cloud-agent PR cannot supply its required
approval. A separately controlled PR author for actual agent-authored work, or
another trusted human reviewer for `BeamoINT`-authored PRs, must be identified
before enabling the rule. The operator then confirmed that no separate GitHub
identity exists. No bot workflow or Actions permission was changed.

### Agent-authored proposal route prepared after operator decision

The operator subsequently chose an agent-authored PR workflow with
`BeamoINT` as reviewer. The proposed `agent-pr.yml` runs only by manual
dispatch on `main` by `BeamoINT`. It accepts a `codex/*` source ref, its exact
commit SHA, and a changed evidence file. It refuses an advanced `main`, merges,
unrelated refs, missing evidence, submodules, prohibited image/key extensions,
and more than 500 changed paths. It replays the exact source tree onto the
dispatch commit, records the source SHA in the new commit and PR, and does not
approve or merge. The source checkout is treated as data: the publisher script
is copied from `main` to the runner's temporary directory before any proposal
files are loaded, and the App token is minted only after replay checks pass.
The job has a ten-minute bound and serializes duplicate source-SHA dispatches.

The proposed route uses a **dedicated GitHub App installation token** scoped
to this repository with Contents, Pull requests, and Workflows write
permissions. Workflows write is required only so a proposal changing a workflow
file can still be pushed and reviewed through the same protected path. The
short-lived token comes from an `agent-pr` environment intended to require
`BeamoINT` approval, using the
`BEAMO_AGENT_APP_ID` environment variable and
`BEAMO_AGENT_APP_PRIVATE_KEY` environment secret. The broad repository switch
that lets `GITHUB_TOKEN` create **and approve** PRs stays disabled. GitHub's
Pull requests write permission also permits review API calls; this workflow
does not make one, and the App key must be stored only in the dedicated
environment and never used for approval. Any workflow on `main` that enters
the same environment could request its secret after environment approval, so
the environment must require a deliberate `BeamoINT` review of each run. Since
`BeamoINT` initiates dispatch, GitHub's optional prevent-self-review switch
must remain off for this single-operator route; that is a residual trust
limit, not a second-person approval. The App needs no administration, secrets,
or deployment permission.
Its installation and environment must be configured and verified before this
route is usable. The exact App identity and installer are not yet known.

This route gives GitHub a distinct PR author for code actually proposed by an
agent and allows `BeamoINT` to review that code. It does **not** prove who
wrote the source branch; relaying a `BeamoINT`-authored change through the App
would defeat the independence the policy seeks. The evidence file and commit
history must be inspected during review. Human-authored `BeamoINT` changes
still need a different qualified reviewer. Until the App route passes an
end-to-end non-release test and the human-authored path is acknowledged, the
one-approval protection must remain unapplied to avoid an unusable merge path.

## Proposed narrow change and rollback

After the review path and eligibility are recorded, re-read protection and
effective GraphQL rules to detect intervening changes. The narrow REST
`PATCH /repos/BeamoTech/beamo-wipe/branches/main/protection/required_pull_request_reviews`
can enable the approved review rule without replacing the existing status-check
object. The proposed body is `required_approving_review_count: 1`,
`dismiss_stale_reviews: false`, `require_code_owner_reviews: false`, and
`require_last_push_approval: false`, with no bypass allowances. Compare every
table entry above after the change, especially strict
`CI gate` and its app ID. Confirm the approval requirement through GraphQL and
the protection parent response; do not infer it from review-subresource
defaults. Verify with the smallest safe non-release PR or supported ruleset
evaluation, without starting an extra costly CI run merely for this audit.

If the review rule causes a lockout or differs from the approved policy,
`DELETE` that same `required_pull_request_reviews` subresource to restore the
recorded no-review state, then re-read the parent protection and GraphQL rule.
Rollback must preserve every existing status, strictness, administrator,
force-push, and deletion setting. Any legitimate approvals made after
enforcement need consideration before rollback; record the actor, timestamp,
response, and final effective rule. Neither this proposal nor this document
authorizes changing GitHub settings.

## Local verification and remaining work

`git diff --check` passed, and the revised contribution commands and relative
links resolve locally. A broad `python3 -m pytest -q` run was interrupted at
14% after failures in the negative-gate isolation test and JUnit lifecycle
test; it is **not** a passing suite result. A focused rerun passed the JUnit
test but the negative-gate test's fake CI subprocess exceeded its 30-second
timeout on this macOS checkout. Neither test reads the three edited Markdown
files. No hosted CI, publication workflow, or repository-setting write was
started. A final read-only protection response was byte-for-byte identical
to the before snapshot. The documentation correction was pushed to
[`codex/review-enforcement-118`](https://github.com/BeamoTech/beamo-wipe/tree/codex/review-enforcement-118)
without opening a PR or starting CI; it is not merged. A reviewer path and
hosted validation remain necessary before merge.
Enforcement, its after-settings comparison, and a safe merge-rule check remain
outstanding.

### Follow-up preparation results

The unmerged agent proposal workflow, publisher, and local Git-fixture tests
were prepared on `codex/review-enforcement-118`. Ten focused fixture tests
passed, including exact-tree replay, malformed/stale input rejection, symlink
evidence rejection, wrong publisher actor, and repeated publication using a
fake `gh` and bare Git remote. `actionlint`, focused Ruff checks and formatting,
shell syntax, and `git diff --check` passed. No live App token or disk was used.
The full local `./scripts/test-all.sh` run finished with **4,605 passed, 710
skipped, four failed** in 7m10s. Failures were in the preview negative fixture
(preview cannot write/open its gallery in this checkout), two `gi`/ATK tests
(PyGObject unavailable on this Mac), and the QMP UNIX-socket fixture (sandbox
denied socket bind). Hosted Linux, Windows, ISO, and QEMU qualification of this
change remain unrun. These failures must not be described as a passing full
local gate. A read-only browser check found no dedicated App installed for
this repository, and the local `gh` token was invalid. No branch-protection or
Actions permission setting changed.

### Dedicated App registration after operator approval

After the operator approved the dedicated App setup and completed GitHub sudo
verification, `BeamoINT` registered the organization-owned GitHub App
[`Beamo Wipe Agent PR Publisher`](https://github.com/apps/beamo-wipe-agent-pr-publisher)
(App ID `5113012`, slug `beamo-wipe-agent-pr-publisher`). At registration, the
form selected only repository Contents, Pull requests, and Workflows read/write,
plus GitHub's mandatory Metadata read permission. Webhooks, user OAuth during
installation, and device flow were disabled; installation was limited to
`BeamoTech`. The post-registration page displayed “Registration successful”
and stated that a private key must be generated before installation. A fresh
saved-permissions page reported three selected repository permissions and one
mandatory permission; the exact entries still require independent readback. No
private key was generated or handled by the agent, the App was not installed,
and no `agent-pr` environment or one-approval branch rule was configured. The
App's existence alone does not provide a qualifying reviewer path.

### Protected agent PR environment

Using the existing `BeamoINT` GitHub credential after a read-only before check,
the `agent-pr` environment was created with `BeamoINT` (user ID `122241124`)
as required reviewer, `prevent_self_review: false`, no wait timer, and a custom
deployment branch policy matching only the branch `main`. The nonsecret
`BEAMO_AGENT_APP_ID` environment variable was created with value `5113012`.
A post-write REST readback verified these values and found no environment
secrets. Before creation, the only repository environment was `production`;
no existing environment was modified. Main protection still required strict
`CI gate` (Actions app ID `15368`) and administrator enforcement, with no
required pull-request review. This environment cannot publish an agent PR
until the private key is stored by the operator, the App is installed only on
this repository, the workflow is merged to `main`, and a safe end-to-end test
succeeds. Rollback of this setup, if needed before any run, is to delete only
the new `agent-pr` environment and App after confirming no dependent secret or
workflow; the existing `production` environment and branch protection must
remain untouched.

### Repository-scoped installation after GitHub authentication

After GitHub sudo authentication, `BeamoINT` installed the dedicated App as
installation `165943719`. The GitHub installation confirmation displayed
"Installed" and its repository access selector showed **Only select
repositories**, with exactly one selected repository,
`BeamoTech/beamo-wipe`. The permission summary showed Metadata read and
Contents, Pull requests, and Workflows read/write. No other repository was
selected. The App ID remains `5113012`.

A same-session REST read of the `agent-pr` environment secret names still
returned an empty list. A fresh read of `main` reported commit
`e986419379f512f8088f5982ee02a51dc91a9dae`, strict `CI gate` bound to
GitHub Actions app ID `15368`, administrator enforcement enabled, force pushes
and deletions disabled, and **no** required PR review. The installed App does
not make the proposal workflow operational until its private key is placed in
the protected environment and the workflow reaches `main`. No private key has
been handled by the agent. No branch-protection change or hosted CI run was
made during installation. The App installation can be suspended or uninstalled
through GitHub's installation `165943719` settings if this route is abandoned.

### Final review and authenticated publication coverage — 2026-09-29

The operator authorized merging PR #80 after Greptile review and confirmed-bug
fixes. [Greptile's review of `466ba9d`](https://github.com/BeamoTech/beamo-wipe/pull/80#discussion_r4129310559)
found that the local publication fixture never invoked the credential helper.
The fixture now uses a loopback-only smart-HTTP Git remote that requires a fake
App token for pushes. It verifies successful authenticated branch publication,
reuse without another push, and rejection before PR creation for an invalid
token. Developer credential configuration and interactive prompts are disabled.
The server has one thread, bounded reads/backend commands, and verified teardown.

All 11 publisher tests passed locally outside the Mac socket sandbox. Removing
the push credential helper in memory made the successful-publication test fail,
as required; the mutation changed no source file. Ruff and diff checks passed.
This tests Git's real authentication exchange with fake credentials, not a live
GitHub App installation. The protected-environment secret and the hosted
App-authored end-to-end smoke remain prerequisites for review enforcement.
