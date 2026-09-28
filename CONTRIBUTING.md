# Contributing

This is a safety-critical wrapper around nwipe. Prefer obvious code over clever code.

## Rules

- Conventional commits: `feat:`, `fix:`, `docs:`, `safety:`.
- Any change to disk selection or nwipe flags is `safety:` and needs a test.
- Never commit ISOs, USB images, or secrets.
- `main` should stay releasable.
- Do not add a new wipe engine, password tools, or Secure Boot circumvention.

## Checks

```bash
python3 -m pytest
./scripts/test-all.sh
```

Open PRs into `main` and obtain one approving review from a non-author with
write access. The required hosted check is `CI gate` in
`.github/workflows/ci.yml`, which runs on Blacksmith through
GitHub Actions for PRs to `main`. The branch must be up to date and the check
must pass before merge. See [CI and branch policy](docs/ci.md). Release
publication is a separate, explicitly authorized workflow.
