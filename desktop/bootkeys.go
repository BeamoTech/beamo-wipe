// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"bytes"
	"context"
	_ "embed"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"
	"time"
	"unicode"
	"unicode/utf8"
)

// bootkeys.json is the one boot-menu key table (#184). The Boot helper pages,
// this launcher's page and docs/boot-card.md are generated from it by
// scripts/gen_boot_keys.py; tests fail when any of them drifts.
//
//go:embed bootkeys.json
var bootKeysJSON []byte

type bootKeyBrand struct {
	ID            string            `json:"id"`
	Name          string            `json:"name"`
	LocalizedName map[string]string `json:"localized_name"`
	Match         []string          `json:"match"`
	Keys          []string          `json:"keys"`
	Join          string            `json:"join"`
	Suffix        map[string]string `json:"suffix"`
	Note          string            `json:"note"`
	Launcher      bool              `json:"launcher"`
	Sources       []string          `json:"sources"`
}

type bootKeyTable struct {
	Schema       string                       `json:"schema"`
	Reviewed     string                       `json:"reviewed"`
	About        string                       `json:"about"`
	Placeholders []string                     `json:"placeholders"`
	Words        map[string]map[string]string `json:"words"`
	Brands       []bootKeyBrand               `json:"brands"`
}

func parseBootKeys(data []byte) (bootKeyTable, error) {
	var t bootKeyTable
	dec := json.NewDecoder(bytes.NewReader(data))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&t); err != nil {
		return t, err
	}
	if dec.Decode(&struct{}{}) != io.EOF {
		return t, errors.New("trailing boot-key data")
	}
	if t.Schema != "beamo-wipe-boot-keys/1" || len(t.Brands) == 0 {
		return t, errors.New("unsupported boot-key table")
	}
	en := t.Words["en"]
	if en["or"] == "" || en["then"] == "" || !strings.Contains(en["launcher_hint"], "{brand}") || !strings.Contains(en["launcher_hint"], "{keys}") {
		return t, errors.New("boot-key table lacks English words")
	}
	seen := map[string]bool{}
	for _, b := range t.Brands {
		if b.ID == "" || seen[b.ID] || b.Name == "" || len(b.Match) == 0 || len(b.Keys) == 0 || len(b.Sources) == 0 || (b.Join != "or" && b.Join != "then") {
			return t, fmt.Errorf("incomplete boot-key brand %q", b.ID)
		}
		seen[b.ID] = true
		for _, m := range b.Match {
			if normalizeVendor(m) != m {
				return t, fmt.Errorf("brand %q match %q is not normalized", b.ID, m)
			}
		}
	}
	return t, nil
}

var bootKeys, bootKeysErr = parseBootKeys(bootKeysJSON)

// normalizeVendor lowercases a firmware string and keeps letters and digits as
// space-separated words: "ASUSTeK COMPUTER INC." -> "asustek computer inc".
func normalizeVendor(s string) string {
	var b strings.Builder
	gap := false
	for _, r := range strings.ToLower(s) {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			if gap && b.Len() > 0 {
				b.WriteByte(' ')
			}
			gap = false
			b.WriteRune(r)
		} else {
			gap = true
		}
	}
	return b.String()
}

// placeholderVendor reports a firmware default such as "To Be Filled By
// O.E.M." or an empty value. Those name no brand.
func placeholderVendor(t bootKeyTable, s string) bool {
	n := normalizeVendor(s)
	if n == "" {
		return true
	}
	for _, p := range t.Placeholders {
		if normalizeVendor(p) == n {
			return true
		}
	}
	return false
}

// brandForVendor returns the one launcher brand whose match phrase appears as
// whole words in the vendor string. No match or several matches name no brand.
func brandForVendor(t bootKeyTable, vendor string, launcherOnly bool) (bootKeyBrand, bool) {
	if placeholderVendor(t, vendor) {
		return bootKeyBrand{}, false
	}
	words := " " + normalizeVendor(vendor) + " "
	var found []bootKeyBrand
	for _, b := range t.Brands {
		if launcherOnly && !b.Launcher {
			continue
		}
		for _, m := range b.Match {
			if strings.Contains(words, " "+m+" ") {
				found = append(found, b)
				break
			}
		}
	}
	if len(found) != 1 {
		return bootKeyBrand{}, false
	}
	return found[0], true
}

// machineInfo is what the computer reports about itself without elevation:
// Windows WMI Win32_ComputerSystem/Win32_BaseBoard or Linux
// /sys/class/dmi/id. Serial numbers are never read.
type machineInfo struct {
	Manufacturer string `json:"manufacturer"`
	Model        string `json:"model"`
	Board        string `json:"board"`
}

var errMachineUnsupported = errors.New("computer brand is not read on this platform")

