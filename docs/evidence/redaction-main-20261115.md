# Redaction record for main (2026-11-15)

The owner's Windows profile directory name was replaced in the five files on
main that contained it. This uses the same placeholders as the PR #93 scrub
(`docs/evidence/security-main-handoff-20261027/redaction-20261115.md` on that
branch). Each edited line differs from the original only by the literal
replacement. No hostname appeared on main.

| Original (not reproduced here) | Replacement |
|---|---|
| `C:/Users/<name>` | `C:/Users/USERNAME` |
| `C:\Users\<name>` | `C:\Users\USERNAME` |
| JSON-escaped `C:\\Users\\<name>` | `C:\\Users\\USERNAME` |

| File | Replaced | Redacted sha256 |
|---|---:|---|
| `.ai/memory/unfinished-work.md` | 80 | `98e6529678e352b0698d57f4830158b09631d2b811d524addbef9ca263b52db5` |
| `docs/evidence/development-ci-120/windows-local-checks.json` | 54 | `4a07e885e08b9312369fc5cc6894064fd3833b51dd22a95fc708158f31ec4b1c` |
| `docs/evidence/development-ci-120/windows-test-results.json` | 6 | `6913ea2e71f6ec7e55e5a9e35b6fe70fd2ae92b5f2377d8b0f1d61c7b3c85954` |
| `docs/evidence/development-ci-120/windows-20261001.md` | 1 | `3df2074743ccc79fd8b5fea5c97d94aa5f8b2207233651d7f4a86afcc566e77a` |
| `docs/evidence/sole-maintainer-policy-20261001.md` | 1 | `ebe88f06523c5556c7f8a690286d159ab8055eb9614941902d300bfb50f9c151` |

Total: 142 mentions in 5 files. Both JSON files still parse.

## Effect on recorded hashes

`windows-test-results.json` (its sha256 map) and
`windows-reference-inventory.tsv` (row for `windows-20261001.md`) record the
sha256 of `windows-20261001.md`. That sha256 was taken before this redaction.
Both records were **not** changed, so they describe the original bytes, not
the published file. A mismatch there is expected; it is not tampering and
not a new verification result.

The original text stays in this repository's history before this commit.
Removing it from history is a separate decision.
