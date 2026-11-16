# Redaction record for PR #93 evidence (2026-11-15)

Before PR #93 merges into the public repository, the owner's Windows
profile directory name and this development PC's hostname were replaced in
every file the PR adds or changes. Nothing else changed: each edited line
differs from the original only by these literal replacements.

| Original (not reproduced here) | Replacement |
|---|---|
| owner profile path, forward slashes (`C:/Users/<name>`) | `C:/Users/USERNAME` |
| owner profile path, JSON-escaped (`C:\\Users\\<name>`) | `C:\\Users\\USERNAME` |
| development PC hostname (`"hostname"` fields) | `HOSTNAME` |

Totals: 54 files, 302 path mentions and 6 hostname mentions
replaced. The original commits were bf2b4909's two PR commits; the scrub was
folded into those commits, keeping their authors, dates and messages.

## Effect on recorded hashes

`canonical_hashes`, `raw_seal` and other sha256 values inside these evidence
files were recorded before redaction. They were **not** changed, so they
describe the original bytes, not the files published here. The redacted
sha256 below identifies the published bytes. A recorded
hash that no longer matches its file is expected for the files listed here.
It is not tampering, and it is not a new verification result.

Recorded hashes that now refer to pre-redaction bytes (18):

- `docs/evidence/bug-audit-20261024/README.md`: recorded in `docs/evidence/bug-audit-20261025/verification.json`
- `docs/evidence/bug-audit-20261025-pass4/reviews.json`: recorded in `docs/evidence/bug-audit-20261025-pass4/verification.json`
- `docs/evidence/bug-audit-20261025-pass6/README.md`: recorded in `docs/evidence/bug-audit-20261025-pass6/verification.json`
- `docs/evidence/bug-audit-20261025-pass6/reviews.json`: recorded in `docs/evidence/bug-audit-20261025-pass6/verification.json`
- `docs/evidence/bug-audit-20261025-pass7/README.md`: recorded in `docs/evidence/bug-audit-20261025-pass7/verification.json`
- `docs/evidence/bug-audit-20261025-pass7/reviews.json`: recorded in `docs/evidence/bug-audit-20261025-pass7/verification.json`
- `docs/evidence/bug-audit-20261025/README.md`: recorded in `docs/evidence/bug-audit-20261025/verification.json`
- `docs/evidence/bug-audit-20261025/reviews.json`: recorded in `docs/evidence/bug-audit-20261025/verification.json`
- `docs/evidence/bug-audit-20261026-pass10/README.md`: recorded in `docs/evidence/bug-audit-20261026-pass10/verification.json`
- `docs/evidence/bug-audit-20261026-pass10/reviews.json`: recorded in `docs/evidence/bug-audit-20261026-pass10/verification.json`
- `docs/evidence/bug-audit-20261026-pass11/README.md`: recorded in `docs/evidence/bug-audit-20261026-pass11/verification.json`
- `docs/evidence/bug-audit-20261026-pass11/reviews.json`: recorded in `docs/evidence/bug-audit-20261026-pass11/verification.json`
- `docs/evidence/bug-audit-20261026-pass12-resume1/README.md`: recorded in `docs/evidence/bug-audit-20261026-pass12-resume1/verification.json`
- `docs/evidence/bug-audit-20261026-pass12/README.md`: recorded in `docs/evidence/bug-audit-20261026-pass12/verification.json`
- `docs/evidence/bug-audit-20261026-pass8/README.md`: recorded in `docs/evidence/bug-audit-20261026-pass8/verification.json`
- `docs/evidence/bug-audit-20261026-pass8/reviews.json`: recorded in `docs/evidence/bug-audit-20261026-pass8/verification.json`
- `docs/evidence/bug-audit-20261026-pass9/README.md`: recorded in `docs/evidence/bug-audit-20261026-pass9/verification.json`
- `docs/evidence/bug-audit-20261026-pass9/reviews.json`: recorded in `docs/evidence/bug-audit-20261026-pass9/verification.json`

## Files

