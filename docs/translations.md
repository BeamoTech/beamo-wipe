# Translations

Canonical guide for the French, German, Spanish and Italian copy. English is the
source; the other languages override it. A native-speaker review is still
required before any language is called final; the checklist at the end lists
the strings that most need one.

## Languages and register

| Code | Register | Notes |
|------|----------|-------|
| `fr` | *vous* | Standard French (France). |
| `de` | *Sie* | Standard German. Terse console labels may use infinitives (`Enter: weiter`). |
| `es` | *usted* | Neutral Spanish for Spain and the Americas (see decisions below). |
| `it` | *Lei* | Standard Italian (Italy). Pronouns and possessives lower case in sentences; buttons use the usual interface imperative (see decisions below). |

Spoken output (Orca/speech), the boot menu and the kiosk recovery screen stay
English: the image has no per-language voice, so translated screens are read
with the English voice. The helper pages say so and quote those English names verbatim
(`Beamo Wipe: speech for screen readers`, `Restart computer`, `Shut down`,
`Technical details and logs`), with a translation in parentheses where useful.

## Where strings live

- `src/beamo_wipe/lang.py` applies a language. English values are the module
  attributes of `beamo_wipe.<module>`; `lang.surface()` lists every
  translated name.
- `src/beamo_wipe/locales/{fr,de,es,it}.py`: `STRINGS[module][NAME] = value`.
  Keys and tuple lengths must match English. Data only, no functions.
- `helper/{fr,de,es,it}.html`: offline START-HERE page per language, reviewed
  against `helper/index.html`.
- `src/beamo_wipe/compat_story.py` `LOCALIZED_HELPER_IDENTITY`: build-label
  sentences injected into the helper pages at image build time.

Some values are fragments joined by code; translate them so the joined text
reads naturally:

- `progress.ESTIMATE_*` follow `Estimated time remaining: ` (`REMAINING_LINE`),
  so FR/DE/ES/IT write lower-case fragments.
- `copy.SOUND_SELECTED` follows an output name (`Headphones`, `HDMI sound`…).
  FR/ES/IT use "— sortie/salida/uscita sélectionnée/seleccionada/selezionata"
  to avoid agreeing with the name; DE `ausgewählt.` does not inflect.
- `progress.duration()` joins `{value} day(s)/hour(s)/minute(s)` with no
  grammatical case, so a sentence around `{text}` must need the plain
  (nominative/accusative) form. DE `NO_UPDATE` uses a label
  (*Zeit ohne neuen Fortschritt: 2 Tage.*) because *seit* needs *Tagen*.

## Conventions

- **Stay in English:** typed console words (`YES`, `ERASE`, `STOP`,
  `KEEP`, `BACK`, `SAVE`, `REPORT`, `DIAGNOSTIC`, `SHUTDOWN`,
  `CHECK DISKS AGAIN`, …), key names (`Enter`, `Esc`, `Space`, `Shift`, `Tab`,
  `F2`, `F5`, `F8`, `Up/Down`, `Left/Right`, `PgUp/PgDn`), file names, `nwipe`,
  `Beamo Wipe`, `Secure Boot`, `BitLocker`, `Error Summary`, layout names
  (`QWERTY`, `AZERTY`, `QWERTZ`). Helper pages may add the local key cap in
  parentheses: `Shift (Maj)`, `Shift (Umschalttaste)`, `Shift (Mayús)`,
  `Shift (Maiusc)`.
- **Placeholders** (`{title}`, `{size}`, `{token}`, …) and escaped braces keep
  the same names and counts as English.
- **Cited labels:** when a sentence names a button, screen or section, use the
  exact translated label, unquoted (as English does), e.g.
  *choisissez Vérifier à nouveau les disques*. Case may follow the sentence in
  console footers.
- **"Clear" is never "erase".** Clearing a selection, preference or
  preparation is *annuler* / *zurücksetzen, verwerfen, abwählen* /
  *anular, quitar* / *annullare*, never *effacer* / *löschen* / *borrar* /
  *cancellare*.
- **Safety wording is never softened:** "cannot get files back", "files may
  still be on the disk", "do not bypass protection", "the Beamo USB stays
  protected", "not a formal certificate", "time is not promised".
