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