| File | Path | Host | Redacted sha256 |
|---|---:|---:|---|
| `.ai/memory/unfinished-work.md` | 31 | 0 | `016d6346aa782d930fa263913e13bc1493a1a2ffce079a83299f94aa1f38a72b` |
| `docs/evidence/bug-audit-20261024/README.md` | 2 | 0 | `5a35754bdbb9f4bbbe6ac9c704776c540150cd9f9c213dfd715240801ae2b9a7` |
| `docs/evidence/bug-audit-20261024/verification.json` | 1 | 0 | `c5f916360ac8254f434914cb8ef68f69aabd296249455959318be8b064f3a570` |
| `docs/evidence/bug-audit-20261025-pass4/README.md` | 3 | 0 | `90c6157fef517edd41a525c29e7da4587aa7ea36584f711b5937428d18cad8be` |
| `docs/evidence/bug-audit-20261025-pass4/reviews.json` | 13 | 0 | `9ff30b23d83f51bc2b4d55951ec783680fbbb0292f255317fe16292abeaf1f93` |
| `docs/evidence/bug-audit-20261025-pass4/verification.json` | 2 | 0 | `06e07025215926fc772c4086a1ca2c550f06c655fe0de8f9bbd1f2516966b1d0` |
| `docs/evidence/bug-audit-20261025-pass5/README.md` | 2 | 0 | `c776ab87995d6be47a76e52f82ec3d3f4cc35af1c62730565db2437601a4bc2b` |
| `docs/evidence/bug-audit-20261025-pass5/reviews.json` | 14 | 0 | `20f3a30d05b67e186563bb9d273b46c17de4356c853099480d7aa5cca7b53b1e` |
| `docs/evidence/bug-audit-20261025-pass5/verification.json` | 8 | 3 | `5bb59ea8d9fc91b6c1e7edf7d884a1ddadd06d4c05aa2040e6eab8baa1a43408` |
| `docs/evidence/bug-audit-20261025-pass6/README.md` | 2 | 0 | `5b3622a5795bd91a880b7bb04035ba6f0adb6359ac837213dd41229e24965619` |
| `docs/evidence/bug-audit-20261025-pass6/reviews.json` | 4 | 0 | `b953f7c6f56beac3501ec77e0f831446e8ff5e62878d6be8351e49fddfec2fdd` |
| `docs/evidence/bug-audit-20261025-pass6/verification.json` | 11 | 0 | `41cec2886411c40b6b2f845b383b16afd01952ff7580117b43f06b74fd847cb2` |
| `docs/evidence/bug-audit-20261025-pass7/README.md` | 2 | 0 | `7add668eb0ee1e84636f95338b206cb7aafc999fa9136416988a094eb78195d6` |
| `docs/evidence/bug-audit-20261025-pass7/reviews.json` | 11 | 0 | `1fe2350b367931c5e94a7dd7b0c33a6a9fe26f75757f68a62a82ab0d7e6a90ac` |
| `docs/evidence/bug-audit-20261025-pass7/verification.json` | 11 | 3 | `7c2752de3da397f046bb5267ae881fc1a8685b77ee2e2fc3bc611636936bc419` |
| `docs/evidence/bug-audit-20261025-repass/README.md` | 2 | 0 | `908dd606465673493a2ed3bbd440d34494a34b6bbdee5ded0c6153ec2f43a0f0` |
| `docs/evidence/bug-audit-20261025-repass/reviews.json` | 25 | 0 | `0750c6d7d2df456b6c526a9f9a8c9317c4726b4054e3a91e74c2ab73526d90d2` |
| `docs/evidence/bug-audit-20261025-repass/verification.json` | 3 | 0 | `5ac609ab4a97f38e86d7fb5a849c84bc07e791068ccf0fc4933e13ffa0422f0b` |
| `docs/evidence/bug-audit-20261025/README.md` | 3 | 0 | `1b62ab663b26ab01c355bd6b024486dd3001e6608ea21a1337948c876d4e48ed` |
| `docs/evidence/bug-audit-20261025/reviews.json` | 3 | 0 | `cb9b5885ff765314ca7b4f294cb0ee930272110bae3af12fb4e69a46b3828ca8` |
| `docs/evidence/bug-audit-20261025/verification.json` | 5 | 0 | `43427ce0124502e8690f556a564fe59574b73de9ee9b1991f2a3070475b6f7a0` |
| `docs/evidence/bug-audit-20261026-pass10/README.md` | 2 | 0 | `17078305848b08eb6fb5d954b6d95d11701e50b8e60cff97bd6b34999ce8082e` |
| `docs/evidence/bug-audit-20261026-pass10/reviews.json` | 5 | 0 | `acd46257c23ff6954400cb041c5b1156f8f36484d939f35d8c0a0d577e3ad40f` |
| `docs/evidence/bug-audit-20261026-pass10/verification.json` | 10 | 0 | `23d2b17c629877079374c854b285efdadd69e0461b32691bc7e182a8201af88a` |
| `docs/evidence/bug-audit-20261026-pass11/README.md` | 2 | 0 | `490d6f36c4288e8f02f32efbbd3c51e09638945d2888431e394ba910918291d2` |
| `docs/evidence/bug-audit-20261026-pass11/reviews.json` | 7 | 0 | `8b220a89558a212a57e4ffb0eb5561d89fbd81c9956b8724ebadcacfc9f683b3` |
| `docs/evidence/bug-audit-20261026-pass11/verification.json` | 6 | 0 | `cd2c1544443e849539a9ce54304651b28cc43b7c3c2759b9e94d9536c2e292af` |
| `docs/evidence/bug-audit-20261026-pass12-resume1/README.md` | 3 | 0 | `e4bb8c6c9386f22cbbb45b3e42b60a3f97bbbfd6ed1883383341195f240a3c60` |
| `docs/evidence/bug-audit-20261026-pass12-resume1/verification.json` | 2 | 0 | `5f94e9802fa309743edeecb8687db8fd3b18480887255a583aa9fdf964830b67` |
| `docs/evidence/bug-audit-20261026-pass12/README.md` | 2 | 0 | `21bec147d8a53d0035f98d04da869c2c1f11b749ba8d3c8286a551df1136f218` |
| `docs/evidence/bug-audit-20261026-pass12/verification.json` | 3 | 0 | `12fa1d223f7f028a1cf4a7a65ae78f131f13d9d6aa922ad2c7d5989cac5cd5fa` |
| `docs/evidence/bug-audit-20261026-pass13/README.md` | 2 | 0 | `7abe6b26d9ba5537d7b6eebb64e2a6df6903f8adb52ea14c6f2b00f036e63219` |
| `docs/evidence/bug-audit-20261026-pass13/reviews.json` | 2 | 0 | `94f0587ccb6df11b3336d256ed1934ac6ea01ca27f3506ff35ae055162182090` |
| `docs/evidence/bug-audit-20261026-pass13/verification.json` | 8 | 0 | `3a081db3ca5e462d7f82babd97d62336d6cc192b11cbd6c029ba0360c899dc4c` |
| `docs/evidence/bug-audit-20261026-pass14/README.md` | 2 | 0 | `88f278bda331897702c38dc2f46d17b37302d17a48495ba2c33619e11665d083` |
| `docs/evidence/bug-audit-20261026-pass14/reviews.json` | 1 | 0 | `b7a3d74a6a4f04df4c86d6733e5e8fceed2a981c14041a59fd03ab924816ffd5` |
| `docs/evidence/bug-audit-20261026-pass14/verification.json` | 1 | 0 | `d9d33fddb93080fcf94a1f21efc41c677896de82ef2d2718fe1cfdb44ef7ed19` |
| `docs/evidence/bug-audit-20261026-pass15/README.md` | 2 | 0 | `b167fd2161b2311bfd259949e89ad9999db903d67836837d1850e0efef2a1e20` |
| `docs/evidence/bug-audit-20261026-pass15/reviews.json` | 5 | 0 | `005b323356d287d07c4471615146431f9bcddf7498bdbdeb7f02be62d7729142` |
| `docs/evidence/bug-audit-20261026-pass15/verification.json` | 1 | 0 | `7e3e7de32114bc21233440fd74455ba8e70676e13d02533bda1d5acebd1927ba` |
| `docs/evidence/bug-audit-20261026-pass16/README.md` | 2 | 0 | `56fe6c91f14cdd926315dcf05f955f6a4d78b795daa758544923e8d6350908a3` |
| `docs/evidence/bug-audit-20261026-pass16/reviews.json` | 6 | 0 | `c50e5d8a8f7ba09bb64be3951c61ab78b44ce46aaa591dc44ceb2008dd39559d` |
| `docs/evidence/bug-audit-20261026-pass16/verification.json` | 1 | 0 | `07d084a4514d3fc3ca4f4cf9fd3b132d928c4fdebb7f162c9084bc41fcb2da3c` |
| `docs/evidence/bug-audit-20261026-pass8/README.md` | 2 | 0 | `b06123ff0011634b4bd50b7b6a9582317c6fe2e90cff8b2016564fb911d2dce2` |
| `docs/evidence/bug-audit-20261026-pass8/reviews.json` | 3 | 0 | `3c2537db6284dfa752abccaf48cc465aca45cd8eb7bc02a2c7948c7cf58cabd2` |
| `docs/evidence/bug-audit-20261026-pass8/verification.json` | 14 | 0 | `28ecb1f5f748e06f0997f3852ea86f9820441f91e8b7f739764e1aa184220f09` |
| `docs/evidence/bug-audit-20261026-pass9/README.md` | 2 | 0 | `c4e8e604a185eb796015972d25ae70de6c943e650a19f8cc9db0458f300a371d` |
| `docs/evidence/bug-audit-20261026-pass9/reviews.json` | 6 | 0 | `bb679aeec2ca11b66443df915ecbebb6875907376d17699eda9634779f679215` |
| `docs/evidence/bug-audit-20261026-pass9/verification.json` | 9 | 0 | `1a2cabd0df3c15bc6e1e7b2c10488b5ca03ead5356c70b46bb6714f78d5a13ee` |
| `docs/evidence/security-main-handoff-20261027/greptile-r1.json` | 10 | 0 | `a9e82d40f5e7192f0ad9e7ae715406281eae52b89044406e8d8ff86ca44a4c8f` |
| `docs/evidence/security-main-handoff-20261027/regression-bindings.json` | 2 | 0 | `de53d22c9f0d99aaf78578c756f46606bd9ce5bb6d00894b41cfcab528011706` |
| `docs/evidence/security-main-handoff-20261027/verification.json` | 19 | 0 | `d9b4760146883018a7425963ab18fafffeadcf2647c364b8a97cb9e509cf7b7d` |
| `docs/evidence/security-review-20261026/README.md` | 1 | 0 | `833ff2ff6d06def62757ba60cd4dd979b01ac4207b36a04b49eaaa192c0ef10d` |
| `docs/evidence/security-review-20261026/verification.json` | 1 | 0 | `7d1700052b5fb6dc40beaddb41d0d5645697df8ddb1e768768d176cb9fb80862` |