- **Typography**
  - French: ordinary space before `: ; ? !` (one rule, used throughout; the
    Linux text console cannot be relied on for U+202F); typographic
    apostrophe `’`; guillemets « » with spaces, helper pages only.
  - German: „…“ in helper pages; noun capitalisation; hyphenated compounds
    with names (`Beamo-USB-Stick`, `Beamo-Wipe-Bericht`); a full sentence
    after a colon starts with a capital.
  - Spanish: every `?`/`!` has its opening `¿`/`¡`; « » in helper pages; no
    comma before *y* in short titles.
  - Italian: typographic apostrophe `’` (*l’identità*, *un’altra*); no space
    before `? ! ; :`; « » without inner spaces in helper pages; `È`, never
    `E’`.

## Glossary

| English | French | German | Spanish | Italian | Why |
|---|---|---|---|---|---|
| USB stick / the Beamo USB | clé USB / la clé USB Beamo | USB-Stick / der Beamo-USB-Stick | memoria USB / la memoria USB Beamo | chiavetta USB / la chiavetta USB Beamo | ES: understood everywhere; *pendrive* is regional |
| *(not used: boot USB — say the Beamo USB, #180)* | *not* clé USB de démarrage | *not* Start-USB-Stick | *not* memoria USB de arranque | *not* chiavetta USB di avvio | one name for the stick the computer starts from; English names are in [glossary.md](glossary.md) |
| report USB | clé USB de rapport | Berichts-USB-Stick | memoria USB del informe | chiavetta USB del rapporto | |
| disk / drive | disque | Datenträger (*Festplatte* only for "hard disk") | disco (*unidad* where English says "drive") | disco (*unità* where English says "drive") | DE: covers SSD, HDD and USB |
| erase / erasure | effacer / effacement | löschen / das Löschen | borrar / borrado | cancellare / cancellazione | |
| overwrite, pass | écraser, écrasement, passe | überschreiben, Überschreibdurchgang | sobrescribir, sobrescritura, pasada | sovrascrivere, sovrascrittura, passata | |
| read-back verification | vérification par relecture | Rückleseprüfung | verificación por relectura | verifica con rilettura | |
| check / verify (a copy) | vérifier / contrôler | prüfen / verifizieren | comprobar / verificar | controllare / verificare | keeps the two export stages distinct |
| review | vérifier | prüfen | revisar | controllare (*Controllo finale* for the last screen) | |
| report / sharing copy | rapport / copie de partage | Bericht / Freigabekopie | informe / copia para compartir | rapporto / copia da condividere | |
| evidence | preuve | Nachweis | pruebas | prove | |
| the saved message | la confirmation d’enregistrement | die Speicherbestätigung | la confirmación de guardado | la conferma di salvataggio | the "saved, safe to remove" confirmation, not a stored message |
| support | l’assistance | der Support | el soporte técnico | l’assistenza | |
| shut down / restart | éteindre / redémarrer | herunterfahren / neu starten | apagar / reiniciar | spegnere / riavviare | |
| boot menu | menu de démarrage | Bootmenü (not *Startmenü*) | menú de arranque | menu di avvio | DE *Startmenü* is the Windows Start menu |
| firmware | micrologiciel | Firmware | firmware | firmware | |
| wall power / lid / sleep | secteur / capot / mise en veille | Netzstrom, Netzteil / Deckel / Ruhezustand | corriente / tapa / suspensión | alimentazione di rete, corrente / coperchio / sospensione | FR *capot* as in Windows power settings |
| wizard / helper page / launcher | assistant / aide / lanceur | Assistent / Hilfeseite / Starter | asistente / ayuda / lanzador | procedura guidata / guida / programma di avvio | FR: the helper is never *assistant* |
| keyboard layout / USB layout | disposition / structure | Tastaturlayout / Partitionierung | distribución / estructura | layout della tastiera / struttura | different concepts |
| dead keys | touches mortes | Tottasten | teclas muertas | tasti morti | |
| pinned nwipe v0.42 | la version figée nwipe v0.42 | die festgelegte Version nwipe v0.42 | la versión fija nwipe v0.42 | la versione fissata nwipe v0.42 | not *épinglé* / *angepinnt* (UI pinning) |
| Everyday / Three overwrites / Quick zero | Usage courant / Trois écrasements / Zéro rapide | Standard / Dreifaches Überschreiben / Schnelles Nullen | Habitual / Tres sobrescrituras / Rápido con ceros | Standard / Tre sovrascritture / Azzeramento rapido | *Quotidien*, *Alltag* read as "daily life" |
| Support code / Save code / Build | Code d’assistance / Code d’enregistrement / Version | Supportcode / Speichercode / Build-Kennung | Código de soporte / Código de guardado / Compilación | Codice di assistenza / Codice di salvataggio / Build | read aloud to support |
| Release build / Build status | Build de publication / État du build | Release-Build / Build-Status | Compilación de la versión / Estado de la compilación | Build di rilascio / Stato della build | report and helper use the same terms |
| withheld | masqué | zurückgehalten | omitido | omesso | |
| countdown | compte à rebours | Countdown | cuenta regresiva | conto alla rovescia | |
| Mute / Unmute (button) | Couper le son / Rétablir le son | Stummschalten / Ton einschalten | Silenciar / Activar el sonido | Disattiva l’audio / Riattiva l’audio | actions, not states |

## Spanish decisions

- **memoria USB**: neutral; *pendrive*, *USB* alone or *lápiz* are regional.
- **equipo** (not *ordenador* / *computadora*): the neutral term Microsoft
  uses in both es-ES and es-MX; avoids the Spain/Americas split.
- **cuenta regresiva** (not *cuenta atrás*): majority usage, accepted by the
  RAE and understood in Spain.
- **ratón** (not *mouse*): RAE and es-ES form, widely understood in the
  Americas.
- **presione** (not *pulse*): matches the firmware and Windows prompts users
  already see (*Presione cualquier tecla…*); *pulse* is Spain-centric.
- **Habitual** for the Everyday method: plain "the usual choice"; *Uso
  diario* reads as product usage, *Estándar* would also work.
- **Compilación** for Build: Windows Spanish calls the OS build
  *Compilación*; the report uses *Compilación de la versión*.
- **omitido** for withheld: matches *Se omiten…* in the sharing-copy notice.
- **SOUND_SELECTED** = "— salida seleccionada. …": no agreement with the
  output name; *salida* is the word used across the sound screen.

## Italian decisions

- **chiavetta USB**: the everyday term; *unità flash USB* is long and
  *pendrive* informal. Short labels may say *USB* alone, as English does.
- **Lei** with lower-case *suo*, *le*, *la* inside sentences (current formal
  usage). Where a pronoun alone would be ambiguous, rephrase:
  *Non inizia nulla senza una sua conferma*, *Interrotta su sua richiesta*.
- **Buttons** use the interface imperative of Italian Windows (*Continua*,
  *Indietro*, *Spegni*, *Cancella ora*); sentences use the Lei imperative
  (*Scelga*, *Prema*, *Digiti*) and cite labels verbatim:
  *scelga Ricontrolla i dischi*.
- **cancellare / cancellazione** for erase; **annullare** for clear and
  cancel. The two share no stem, so "clear is never erase" stays testable
  (`cancell`).
- **passata** for an overwrite pass (Italian wiping usage: *3 passate*),
  **passaggio** for an erase step (*Passaggio 2 di 3*), **passo** for a
  wizard step (*Passo 1 di 3*), **fase** for an engine phase.
- **rapporto** for report (not *report*); **prove** for evidence (not
  *evidenze*); **riferimento** for the diagnostic baseline.
- **Standard** for Everyday, as in German; *Quotidiano* reads as "daily".
- **Controllo finale** (final check) for the Review before erasing button and,
  as *Controllo finale prima di cancellare*, the last-chance title.
- **Build**: Italian Windows keeps *build* (*build del sistema operativo*);
  support hears the value read aloud.
- **non è una promessa** for "not promised"; never *garantito/garantita*
  (`tests/test_language_selection.py` lists the Italian forbidden claims).
- **Non tiri a indovinare** for "do not guess".
- Windows names follow Italian Windows 10/11: *Impostazioni → Sistema →
  Ripristino → Avvio avanzato → Riavvia ora*, *Scegli un’opzione*, *Usa un
  dispositivo*, *Riavvia il sistema* in the *Arresta* menu, *Ambiente
  ripristino Windows*.
- **SOUND_SELECTED** = "— uscita selezionata. …": no agreement with the
  output name.

## Checks

`tests/test_translation_consistency_20261027.py` (placeholders by name and
count, cited labels, key names, "clear" never "erase", Spanish opening marks,
French apostrophes and spacing, Italian apostrophes and spacing, helper pages
citing UI labels) and
`tests/test_language_selection.py` (surface coverage, typed words, no English
leaks). Layout fits: `tests/test_adaptive_layout.py`,
`tests/test_keyboard_layout.py`.

## Native review checklist

Least certain strings (key: current text). Please confirm or replace.

French
- `methods.TITLE_PRNG`: Usage courant
- `copy.METHOD_LEAD`: Choisissez le niveau d’écrasement du disque. …
- `copy.TITLE_BLOCKED`: Arrêt
- `copy.SUPPORT_SAVE_LABEL`: Code d’enregistrement (could read as "registration code")
- `copy.SUPPORT_BUILD_LABEL`: Version (labels a build id)
- `copy.CON_OWNER_FOOTER`: Space : cocher. Enter choisit un disque si la case est cochée. Esc : retour
- `storage_limits.SECTION_SUPPORTS_BODY`: … la version figée nwipe v0.42 … (secure erase) ni de nettoyage (sanitize).
- `result_summary.H_WRAPPER_COMMIT`: Commit de l’enveloppe
- `helper/fr.html`: Windows names *Utiliser un périphérique*, *Choisir une option*, *Marche/Arrêt*
- `helper/fr.html` problem guide (2026-10-28): titles *La clé USB n’apparaît pas ou n’est pas dans la liste*, *Le lanceur a échoué*; *Détail technique*; *hub de clavier*; *évite cette contrainte de temps* ("avoids that race"); *Ces vérifications n’assurent pas que la clé USB démarrera* (avoids *garantir*)

German
- `methods.TITLE_PRNG`: Standard
- `copy.TITLE_BLOCKED`: Stopp
- `copy.REPORT_HELP_TITLE`: Bericht nötig?
- `copy.HINT_DEFAULT`: Enter fährt fort.  Esc geht zurück.
- `copy.CON_OWNER_FOOTER`: Space: aktivieren. Enter wählt erst danach einen Datenträger. Esc: zurück
- `copy.SUPPORT_SAVE_LABEL`: Speichercode
- `progress.PHASE_NOTE_SYNCING`: … Dieser Schritt kann eine Weile unverändert wirken.
- `progress.NO_UPDATE`: Zeit ohne neuen Fortschritt: {text}. (label form avoids the dative *seit 2 Tagen*)
- `helper/de.html` tagline and `copy.GALLERY_NOTE`: Starthilfe
- `helper/de.html`: Windows names *Ein Gerät verwenden*, *Option auswählen*, *Ein/Aus-Menü*
- `helper/de.html` problem guide (2026-10-28): titles *Der USB-Stick wird nicht angezeigt oder fehlt in der Liste*, *Der Starter ist fehlgeschlagen*; *Technisches Detail*; *vermeidet dieses Zeitproblem* ("avoids that race"); *Diese Prüfungen stellen nicht sicher, dass der USB-Stick startet* (avoids *garantieren*); kept intro *Wählen Sie das beobachtete Problem*

Spanish
- `methods.TITLE_PRNG`: Habitual
- `copy.TITLE_BLOCKED`: Deténgase
- `copy.METHOD_LEAD`: Elija con qué minuciosidad sobrescribir el disco. …
- `copy.OWNER_CHECKBOX`: Soy el propietario de este equipo… (gendered; alternative *Este equipo y estos discos son míos…*)
- `copy.SUPPORT_SAVE_LABEL`: Código de guardado
- `copy.STARTUP_TITLE_HINT`: Preparándose.
- `progress.ESTIMATE_EARLY`: se calculará cuando haya más progreso.
- `storage_limits.SECTION_SUPPORTS_BODY`: … sanitización del controlador.
- *contacte con el soporte técnico* (*contactar con* vs *contactar a*), used in many keys

Italian
- `methods.TITLE_PRNG`: Standard
- `copy.TITLE_BLOCKED`: Si fermi
- `copy.BTN_REVIEW_ERASE` / `copy.TITLE_LAST`: Controllo finale / Controllo finale prima di cancellare
- `copy.STOP_ASK`: Interrompi la cancellazione (cited in several sentences; long for a button)
- `copy.WHAT_LEAD`: Non inizia nulla senza una sua conferma.
- `copy.SUPPORT_SAVE_LABEL`: Codice di salvataggio
- `copy.SUPPORT_BUILD_LABEL`: Build (identical to English)
- `copy.SPLASH_ROADMAP`: Scegliere un disco → Confermarne l’identità → Controllare e cancellare
- `inventory.AVAILABLE_*`: N dischi cancellabili
- `progress.ESTIMATE_EARLY`: disponibile quando ci sarà più avanzamento.
- `support_export.HELPER_*`: processo ausiliario isolato del rapporto
- `support_export.*_MALFORMED`: malformato/malformata
- `compat_story` labels: immagine USB prodotta (manufactured image)
- `helper/it.html`: Windows names *Usa un dispositivo*, *Scegli un’opzione*, *Riavvia il sistema*, menu *Arresta*, *Ambiente ripristino Windows*; defaults *non pacchettizzata/o*
- Lower-case *suo/le/la* for Lei throughout (rather than *Suo/Le/La*)
- Added after the first Italian pass, not yet reviewed with it: `copy.CONTENTS_HINT_*` (*… trovato su questo disco*), `outcomes.NEXT_*` per-result next steps (*Valuti di sostituirlo o di distruggerlo fisicamente*, *Se si ripete*), `inventory.CANNOT_ERASE` (*Impossibile cancellare:*), `progress.OLD_PERCENT` (*non recente*), `copy.ACCESSIBLE_SELECT_DISK` (*Seleziona*) and `result_summary.H_RANDOM_GENERATOR` (*Generatore di dati casuali*)

All languages (added 2026-11-02 for #128, not yet reviewed)
- `copy.ERASE_EVERYTHING`, `copy.ERASE_EVERYTHING_WINDOWS`, `copy.ERASE_EVERYTHING_SYSTEM`
  and `copy.ERASE_CANNOT_UNDO`: the one erase warning on Confirm and Review.
  `{disk}` is the model and size (Review adds the serial), so the sentence must
  read naturally with a comma-separated name in that slot. FR *Vous ne pourrez
  pas le récupérer* (*le* = *tout le contenu*), DE *Sie bekommen nichts davon
  zurück*, ES *No podrá recuperarlo*, IT *Non potrà recuperarlo*.
- `copy.WHAT_BULLETS[0:2]` and the first paragraph of each `helper/*.html`
  "What this USB does" card: the Owner sentence about what the tool does and
  the backup reminder.
- `copy.CONFIRM_SERIAL_END`, `CONFIRM_SERIAL_ALL`, `CONFIRM_HARDWARE_END`,
  `CONFIRM_HARDWARE_ALL`, `CONFIRM_LONGER`, `CONFIRM_MARKED` and
  `CONFIRM_MARKED_CONSOLE` (added 2026-11-02 for #129, not yet reviewed): the
  Confirm instruction. It must name the same field as `identity.SERIAL_LABEL`
  / `HARDWARE_ID_LABEL` in the card; *{count}* is a numeral; the console
  string must keep literal [brackets]. FR *soulignés*, DE *unterstrichen*,
  ES *subrayados*, IT *sottolineati* refer to the marked characters.
- `copy.STEP_NAME_KEYBOARD` … `STEP_NAME_REVIEW`, `STEP_CAPTION` and
  `STEP_SPOKEN` (added 2026-11-02 for #130, not yet reviewed): the step
  bar's step names. `STEP_NAME_REVIEW` is *Final check* (#166, 2026-11-05; FR
  *Dernière vérification*, DE *Letzte Prüfung*, ES *Última comprobación*, IT
  *Controllo finale*, drafts) and must never contain the erase verb (#138):
  it is the last step before the Erase stage. Keep `{n}`, `{total}`,
  `{name}` and `{stage}`; the caption must fit the 800 px header (it is
  shortened to `STEP_OF` when it does not).
- `copy.ROADMAP_STAGE_STEPS` (2026-11-03 for #138, not yet reviewed): the
  start-screen roadmap's first stage, "{stage} ({count} steps)". The roadmap
  is otherwise the `JOURNEY_LABELS` stage names, so it matches the header.
- `copy.HINT_KEYBOARD`, `KEYBOARD_AUTO`, `KEYBOARD_AUTO_ALT`,
  `KEYBOARD_AUTO_OTHER`, `KEYBOARD_KEPT` and `KEYBOARD_STAYS` (changed or added
  2026-11-02 for #131, not yet reviewed): keep the literal key words
  `Left/Right`, `Up/Down`, `Tab` and `Enter` (the Tk and web views turn the
  first two into key caps) and the `{layout}`, `{language}` and `{alt}`
  slots, which take the translated layout title and the language's own name.
  `lang.LANGUAGE_WORDS` (the picker label) is deliberately not translated: it
  is the word *Language* in every offered language.
- `progress.GLANCE_*` (added 2026-11-02 for #132, not yet reviewed): the
  Working screen's three lines and the calm *Starting…* word. `{text}` takes
  `progress.duration()` output, so the sentence needs the plain case: DE uses
  the label *Laufzeit: {text}* (not *seit*, which would need *Tagen*); FR/ES/IT
  time-left lines avoid agreeing with the unit (*Encore environ…*, *Tiempo
  restante: aproximadamente…*, *Tempo rimanente: circa…*). Keep `{i}` / `{n}`;
  IT uses *passata* there because `STAGE_STEP` already says *Passaggio*.
- `copy.FINISH_SOUND_TOGGLE`, `WALK_AWAY_BEEP`, `WALK_AWAY_QUIET`,
  `WALK_AWAY_NO_SOUND`, `FINISH_SOUND_REASON_*` and `FINISH_SOUND_STATE_*`
  (added 2026-11-03 for #133, not yet reviewed): the Working screen's
  finish-sound check box, walk-away line and reasons. Only `WALK_AWAY_BEEP`
  may promise a sound. The `FINISH_SOUND_STATE_*` values must start with the
  exact `FINISH_SOUND_TOGGLE` text (the console prints them as its state).
- `outcomes.HEADLINE_*`, `NOTE_VERIFIED`, `NOTE_UNVERIFIED`, `WHAT_NEXT` and
  `NEXT_ITEM_*` (added 2026-11-03 for #134, owner-approved English, not yet
  reviewed): the result screen's plain headline, note and What next list.
  The `MSG_*` status messages are unchanged (evidence, report, photo record).
  Quick zero's headline and note must never say checked or verified (FR/DE/ES/
  IT: *non vérifié*, *nicht geprüft*, *sin comprobar*, *non controllato*);
  nothing may promise data cannot be recovered. `NEXT_ITEM_GIVE_UNVERIFIED`
  keeps `{method}` (the Everyday name), quoted in each language's style.
- `inventory.COMPARE_SERIAL_OTHER`, `COMPARE_SERIAL_SIMILAR_ONE`,
  `COMPARE_SERIAL_SIMILAR_MANY`, `POSITION_MANY`, `POSITION_ITEM_RANGE`,
  `POSITION_AND` (2026-11-04 for #152, replacing #148's `COMPARE_SERIAL`;
  drafts, not yet reviewed): the Pick a disk note under a serial whose
  differing characters are marked, also spoken by Orca. Each keeps `{size}`
  (the capacity phrase, e.g. "256 GB"), `{position}` and `{reminder}`.
  OTHER is used when exactly one other disk has that size ("the other 256 GB
  disk"); SIMILAR_ONE/MANY when there are more, naming only the look-alike
  ones. `{position}` comes from `POSITION_ONE`/`POSITION_RANGE`, or for
  several runs `POSITION_MANY` with items such as "7", "11 to 14"
  (`POSITION_ITEM_RANGE`) joined by ", " and `POSITION_AND`. The note must
  never repeat the serial's characters; the card shows them once.
- `progress.GLANCE_STARTED_AGO`, `GLANCE_STARTED_AT`, `GLANCE_ABOUT_LEFT`,
  `GLANCE_LESS_LEFT`, `GLANCE_EXPECTED_AT`, `CLOCK_STYLE`, `CLOCK_AM`,
  `CLOCK_PM` (2026-11-05 for #167, replacing `GLANCE_RUNNING`; drafts, not
  yet reviewed): the Working time line, joined by " · ". Keep `{text}`
  (a duration) and `{time}` (a time of day); the part after the separator
  starts in lower case where the language allows. `CLOCK_STYLE` is "12"
  (2:02 PM) or "24" (14:02); FR/DE/ES/IT use "24". Never promise a
  finish time: *expected around*, *voraussichtlich*, *prévue*, *previsto*.
- `copy.REVIEW_METHOD_LINE` (2026-11-05 for #164; drafts, not yet reviewed):
  Review's one method line, `{method}` (the method title) and `{operation}`
  (`methods.OPERATION_*`, which already say whether verification follows).
  Keep both placeholders; French spaces the colon ("{method} : {operation}").
- `copy.COUNTDOWN_READY_WORD`, `copy.COUNTDOWN_AVAILABLE` (2026-11-05 for #163;
  drafts, not yet reviewed): the Review ready state, "Ready" beside the
  ring's check mark and "Erase now is available." spoken by Orca.
  `COUNTDOWN_AVAILABLE` names the language's own `BTN_ERASE` (a test checks
  it); `COUNTDOWN_READY_WORD` is one short word with no number.
- `copy.LAST_LEAD` (2026-11-05 for #162; drafts, not yet reviewed): the
  Review before erasing lead now says what starts the erase ("Erasing starts
  only when you press Erase now."). Name the language's own `BTN_ERASE`
  label exactly, unquoted as in `COUNTDOWN_READY`; never imply the
  countdown starts anything.
- `methods.MARK_RARELY_NEEDED` (replacing `MARK_MORE_OVERWRITES`) and
  `methods.EXTRA_WORK_DOD` (2026-11-05 for #161; English awaiting owner
  sign-off, translations drafts, not yet reviewed): Three overwrites' chip
  "Rarely needed" and its Show more explanation. Keep `{everyday}` (the
  Everyday name, used twice), "DoD" untranslated, and the sentence that it
  is not a DoD certificate; never "DoD certified", never promise that
  more passes reach hidden storage.
- `copy.TIME_GUIDE_UNKNOWN` (2026-11-05 for #159; drafts, not yet reviewed):
  the method card's time line when no range can be given ("Time depends on
  the disk."). No number, no promise and no guess at a duration.
- `copy.TOKEN_TYPED`, `TOKEN_WRONG_ONE`/`_MANY`, `TOKEN_MISSING_ONE`/`_MANY`,
  `TOKEN_EXTRA_ONE`/`_MANY`, `TOKEN_SPACE_NOTE`, `TOKEN_SPACE_WORD` (2026-11-04
  for #156; drafts, not yet reviewed): Confirm's wrong-entry feedback.
  Placeholders: `{typed}`, `{n}`, `{list}` (joined with
  `inventory.POSITION_AND`), `{count}`. Never add the expected characters.
- `copy.CONFIRM_LAYOUT_HINT`, `CONFIRM_LAYOUT_CHANGE`, `CON_CONFIRM_LAYOUT_KEY`
  (2026-11-04 for #155, replacing `CONFIRM_KEYBOARD_LINE`; drafts, not yet
  reviewed): Confirm's help after a wrong entry. The hint keeps `{layout}`
  (the layout's own title) and nothing else; the console key text keeps F2.
- `inventory.TAG_BITLOCKER`, `inventory.TAG_LUKS` (2026-11-04 for #154; drafts,
  not yet reviewed): pick-card tags "BitLocker (Windows encryption)" and
  "Encrypted (LUKS)". Keep the product names BitLocker and LUKS; never add
  words about unlocking, keys, passwords or recovery (out of scope per
  docs/claims.md). A test rejects those words in every language.
- `copy.HINT_PICK`, `copy.HINT_CONFIRM` (2026-11-04 for #153; drafts, not yet
  reviewed): footer hints whose key names (`Up/Down`, `Enter`, `Esc`) become
  key-caps. No sentence may end on a key name (no `.`, `,`, `;`, `:` right
  after it): "use Up/Down to choose one", "press Enter to continue". A test
  checks every language.
- `inventory.ROLE_EFI`, `ROLE_MSR`, `ROLE_RECOVERY`, `FORMAT_UNKNOWN`,
  `FORMAT_BITLOCKER`, `FORMAT_LUKS`, `ITEM_NAMED`, `MORE_COUNT` (2026-11-03 for
  #147, not yet reviewed): the Pick a disk contents line. `ITEM_NAMED` keeps
  `{name}`, `{format}` and `{size}` and quotes the untrusted volume name in the
  language's usual quote marks (« », „ “, « »); the name never appears
  unquoted. File-system names (NTFS, FAT32, exFAT, ext4, APFS, HFS+) and
  "Windows" are not translated. `MORE_COUNT` keeps `{count}`.
- `copy.REPORT_MEDIA_WHAT` (changed), `LEARN_MORE`, `LEARN_MORE_REPORT_NAME`,
  `CON_REPORT_LEARN` (2026-11-03 for #145, not yet reviewed): the one-line
  Owner report notice. Keep "when asked": the report USB stays unplugged
  until the result screen asks. `CON_REPORT_LEARN` starts with the key R.
- `copy.KEYBOARD_CHECK_*`, `CON_KEYBOARD_CHECK_*` and the changed
  `KEYBOARD_LEAD` (2026-11-03 for #140, not yet reviewed): the guided keyboard
  check. "Z" is the key label printed on the keyboard; keep it as is. Keep
  `{layout}` and `{typed}`; the typed `SWITCH` and `F3` stay English. The match
  line promises only letters and numbers, nothing about symbols.
- `copy.SPLASH_TAGLINE` (changed 2026-11-03 for #137, not yet reviewed): the
  start screen's first line. It must name the translated `BTN_ERASE` exactly
  (tested) and stay two short sentences.
- `copy.REFRESH_GUARD_LEAD`, `REFRESH_THEN_READER`, `BTN_REFRESH_CANCEL`,
  `HINT_REFRESH_GUARD` and `CON_REFRESH_GUARD_*` (2026-11-03 for #136, not
  yet reviewed): the guarded Check disks again dialog. It must say the
  confirmations are cleared and the person starts again from choosing a
  disk; `HINT_REFRESH_GUARD` names the `BTN_REFRESH` button exactly; the
  typed `CHECK DISKS AGAIN` and the `C`, `Enter`, `Esc`, `Tab` keys stay
  English.
- `copy.REPORT_STEP_*`, `REPORT_USB_*`, `REPORT_SAVE_WAIT`,
  `REPORT_NOT_OFFERED`, `RETRY_UNAVAILABLE`, `DONE_WAIT_*`, `DONE_ANOTHER_*`,
  `CON_PANEL_*` and `CON_PLAIN_RECHECK`, plus the changed
  `REPORT_STATUS_TITLE` and `REPORT_HELP_STAGES` (2026-11-03 for #135, not
  yet reviewed): the Save a report panel and the two-action footer. Keep
  `{label}` and `{filesystem}`; filesystem names (FAT32, exFAT, NTFS) are
  not translated. Button names inside sentences must match `BTN_*` /
  `RETRY_SAVE` exactly. Key names stay English (`R`, `E`, `Enter`).
- `safety.BOOT_APPEARED_SELECTABLE`, `BOOT_APPEARED_ALIAS` (2026-11-07,
  #180 follow-up `safety:` review; drafts, not yet reviewed): the blocked
  screen's body when the Beamo USB appears as a disk to erase or under a
  second device path. Only the stick's name changed, to the Beamo USB of
  the glossary above; keep the refusal ("Refusing to continue") and never
  suggest the stick can be erased.
- Reading level (2026-11-09 for #181; drafts, not yet reviewed): long English
  sentences were split so each reads at an 8th-grade level
  (`tests/test_reading_level_181.py`). Every translation of a changed string
  was split the same way, keeping each warning and limit: `copy.POWER_EVENTS`
  (FR adds *Dans ce cas* to keep *recommencez*), `REPORT_HELP_PHOTO`,
  `REPORT_HELP_NEED` (IT now *una chiavetta USB … separata*, so *diversa*),
  `REPORT_HELP_INSERT`, `REPORT_HELP_CONTAINS`, `REPORT_HELP_START`,
  `REPORT_SHARE_REDACTED`, `ADVANCED_LOG_LEAD`, `MEDIA_STEP_UNSURE` (now two
  questions), `REFRESH_GUARD_LEAD`, `REFRESH_LEAD` (the ownership
  acknowledgement is now "unticks the ownership box"), `DISK_HELP_TEXT`,
  `SOUND_RECOVERY`; `inventory.EMPTY_STEPS`, `recovery.NEXT_EMPTY`,
  `diagnostic_report.PREPARE`; `storage_limits.OVERWRITE_LIMITS` and the
  `SECTION_*_BODY` texts of the storage limits page. Button names inside
  sentences still match `BTN_*` exactly. New key
  `storage_limits.REPORT_OVERWRITE_LIMITS` holds the earlier
  `OVERWRITE_LIMITS` translation unchanged: saved reports keep that wording,
  so do not edit it with the screens.
