# Code-signing the Windows launcher (#182)

Status, 2026-11-09: **prepared, not bought.** Nothing was bought, no account
was made, and no workflow signs anything yet. Today `Start Beamo Wipe.exe`
has no Authenticode signature. Keep the "unknown publisher" wording in
[boot-card.md](boot-card.md) and [desktop-entry-design.md](desktop-entry-design.md)
until a signed release ships.

Prices below were read on 2026-11-09. Prices change. Check the price on the
checkout page before you pay.

## Decision

**Buy Microsoft Artifact Signing (formerly Trusted Signing), Basic plan.**

- **Cost: US $9.99 a month** (US $119.88 a year), plus any sales tax Azure
  adds for your billing address. Basic includes 5,000 signatures a month.
  Each extra signature costs $0.005. We sign one file per release, so we
  will not go over.
- **Billing:** monthly, on a paid (pay-as-you-go) Azure subscription. Free and
  trial subscriptions are not allowed. Billing starts when you create the
  signing account. Microsoft charges the full month; it is not pro-rated.
- **No hardware, no shipping, and no key to look after.** Microsoft keeps the
  key in its own hardware security module (HSM). The release job signs by
  GitHub OIDC, so we store no signing password in GitHub.
- **Why not cheaper:** only one cheaper route exists, and it does not fit. See
  the table.

**Runner-up, if Microsoft will not validate the company:**
an SSL.com OV code-signing certificate, **US $129 a year**, with the key in
Google Cloud KMS at HSM level in the existing `beamo-wipe` project. SSL.com
charges a **$75 attestation fee** for a Google Cloud HSM key. Add the small
Google Cloud KMS monthly key charge (not checked here). First year is about
**$204 plus KMS**. This reuses the release job's existing Google OIDC login.
If that set-up is too much work, SSL.com eSigner cloud signing is simpler but
costs $180 a year more (Tier 1 yearly plan, 240 signings), about **$309 a year** in total.

### Route comparison