// detectBrand prefers the system manufacturer. Only when that is empty or a
// firmware placeholder (common on self-built computers) does it fall back to
// the motherboard vendor.
func detectBrand(t bootKeyTable, m machineInfo) (bootKeyBrand, string, bool) {
	if b, ok := brandForVendor(t, m.Manufacturer, true); ok {
		return b, "manufacturer", true
	}
	if placeholderVendor(t, m.Manufacturer) {
		if b, ok := brandForVendor(t, m.Board, true); ok {
			return b, "motherboard", true
		}
	}
	return bootKeyBrand{}, "", false
}

func joinKeys(keys []string, join string, words map[string]string) string {
	if join == "then" {
		return strings.Join(keys, words["then"])
	}
	return strings.Join(keys, words["or"])
}

type bootKeyView struct {
	Brand string `json:"brand"`
	Hint  string `json:"hint"`
	Note  string `json:"note"`
}

// reported keeps firmware text printable and short for Technical details.
func reported(s string) string {
	var b strings.Builder
	for _, r := range strings.TrimSpace(s) {
		if !unicode.IsPrint(r) {
			r = ' '
		}
		b.WriteRune(r)
	}
	out := strings.Join(strings.Fields(b.String()), " ")
	if utf8.RuneCountInString(out) > 64 {
		out = string([]rune(out)[:64]) + "…"
	}
	if out == "" {
		return "not reported"
	}
	return out
}

// withBootKey adds the brand hint. Unknown brands get no hint, and the page
// shows the full table instead. The wording never claims certainty.
func withBootKey(v view, m machineInfo, readErr error) view {
	v.BootKey = &bootKeyView{}
	line := "Boot-menu key: not recognized; the page shows the typical keys"
	if bootKeysErr != nil {
		line = "Boot-menu key: table unavailable"
	} else if readErr != nil {
		line = "Boot-menu key: computer brand not read; the page shows the typical keys"
	} else if b, from, ok := detectBrand(bootKeys, m); ok {
		en := bootKeys.Words["en"]
		hint := strings.NewReplacer("{brand}", b.Name, "{keys}", joinKeys(b.Keys, b.Join, en)).Replace(en["launcher_hint"])
		v.BootKey = &bootKeyView{Brand: b.Name, Hint: hint, Note: b.Note}
		line = fmt.Sprintf("Boot-menu key: %s (from the reported %s)", b.Name, from)
	}
	if readErr == nil {
		line += fmt.Sprintf("\nReported manufacturer: %s\nReported model: %s\nReported motherboard vendor: %s", reported(m.Manufacturer), reported(m.Model), reported(m.Board))
	}
	if v.Technical != "" {
		v.Technical += "\n"
	}
	v.Technical += line
	return v
}

// parseMachineJSON reads the Windows reader's one compact JSON object.
func parseMachineJSON(data []byte) (machineInfo, error) {
	var m machineInfo
	dec := json.NewDecoder(bytes.NewReader(bytes.TrimPrefix(data, []byte("\xef\xbb\xbf"))))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&m); err != nil {
		return machineInfo{}, err
	}
	if dec.Decode(&struct{}{}) != io.EOF {
		return machineInfo{}, errors.New("trailing computer data")
	}
	return m, nil
}

// readDMI reads the Linux SMBIOS strings that any user may read. Missing
// files are allowed; all three missing is an error.
func readDMI(read func(name string) ([]byte, error)) (machineInfo, error) {
	var m machineInfo
	found := false
	for _, f := range []struct {
		name string
		dst  *string
	}{{"sys_vendor", &m.Manufacturer}, {"product_name", &m.Model}, {"board_vendor", &m.Board}} {
		b, err := read(f.name)
		if err != nil {
			continue
		}
		found = true
		*f.dst = strings.TrimSpace(string(b))
	}
	if !found {
		return machineInfo{}, errors.New("no DMI identity files")
	}
	return m, nil
}

const machineReadTimeout = 20 * time.Second

// readMachineBounded runs an injected reader with its own deadline. A reader
// that never returns cannot hold the readiness check open.
func readMachineBounded(parent context.Context, reader func(context.Context) (machineInfo, error)) (machineInfo, error) {
	if reader == nil {
		return machineInfo{}, errMachineUnsupported
	}
	ctx, cancel := context.WithTimeout(parent, machineReadTimeout)
	defer cancel()
	type result struct {
		m   machineInfo
		err error
	}
	done := make(chan result, 1)
	go func() {
		m, err := reader(ctx)
		done <- result{m, err}
	}()
	select {
	case r := <-done:
		return r.m, r.err
	case <-ctx.Done():
		return machineInfo{}, ctx.Err()
	}
}
