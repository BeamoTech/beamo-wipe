// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestBootKeyTableParses(t *testing.T) {
	if bootKeysErr != nil {
		t.Fatalf("embedded bootkeys.json: %v", bootKeysErr)
	}
	for _, b := range bootKeys.Brands {
		for _, src := range b.Sources {
			if !strings.HasPrefix(src, "https://") {
				t.Errorf("%s: source %q is not an https link", b.ID, src)
			}
		}
	}
}

func TestBootKeyTableRejectsBadData(t *testing.T) {
	for name, data := range map[string]string{
		"unknown field":  `{"schema":"beamo-wipe-boot-keys/1","surprise":1}`,
		"wrong schema":   `{"schema":"other","brands":[]}`,
		"trailing":       string(bootKeysJSON) + `{}`,
		"unnormalized":   strings.Replace(string(bootKeysJSON), `"match": ["dell"]`, `"match": ["Dell Inc."]`, 1),
		"missing source": strings.Replace(string(bootKeysJSON), `"sources": ["https://www.dell.com/support/kbdoc/en-us/000126121"]`, `"sources": []`, 1),
		"bad join":       strings.Replace(string(bootKeysJSON), `"join": "then"`, `"join": "and"`, 1),
	} {
		if _, err := parseBootKeys([]byte(data)); err == nil {
			t.Errorf("%s: accepted", name)
		}
	}
}

func TestNormalizeVendor(t *testing.T) {
	for in, want := range map[string]string{
		"ASUSTeK COMPUTER INC.":    "asustek computer inc",
		"Hewlett-Packard":          "hewlett packard",
		"  Dell Inc.  ":            "dell inc",
		"To Be Filled By O.E.M.":   "to be filled by o e m",
		"Micro-Star International": "micro star international",
		"":                         "",
		"\x00\t":                   "",
	} {
		if got := normalizeVendor(in); got != want {
			t.Errorf("normalizeVendor(%q) = %q, want %q", in, got, want)
		}
	}
}

// The messy strings WMI and SMBIOS really report (#184).
func TestDetectBrandFromReportedStrings(t *testing.T) {
	cases := []struct {
		m    machineInfo
		want string
		from string
	}{
		{machineInfo{Manufacturer: "LENOVO", Model: "20XW0026US"}, "Lenovo", "manufacturer"},
		{machineInfo{Manufacturer: "Hewlett-Packard", Model: "HP EliteBook 840 G3"}, "HP", "manufacturer"},
		{machineInfo{Manufacturer: "HP", Model: "HP ProBook 450 G8"}, "HP", "manufacturer"},
		{machineInfo{Manufacturer: "Dell Inc.", Model: "Latitude 5420"}, "Dell", "manufacturer"},
		{machineInfo{Manufacturer: "ASUSTeK COMPUTER INC.", Model: "VivoBook"}, "ASUS", "manufacturer"},
		{machineInfo{Manufacturer: "ASUS", Model: "ROG"}, "ASUS", "manufacturer"},
		{machineInfo{Manufacturer: "Micro-Star International Co., Ltd.", Model: "MS-7C02"}, "MSI", "manufacturer"},
		{machineInfo{Manufacturer: "Acer", Model: "Aspire A515-54"}, "Acer", "manufacturer"},
		{machineInfo{Manufacturer: "Gigabyte Technology Co., Ltd.", Model: "B550"}, "Gigabyte", "manufacturer"},
		// Self-built computers often keep the firmware placeholder; the
		// motherboard vendor is the brand that chose the boot-menu key.
		{machineInfo{Manufacturer: "To Be Filled By O.E.M.", Board: "ASUSTeK COMPUTER INC."}, "ASUS", "motherboard"},
		{machineInfo{Manufacturer: "System manufacturer", Board: "Micro-Star International Co., Ltd."}, "MSI", "motherboard"},
		{machineInfo{Manufacturer: "", Board: "Gigabyte Technology Co., Ltd."}, "Gigabyte", "motherboard"},
		{machineInfo{Manufacturer: "Default string", Board: "Default string"}, "", ""},
		{machineInfo{Manufacturer: "To Be Filled By O.E.M.", Board: "To Be Filled By O.E.M."}, "", ""},
		{machineInfo{}, "", ""},
		{machineInfo{Manufacturer: "   "}, "", ""},
		// A named but unknown vendor never falls back to the board.
		{machineInfo{Manufacturer: "Framework", Board: "Dell Inc."}, "", ""},
		{machineInfo{Manufacturer: "Microsoft Corporation", Model: "Surface Laptop 4"}, "", ""},
		{machineInfo{Manufacturer: "QEMU", Model: "Standard PC (Q35 + ICH9, 2009)"}, "", ""},
		// Apple is in the table for the Boot helper only; the launcher
		// does not run on macOS and never shows a Mac hint.
		{machineInfo{Manufacturer: "Apple Inc.", Model: "MacBookPro16,1"}, "", ""},
		// Whole words only: "Dellwood" and "Shpritz" name no brand.
		{machineInfo{Manufacturer: "Dellwood Systems"}, "", ""},
		{machineInfo{Manufacturer: "Shpritz"}, "", ""},
		// Two brands in one string is ambiguous, so no hint.
		{machineInfo{Manufacturer: "Dell HP joint"}, "", ""},
	}
	for _, c := range cases {
		b, from, ok := detectBrand(bootKeys, c.m)
		if ok != (c.want != "") || b.Name != c.want || from != c.from {
			t.Errorf("detectBrand(%+v) = %q from %q ok=%v, want %q from %q", c.m, b.Name, from, ok, c.want, c.from)
		}
	}
}

