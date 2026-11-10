# Owner answers: UI review wording and layout questions (2026-11-10)

> **Status: DECIDED 2026-11-10.** On 2026-11-10 the owner directed: apply the
> recommended option for every open wording and decision item from the
> 2026-11 UI review (#127–#187, merged in PR 94) and record the choice.
> Recorded by Claude (Opus 5.5) on branch `fix/owner-decisions-20261110`.

Each answer below keeps behaviour that is already built and tested, unless it
says otherwise. Native-speaker review of the FR/DE/ES/IT drafts is still open.
These answers do not replace that review.

| Item | Question | Answer (recommended option) | Change made |
| --- | --- | --- | --- |
| #184 | Approve HP "Esc, then F9" and ASUS "Esc or F8"? The runbook and compatibility matrix still said "HP F9/Esc". | **Approved.** `desktop/bootkeys.json` stays the one key table. | `docs/runbook.md` and `docs/compatibility-matrix.md` FW-06 now match the table. |
| #185 | Approve "This computer's disk" (the glossary bans "PC")? | **Approved.** | None. |
| #185 | Show the VMD hint when VMD is bound but no NVMe controller is visible? | **Yes, keep showing it.** The text already says the disk "may be hidden", and the hint is display only. Selection and boot exclusion are unchanged. | None. |
| #186 | The 8 decisions in §12 of `docs/decisions/ssd-firmware-erase.md`. | **Option A:** keep the nwipe overwrite only. The answer to each point is recorded in that file. | Decision record updated. No code or claims change. |
| #180f | Rename the evidence text "nwipe exited without wiping"? | **Keep it.** It is saved evidence text that older reports and checks rely on. It is not shown as a screen message. | None. |
| #177g | A 55-character serial wraps one row sooner at Large/Extra because of letter spacing. | **Accept.** Letter spacing makes look-alike characters easier to compare (#129, #152). | None. |
| #158 | At 800x600 standard, the Quick zero title is below the fold. | **Accept.** The owner asked not to redesign the method cards. The page scrolls, and Quick zero stays reachable by keyboard and scrolling. | None. |
| #158 | In GTK, the Storage limits button sits inside the Show more expander. | **Accept, as option (b).** The button shows once Show more is open, and the L key works in every state, the same as in Tk and on the web preview. | None. |
| Tk footer | At 800x600 Extra, the footer shows "Check disks again" / "Screen-reader view" without "(F5)/(F8)". | **Accept.** The keys still work and are listed on the Keyboard shortcuts page. They drop only when the line would otherwise wrap. | None. |
| Tk footer | DE/FR/ES/IT footers at Large/Extra need 3 rows. | **Accept 3 rows.** Moving the tools would change every screen. Revisit after native review if translations get shorter. | None. |
| Console | At 80 columns, the power badge takes priority over the step name in the header. | **Accept.** This is the #144 design: power state matters more during an erase, and the step name is still in the body. | None. |

## Still open

- Native-speaker review of FR/DE/ES/IT strings.
- Physical checks of these screens on real panels and hardware: see the
  physical acceptance packet (#116).
