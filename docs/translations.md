# Translations

Canonical guide for the French, German and Spanish copy. English is the
source; the other languages override it. A native-speaker review is still
required before any language is called final; the checklist at the end lists
the strings that most need one.

## Languages and register

| Code | Register | Notes |
|------|----------|-------|
| `fr` | *vous* | Standard French (France). |
| `de` | *Sie* | Standard German. Terse console labels may use infinitives (`Enter: weiter`). |
| `es` | *usted* | Neutral Spanish for Spain and the Americas (see decisions below). |

Spoken output (Orca/speech), the boot menu and the kiosk recovery screen stay
English. The helper pages say so and quote those English names verbatim
(`Beamo Wipe: speech for screen readers`, `Restart computer`, `Shut down`,
`Technical details and logs`), with a translation in parentheses where useful.

## Where strings live

- `src/beamo_wipe/lang.py` applies a language. English values are the module
  attributes of `beamo_wipe.<module>`; `lang.surface()` lists every
  translated name.
- `src/beamo_wipe/locales/{fr,de,es}.py`: `STRINGS[module][NAME] = value`.
  Keys and tuple lengths must match English. Data only, no functions.
- `helper/{fr,de,es}.html`: offline START-HERE page per language, reviewed
  against `helper/index.html`.
- `src/beamo_wipe/compat_story.py` `LOCALIZED_HELPER_IDENTITY`: build-label
  sentences injected into the helper pages at image build time.

Some values are fragments joined by code; translate them so the joined text
reads naturally:

- `progress.ESTIMATE_*` follow `Estimated time remaining: ` (`REMAINING_LINE`),
  so FR/DE/ES write lower-case fragments.
- `copy.SOUND_SELECTED` follows an output name (`Headphones`, `HDMI sound`…).
  FR/ES use "— sortie/salida sélectionnée/seleccionada" to avoid agreeing
  with the name; DE `ausgewählt.` does not inflect.
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
  parentheses: `Shift (Maj)`, `Shift (Umschalttaste)`, `Shift (Mayús)`.
- **Placeholders** (`{title}`, `{size}`, `{token}`, …) and escaped braces keep
  the same names and counts as English.
- **Cited labels:** when a sentence names a button, screen or section, use the
  exact translated label, unquoted (as English does), e.g.
  *choisissez Vérifier à nouveau les disques*. Case may follow the sentence in
  console footers.
- **"Clear" is never "erase".** Clearing a selection, preference or
  preparation is *annuler* / *zurücksetzen, verwerfen, abwählen* /
  *anular, quitar*, never *effacer* / *löschen* / *borrar*.
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

## Glossary

| English | French | German | Spanish | Why |
|---|---|---|---|---|
| USB stick / the Beamo USB | clé USB / la clé USB Beamo | USB-Stick / der Beamo-USB-Stick | memoria USB / la memoria USB Beamo | ES: understood everywhere; *pendrive* is regional |
| boot USB | clé USB de démarrage | Start-USB-Stick | memoria USB de arranque | |
| report USB | clé USB de rapport | Berichts-USB-Stick | memoria USB del informe | |
| disk / drive | disque | Datenträger (*Festplatte* only for "hard disk") | disco (*unidad* where English says "drive") | DE: covers SSD, HDD and USB |
| erase / erasure | effacer / effacement | löschen / das Löschen | borrar / borrado | |
| overwrite, pass | écraser, écrasement, passe | überschreiben, Überschreibdurchgang | sobrescribir, sobrescritura, pasada | |
| read-back verification | vérification par relecture | Rückleseprüfung | verificación por relectura | |
| check / verify (a copy) | vérifier / contrôler | prüfen / verifizieren | comprobar / verificar | keeps the two export stages distinct |
| review | vérifier | prüfen | revisar | |
| report / sharing copy | rapport / copie de partage | Bericht / Freigabekopie | informe / copia para compartir | |
| evidence | preuve | Nachweis | pruebas | |
| the saved message | la confirmation d’enregistrement | die Speicherbestätigung | la confirmación de guardado | the "saved, safe to remove" confirmation, not a stored message |
| support | l’assistance | der Support | el soporte técnico | |
| shut down / restart | éteindre / redémarrer | herunterfahren / neu starten | apagar / reiniciar | |
| boot menu | menu de démarrage | Bootmenü (not *Startmenü*) | menú de arranque | DE *Startmenü* is the Windows Start menu |
| firmware | micrologiciel | Firmware | firmware | |
| wall power / lid / sleep | secteur / capot / mise en veille | Netzstrom, Netzteil / Deckel / Ruhezustand | corriente / tapa / suspensión | FR *capot* as in Windows power settings |
| wizard / helper page / launcher | assistant / aide / lanceur | Assistent / Hilfeseite / Starter | asistente / ayuda / lanzador | FR: the helper is never *assistant* |
| keyboard layout / USB layout | disposition / structure | Tastaturlayout / Partitionierung | distribución / estructura | different concepts |
| dead keys | touches mortes | Tottasten | teclas muertas | |
| pinned nwipe v0.42 | la version figée nwipe v0.42 | die festgelegte Version nwipe v0.42 | la versión fija nwipe v0.42 | not *épinglé* / *angepinnt* (UI pinning) |
| Everyday / Three overwrites / Quick zero | Usage courant / Trois écrasements / Zéro rapide | Standard / Dreifaches Überschreiben / Schnelles Nullen | Habitual / Tres sobrescrituras / Rápido con ceros | *Quotidien*, *Alltag* read as "daily life" |
| Support code / Save code / Build | Code d’assistance / Code d’enregistrement / Version | Supportcode / Speichercode / Build-Kennung | Código de soporte / Código de guardado / Compilación | read aloud to support |
| Release build / Build status | Build de publication / État du build | Release-Build / Build-Status | Compilación de la versión / Estado de la compilación | report and helper use the same terms |
| withheld | masqué | zurückgehalten | omitido | |
| countdown | compte à rebours | Countdown | cuenta regresiva | |
| Mute / Unmute (button) | Couper le son / Rétablir le son | Stummschalten / Ton einschalten | Silenciar / Activar el sonido | actions, not states |

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

## Checks

`tests/test_translation_consistency_20261027.py` (placeholders by name and
count, cited labels, key names, "clear" never "erase", Spanish opening marks,
French apostrophes and spacing, helper pages citing UI labels) and
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