func TestWithBootKeyHintNeverClaimsCertainty(t *testing.T) {
	v := withBootKey(view{Technical: "base"}, machineInfo{Manufacturer: "Dell Inc.", Model: "Latitude 5420"}, nil)
	if v.BootKey == nil || v.BootKey.Brand != "Dell" || v.BootKey.Hint != "Most Dell computers: press F12 at power-on." {
		t.Fatalf("Dell hint = %+v", v.BootKey)
	}
	if !strings.HasPrefix(v.Technical, "base\nBoot-menu key: Dell (from the reported manufacturer)") || !strings.Contains(v.Technical, "Reported model: Latitude 5420") {
		t.Fatalf("technical = %q", v.Technical)
	}
	hp := withBootKey(view{}, machineInfo{Manufacturer: "Hewlett-Packard"}, nil)
	if hp.BootKey.Hint != "Most HP computers: press Esc, then F9 at power-on." {
		t.Fatalf("HP hint = %q", hp.BootKey.Hint)
	}
	lenovo := withBootKey(view{}, machineInfo{Manufacturer: "LENOVO"}, nil)
	if !strings.Contains(lenovo.BootKey.Note, "Novo") {
		t.Fatalf("Lenovo note = %q", lenovo.BootKey.Note)
	}
	for _, b := range bootKeys.Brands {
		for _, word := range []string{"always", "guarantee", "certain", "will work"} {
			if strings.Contains(strings.ToLower(b.Note), word) {
				t.Errorf("%s note claims certainty: %q", b.ID, b.Note)
			}
		}
	}
}

func TestWithBootKeyUnknownOrUnreadShowsTable(t *testing.T) {
	unknown := withBootKey(view{}, machineInfo{Manufacturer: "To Be Filled By O.E.M."}, nil)
	if unknown.BootKey == nil || unknown.BootKey.Brand != "" || unknown.BootKey.Hint != "" {
		t.Fatalf("unknown brand got a hint: %+v", unknown.BootKey)
	}
	if !strings.Contains(unknown.Technical, "not recognized") || !strings.Contains(unknown.Technical, "Reported manufacturer: To Be Filled By O.E.M.") {
		t.Fatalf("technical = %q", unknown.Technical)
	}
	unread := withBootKey(view{}, machineInfo{Manufacturer: "Dell Inc."}, errors.New("WMI failed"))
	if unread.BootKey.Hint != "" || !strings.Contains(unread.Technical, "brand not read") || strings.Contains(unread.Technical, "Dell") {
		t.Fatalf("unread = %+v %q", unread.BootKey, unread.Technical)
	}
}

func TestReportedStringsAreBoundedAndPrintable(t *testing.T) {
	if got := reported("  a\x00b\nc  "); got != "a b c" {
		t.Fatalf("reported = %q", got)
	}
	if got := reported(""); got != "not reported" {
		t.Fatalf("empty = %q", got)
	}
	if got := reported(strings.Repeat("x", 200)); len([]rune(got)) != 65 {
		t.Fatalf("long = %d runes", len([]rune(got)))
	}
}