| Route | Publisher name users see | First year | Later years | Signs from CI without a person | Fits Beamo? |
|---|---|---|---|---|---|
| **Microsoft Artifact Signing, Basic** | Validated company name (or the person's name, see below) | **$119.88** + tax | $119.88 | Yes: OIDC, jsign on Linux or the official action on Windows | **Yes, if the company passes validation** |
| Certum Open Source, cloud | "Open Source Developer, <person>" | €49 | €49 | No: SimplySign needs a code from a phone app | No: person only, not the company name; listed "out of stock" |
| SignPath Foundation | "SignPath Foundation" | Free | Free | Yes | No: the certificate names SignPath, not Beamo |
| SSL.com OV + own Google Cloud HSM key | Validated company name | $129 + $75 + KMS | $129 + KMS (attestation may repeat; not confirmed) | Yes: jsign `GOOGLECLOUD` | Runner-up |
| SSL.com OV + eSigner | Validated company name | $129 + $180 = $309 | $309 | Yes: eSigner CodeSignTool | Simple fallback |
| Certum Standard, cloud / card set | Validated company name | €209 cloud; €169 card set (+ shipping, not stated) | same | Cloud: no (phone code); card: no | No |
| Sectigo through resellers | Validated company name | About $212–$288 (reseller pages disagree) + token or HSM | same | Depends on key storage | Costs more |
| DigiCert | Validated company name | From $696 (12-month plan) | same | Yes (KeyLocker) | Costs much more |
| GlobalSign | Validated company name | Price not shown publicly | — | — | Not compared |
| Any EV certificate | Validated company name | €329–$972+ | same | Varies | No: EV gives no SmartScreen benefit now |

## Rules that shape the choice

- **Key storage.** Since 1 June 2023 the CA/Browser Forum code-signing rules
  require the private key of every OV and EV certificate to live in hardware: a
  token, an HSM, or a cloud HSM. A key in a file is no longer allowed. This is
  why the token or cloud fee counts as part of the price.
- **Validity, 2026 change.** CA/Browser Forum ballot CSC-31 (adopted
  2025-11-17) cut the longest code-signing certificate from 39 months to
  **460 days**, from **1 March 2026**. Certum lists 459 days from 27 February 2026.
  So a bought certificate must be re-issued about once a year, even on a
  "multi-year" order. Multi-year discounts still apply, but the yearly cost
  barely changes. Artifact Signing is not affected: its certificates last
  3 days and renew by themselves.
- **SmartScreen.** EV no longer gives instant reputation. Microsoft says:
  "EV certificates no longer bypass SmartScreen." OV and EV act the same. See
  [What users will see](#what-users-will-see).

## Eligibility checklist (the owner must confirm)

The repository says only this about the publisher: the copyright holder is
"Jack Allison / Beamo" (`NOTICE`, `pyproject.toml`), the GitHub organization
is `BeamoTech`, and the support site is `beamosupport.com`. It does **not**
say the legal company name, the kind of company, the country, the founding
year, or a business registration number. These are unknown. Confirm each
one before you pay:

1. **A registered legal company.** Write down its exact legal name. The
   certificate shows only that name. Microsoft does not allow a custom name.
2. **Country.** For a company certificate, Microsoft lists: the United
   States, Canada, the EU, the UK, Australia, New Zealand, Japan, South Korea,
   Singapore, Switzerland, Norway and Israel.
3. **Company age.** Several Microsoft Q&A answers say a company needs about
   **3 years** of history (founding date or tax records). The current
   Microsoft FAQ no longer says this. **Not confirmed.** If the company is
   younger than 3 years, expect a refusal and use the fallback below.
4. **Business identifier.** For example, a US EIN or a company registration
   number.
5. **Business address** that matches public records.
6. **Website and two email addresses on the company domain.** Example:
   `beamosupport.com`. Both mailboxes must get mail from outside senders,
   including links. A list address is fine for the second one only.
7. **The person who will verify.** That person needs a government photo ID
   (passport, driving licence or ID card) and a phone with Microsoft
   Authenticator for a face check. The name must match the ID exactly.
8. **Recent papers ready.** Microsoft may ask for business registration or
   articles of incorporation, and a domain registration or invoice. All
   papers must be dated within the last 12 months.
9. **A card for the Azure subscription.**

**Fallback in the same service (individual):** If the company cannot pass
but the owner lives in the **United States or Canada**, choose "Individual"
validation. The price is the same. The certificate then shows the **owner's
own name** and city, not "Beamo". The Azure billing account must be of type
"Individual" and must match the ID exactly. If neither fits, buy the runner-up.

## Purchase steps (owner only)

Only the owner can do these steps. Identity checks cannot be done by an agent.

1. Go to <https://portal.azure.com> and sign in, or create a Microsoft account.
2. Create a **pay-as-you-go** subscription and add the card.
3. Open **Subscriptions** → your subscription → **Resource providers**.
   Select **Microsoft.CodeSigning** → **Register**.
4. Search **Artifact Signing Accounts** → **Create**.
   - Resource group: **Create new** → `beamo-signing`.
   - Account name: for example `beamowipesign` (3–24 letters or numbers, unique worldwide).
   - Region: **East US** (or the region nearest you).
   - Pricing: **Basic**.
   - **Review + Create** → **Create**. *Billing ($9.99 a month) starts now.*
5. In the new account, open **Access control (IAM)**. Give yourself the
   role **Artifact Signing Identity Verifier**.
6. Open **Identity validations** → **Organization** → **New identity** →
   **Public**. Fill in the legal name, website, both emails, business
   identifier and address. Check **Certificate subject preview**. Select **Create**.
7. Click the link in the email within **7 days**. When the status says
   **Action Required**, do the ID and face check on your phone.
8. Wait. Microsoft says 1 to 20 business days. If it asks for papers, upload
   them in the portal (3 tries only).
9. When the status is **Completed**: open **Certificate profiles** →
   **Create** → **Public Trust**. Name it, for example `beamowipe-public`.
   Choose your validation. Leave the street address and postal code unticked.
   Select **Create**.
10. Let GitHub sign without a password (OIDC). In **Microsoft Entra ID** →
    **App registrations** → **New registration** (name `beamo-wipe-release-signing`).
    Under **Certificates & secrets** → **Federated credentials** → **Add**:
    GitHub Actions, organization `BeamoTech`, repository `beamo-wipe`, entity
    **Branch**, branch `main`. Do **not** create a client secret.
11. Back in the certificate profile → **Access control (IAM)**: give the app
    from step 10 the role **Artifact Signing Certificate Profile Signer**.
    Give it nothing else.

If validation fails, delete the signing account so billing stops, then use
the fallback or the runner-up.

## What to hand back after purchase

Hand back only these names and their values. None of them is a secret. Store
them as **GitHub repository variables** (Settings → Secrets and variables →
Actions → Variables). Do not add a GitHub secret for signing. With OIDC none
is needed.

| Variable name | What it holds |
|---|---|
| `AZURE_TENANT_ID` | Directory (tenant) ID from Entra |
| `AZURE_CLIENT_ID` | Application (client) ID of the app from step 10 |
| `AZURE_SUBSCRIPTION_ID` | The subscription ID |
| `BEAMO_SIGN_ENDPOINT` | The region endpoint, for example `https://eus.codesigning.azure.net` |
| `BEAMO_SIGN_ACCOUNT` | Signing account name from step 4 |
| `BEAMO_SIGN_PROFILE` | Certificate profile name from step 9 |
| `BEAMO_SIGN_PUBLISHER` | The exact company name shown in the certificate subject |
| `BEAMO_AUTHENTICODE_ENABLED` | Leave **unset** until the release change below is merged and tested |

Also tell us: which validation passed (organization or individual), the date
it expires, and the monthly invoice amount shown in Azure.

Never paste a password, token, client secret or ID photo into chat, an issue
or this repository.

## How signing plugs into the release

`release.yml` was **not changed**. A safe signing step does not fit there yet:

- The launcher is built by `scripts/build_desktop.py`. That script records the
  launcher's SHA-256 in `dist/desktop/desktop-build.json`. `build-iso.sh` then
  checks that hash and copies the launcher into the ISO and the USB image.
  The `verify` job then qualifies those exact image bytes in QEMU.
- So the launcher must be signed **inside the build, before the hash is
  recorded**. Signing in the `publish` job would change files inside an
  image that was already qualified. That is not allowed.
- The `verify` job has no OIDC permission today. Adding one moves a signing
  identity into the job that builds and tests the image. That trust change is
  a separate owner decision.

**Remaining code work (not purchase):**

1. Add an opt-in hook to `scripts/build_desktop.py`. When `BEAMO_SIGN_LAUNCHER=1`,
   run `scripts/sign_windows_launcher.py` on the staged
   `Start Beamo Wipe.exe` after `go build` and **before** its SHA-256 is
   recorded. Record the signer and the signed hash in `desktop-build.json`.
   Without the variable, nothing changes. Add tests.
2. Add the YAML below to the `verify` job and give that job
   `id-token: write`. Pull requests and `ci.yml` never sign.
3. Make the release refuse an unsigned launcher once
   `BEAMO_AUTHENTICODE_ENABLED` is `true`.
4. Get the root certificate file (see below) and pin its hash.

Ready-to-apply snippet for `.github/workflows/release.yml`, job `verify`.
Put it **after** "Run source and safety gates" and **before** "Build and
inspect customer ISO". The sources gate (`scripts/ci-desktop.sh`) builds an
unsigned pair. This step replaces it with a signed pair. `build-iso.sh` then
uses the existing `dist/desktop` pair. Every step is skipped unless the
repository variable `BEAMO_AUTHENTICODE_ENABLED` is exactly `true`:

```yaml
      - name: Log in to Azure for launcher signing (only when enabled)
        if: vars.BEAMO_AUTHENTICODE_ENABLED == 'true'
        uses: azure/login@a641126d1b8aa4d1fa005f4f92df94a3a4c4c906 # v3.1.0
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - name: Build and sign the Windows launcher (only when enabled)
        if: vars.BEAMO_AUTHENTICODE_ENABLED == 'true'
        env:
          BEAMO_SIGN_LAUNCHER: '1'
          BEAMO_SIGN_ENDPOINT: ${{ vars.BEAMO_SIGN_ENDPOINT }}
          BEAMO_SIGN_ACCOUNT: ${{ vars.BEAMO_SIGN_ACCOUNT }}
          BEAMO_SIGN_PROFILE: ${{ vars.BEAMO_SIGN_PROFILE }}
          BEAMO_SIGN_PUBLISHER: ${{ vars.BEAMO_SIGN_PUBLISHER }}
        run: |
          set -euo pipefail
          sudo apt-get install -y --no-install-recommends osslsigncode default-jre-headless
          curl -fsSL -o "$RUNNER_TEMP/jsign-7.6.jar" \
            https://github.com/ebourg/jsign/releases/download/7.6/jsign-7.6.jar
          echo "6cf58aa080e7ff82656f320cff8d4a3bff30408df8766806dcba3740dd839fa5  $RUNNER_TEMP/jsign-7.6.jar" | sha256sum -c -
          export BEAMO_SIGN_JSIGN_JAR="$RUNNER_TEMP/jsign-7.6.jar"
          export BEAMO_SIGN_CA_FILE="$GITHUB_WORKSPACE/packaging/signing/microsoft-artifact-signing-roots.pem"
          BEAMO_SIGN_ACCESS_TOKEN="$(az account get-access-token --resource https://codesigning.azure.net --query accessToken -o tsv)"
          echo "::add-mask::$BEAMO_SIGN_ACCESS_TOKEN"
          export BEAMO_SIGN_ACCESS_TOKEN
          bash scripts/build-desktop.sh
```

This snippet needs the `build_desktop.py` hook (step 1) and the roots file
(step 4) first. `packaging/signing/microsoft-artifact-signing-roots.pem` does
not exist yet. Pin the action by the full commit hash, as above.

### The signing script

`scripts/sign_windows_launcher.py` is ready. It:

- refuses to run unless `BEAMO_SIGN_ENDPOINT`, `BEAMO_SIGN_ACCOUNT`,
  `BEAMO_SIGN_PROFILE`, `BEAMO_SIGN_PUBLISHER`, `BEAMO_SIGN_JSIGN_JAR` and
  `BEAMO_SIGN_CA_FILE` are set, and (except in `--dry-run`)
  `BEAMO_SIGN_ACCESS_TOKEN`;
- signs only paths named exactly `Start Beamo Wipe.exe` that are regular,
  unsigned Windows programs, and refuses links, folders, repeats and other files;
- refuses a jsign jar whose SHA-256 is not the pinned jsign 7.6 hash;
- passes the token to jsign by name (`--storepass env:BEAMO_SIGN_ACCESS_TOKEN`),
  so the token is never on a command line, and hides it in any error text;
- signs with SHA-256 and an RFC 3161 timestamp from
  `http://timestamp.acs.microsoft.com`;
- checks afterwards with `osslsigncode verify` that the signature is valid,
  names `BEAMO_SIGN_PUBLISHER`, and has a timestamp. Then it prints a JSON
  receipt with the unsigned and signed SHA-256.

Check settings without signing:

```bash
python3 scripts/sign_windows_launcher.py --dry-run "dist/desktop/Start Beamo Wipe.exe"
```

Tests: `tests/test_sign_windows_launcher_182.py` (fake files, no network, no Java).

## Verify a signed launcher

On Windows (PowerShell):

```powershell
Get-AuthenticodeSignature -FilePath 'E:\Start Beamo Wipe.exe' | Format-List Status, StatusMessage, SignerCertificate, TimeStamperCertificate
signtool verify /pa /v 'E:\Start Beamo Wipe.exe'
```

`Status` must be `Valid`, and the signer must be the company name.
`TimeStamperCertificate` must not be empty. `signtool` comes with the Windows SDK.
You can also right-click the file → **Properties** → **Digital Signatures**.

On Linux:

```bash
osslsigncode verify -CAfile roots.pem -TSA-CAfile roots.pem -in "Start Beamo Wipe.exe"
```

## What users will see

From Microsoft's SmartScreen page (updated 2026-08-17):

- A new signed file can **still** show a SmartScreen warning at first. The
  difference: the warning shows the **verified publisher name** instead of
  "Unknown publisher".
- Reputation builds over time. Microsoft says it "can take several weeks and
  hundreds of clean installs". There is no way to buy it.
- Signing every release with the **same identity** lets later versions keep
  the publisher's reputation. Unsigned files start from zero each time.
- On Windows 11, **Smart App Control** (when it is on) blocks unsigned
  programs that have no good reputation. Signing matters there.

Not checked: a launcher opened from the Beamo USB usually has no "downloaded
from the internet" mark, so the SmartScreen download check may not run at
all. Smart App Control checks it anyway. Neither was tested on a real
computer. Update the boot card only after a signed release ships and is
checked on real Windows 10 and 11.

## Renewal

- Azure bills **$9.99 every month** until the signing account is deleted.
- The certificates last 3 days and renew by themselves. The RFC 3161
  timestamp keeps old signatures valid after that.
- **Identity validation expires.** Microsoft emails reminders starting 60
  days before. Renew it, or signing stops. The FAQ does not say how long a
  validation lasts. Write down the date shown in the portal.
- If you stop paying, files already signed stay valid. New releases would
  be unsigned and lose the publisher reputation.
- Runner-up only: re-issue the certificate about once a year (460-day limit),
  and renew it before it expires.

## Still not verified

- Whether the company qualifies (legal name, country, age, papers). Only the
  owner can confirm this.
- The 3-year company-age rule. It appears in Microsoft Q&A answers but not in
  the current FAQ.
- Sales tax on the Azure bill. It depends on the billing address.
- jsign 7.6 `TRUSTEDSIGNING` signing from a Blacksmith Linux runner. Also
  whether `az`, Java and `osslsigncode` are on that runner image.
- The exact Microsoft root and timestamp certificates that `osslsigncode`
  needs. Get them from the Microsoft PKI repository
  (<https://www.microsoft.com/pkiops/docs/repository.htm>) at first signing,
  pin their hash, and confirm the `osslsigncode` output names the publisher
  and a timestamp.
- SmartScreen and Smart App Control on real Windows 10/11 with a signed launcher.
- Runner-up prices: Google Cloud KMS HSM key charge, and whether SSL.com's $75
  attestation fee repeats each re-issue.

## Sources (read 2026-11-09)

- Azure retail price API, service "Trusted Signing": Basic $9.99/month,
  Premium $99.99/month, overage $0.005/signature —
  <https://prices.azure.com/api/retail/prices?$filter=contains(serviceName,'Signing')>
- Artifact Signing pricing page (5,000 signatures/month on Basic) —
  <https://azure.microsoft.com/pricing/details/artifact-signing/>
- Artifact Signing quickstart (countries, individual US/Canada only,
  validation fields, 1–20 business days; updated 2026-10-08) —
  <https://learn.microsoft.com/azure/artifact-signing/quickstart>
- Artifact Signing FAQ (paid subscription only, not pro-rated, no custom name,
  validation expiry; updated 2026-10-27) —
  <https://learn.microsoft.com/azure/artifact-signing/faq>
- 3-year rule, Microsoft Q&A (not official policy) —
  <https://learn.microsoft.com/answers/questions/5781004/identity-validation-failed-for-polish-sole-proprie>
- SmartScreen reputation (updated 2026-08-17) —
  <https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation>
- Official GitHub action (Windows runners only) —
  <https://github.com/Azure/artifact-signing-action>
- jsign 7.6 (`TRUSTEDSIGNING`, `GOOGLECLOUD`, `env:` passwords; release
  2026-10-12, jar SHA-256 from the GitHub release asset) —
  <https://ebourg.github.io/jsign/>, <https://github.com/ebourg/jsign/releases/tag/7.6>
- CA/B Forum Code Signing Baseline Requirements (hardware key rule from
  2023-06-01, ballots CSC-13 and CSC-17) —
  <https://cabforum.org/working-groups/code-signing/requirements/>
- CA/B Forum ballot CSC-31, 460 days from 2026-03-01 —
  <https://cabforum.org/2025/11/17/ballot-csc-31-maximum-validity-reduction/>
- Certum prices and 459-day note — <https://shop.certum.eu/code-signing.html>;
  open-source cloud product — <https://shop.certum.eu/open-source-code-signing-on-simplysign.html>
- SSL.com OV price and HSM attestation fees —
  <https://www.ssl.com/products/software-integrity/code-signing/ov/>;
  eSigner tiers (updated 2026-03-25) —
  <https://www.ssl.com/guide/esigner-pricing-for-code-signing/>
- SignPath Foundation terms — <https://signpath.org/terms>
- DigiCert — <https://www.digicert.com/signing/code-signing-certificates>;
  GlobalSign — <https://shop.globalsign.com/en/code-signing>
- Sectigo reseller prices (unconfirmed, affiliate sites) —
  <https://cheapsslsecurity.com/sectigo/sectigo-code-signing-certificate.html>,
  <https://sslinsights.com/sectigo-code-signing-certificate-guide/>
