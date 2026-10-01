# Sole-maintainer PR policy — 2026-10-01

The repository owner confirmed that BeamoINT is the only user and BeamoTech is
the organization, then explicitly instructed: “Get rid of that requirement
then since I'm the only person that works on this and then merge it if it's
complete.” This replaces the former non-author approval requirement; the
[current policy](../ci.md#required-checks-and-rollout) remains the canonical guide.

Read-only GitHub inspection at 14:00 UTC found the following existing settings:

| Setting | Observed value |
| --- | --- |
| Required check | `CI gate`, bound to GitHub Actions app ID 15368 |
| Up-to-date branch | strict `true` |
| Administrator enforcement | enabled |
| Required pull-request reviews | absent (`null`) |
| Force pushes and deletion | both disabled |
| Repository/inherited rulesets | empty |

Commands were authenticated `gh api` GETs for
`repos/BeamoTech/beamo-wipe/branches/main/protection` and
`repos/BeamoTech/beamo-wipe/rulesets?includes_parents=true`.
Responses and timestamps are preserved under
`C:\Users\Jack\AppData\Local\BeamoWipe\development-ci-120\20261001T140001Z-review-policy`.
Credentials were supplied only to the subprocess environment and were not logged.
No remote protection mutation was necessary: there was no active approval rule
to remove. The required CI, administrator and branch-integrity protections stay
in place.

Updated CONTRIBUTING, development and CI guidance, and marked the two older
review audits as superseded for this policy. Historical findings, release assets
and the optional agent-PR authoring workflow are retained. No runtime, disk
selection, wipe flags, release procedure or CI workflow changed.

These edits update [PR #83](https://github.com/BeamoTech/beamo-wipe/pull/83).
The prior head `cd0a1d8154691d022c5acd5c4bb1771453187fe5` passed
[CI attempt 2](https://github.com/BeamoTech/beamo-wipe/actions/runs/36817967747/attempts/2)
at merge revision `5b50175bf4f7c81ac8fb1abb5b79fcaf38ac8ef5`. That result does
not qualify this new documentation revision. The owner authorized merging after
the updated exact-revision CI gate passes; resulting main CI must be observed
separately. Current qualification and merge results are recorded on the PR.