func TestParseMachineJSON(t *testing.T) {
	m, err := parseMachineJSON([]byte("\xef\xbb\xbf{\"manufacturer\":\"Dell Inc.\",\"model\":\"OptiPlex 7090\",\"board\":\"Dell Inc.\"}\r\n"))
	if err != nil || m.Manufacturer != "Dell Inc." || m.Model != "OptiPlex 7090" || m.Board != "Dell Inc." {
		t.Fatalf("parse = %+v, %v", m, err)
	}
	for _, bad := range []string{"", "{", `{"manufacturer":"x","serial":"y"}`, `{"manufacturer":"x"}{}`, `[]`} {
		if _, err := parseMachineJSON([]byte(bad)); err == nil {
			t.Errorf("accepted %q", bad)
		}
	}
}

func TestReadDMIUsesInjectedReader(t *testing.T) {
	files := map[string]string{"sys_vendor": "LENOVO\n", "product_name": "21AH\n", "board_vendor": "LENOVO\n", "product_serial": "SECRET"}
	var asked []string
	m, err := readDMI(func(name string) ([]byte, error) {
		asked = append(asked, name)
		if v, ok := files[name]; ok {
			return []byte(v), nil
		}
		return nil, os.ErrNotExist
	})
	if err != nil || m != (machineInfo{Manufacturer: "LENOVO", Model: "21AH", Board: "LENOVO"}) {
		t.Fatalf("readDMI = %+v, %v", m, err)
	}
	for _, name := range asked {
		if strings.Contains(name, "serial") || strings.Contains(name, "uuid") {
			t.Fatalf("read a root-only identity file %q", name)
		}
	}
	if _, err := readDMI(func(string) ([]byte, error) { return nil, os.ErrPermission }); err == nil {
		t.Fatal("no DMI files must be an error")
	}
	partial, err := readDMI(func(name string) ([]byte, error) {
		if name == "board_vendor" {
			return []byte("ASUSTeK COMPUTER INC.\n"), nil
		}
		return nil, os.ErrNotExist
	})
	if err != nil || partial.Board != "ASUSTeK COMPUTER INC." || partial.Manufacturer != "" {
		t.Fatalf("partial = %+v, %v", partial, err)
	}
}

func TestReadMachineBoundedStopsAHungReader(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	release := make(chan struct{})
	defer close(release)
	start := time.Now()
	_, err := readMachineBounded(ctx, func(context.Context) (machineInfo, error) {
		<-release
		return machineInfo{Manufacturer: "Dell Inc."}, nil
	})
	if err == nil || time.Since(start) > 5*time.Second {
		t.Fatalf("hung reader: err=%v after %v", err, time.Since(start))
	}
	if _, err := readMachineBounded(context.Background(), nil); !errors.Is(err, errMachineUnsupported) {
		t.Fatalf("nil reader = %v", err)
	}
}

// The check endpoint reads the brand through the injected reader once, and
// tries again only after a failed read.
func TestCheckReadsBrandOnceThroughInjectedReader(t *testing.T) {
	var calls atomic.Int32
	fail := atomic.Bool{}
	fail.Store(true)
	a := &app{token: strings.Repeat("a", 64), host: "127.0.0.1:1", probe: func(context.Context) Snapshot { return Snapshot{Problem: "legacy"} },
		machine: func(context.Context) (machineInfo, error) {
			calls.Add(1)
			if fail.Load() {
				return machineInfo{}, errors.New("WMI unavailable")
			}
			return machineInfo{Manufacturer: "Dell Inc.", Model: "Latitude"}, nil
		}, close: make(chan struct{})}
	check := func() view {
		req := httptest.NewRequest("POST", "http://127.0.0.1:1/api/check", strings.NewReader(`{}`))
		req.Host = a.host
		req.Header.Set("Origin", "http://"+a.host)
		req.Header.Set("X-Beamo-Token", a.token)
		req.Header.Set("Content-Type", "application/json")
		rec := httptest.NewRecorder()
		a.serve(rec, req)
		if rec.Code != http.StatusOK {
			t.Fatalf("check = %d %s", rec.Code, rec.Body)
		}
		var v view
		if err := json.Unmarshal(rec.Body.Bytes(), &v); err != nil {
			t.Fatal(err)
		}
		return v
	}
	if v := check(); v.BootKey == nil || v.BootKey.Hint != "" {
		t.Fatalf("failed read showed a hint: %+v", v.BootKey)
	}
	fail.Store(false)
	if v := check(); v.BootKey == nil || v.BootKey.Brand != "Dell" {
		t.Fatalf("second check = %+v", v.BootKey)
	}
	if v := check(); v.BootKey.Brand != "Dell" || calls.Load() != 2 {
		t.Fatalf("brand re-read: calls=%d", calls.Load())
	}
}
