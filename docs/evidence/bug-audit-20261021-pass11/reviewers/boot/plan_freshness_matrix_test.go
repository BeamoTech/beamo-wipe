package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func TestPass11PlanFreshnessMatrix(t *testing.T) {
	counts := map[string]int{"states": 0, "positive_plans": 0, "order_controls": 0, "unrelated_entry_controls": 0, "sensitive_field_changes": 0, "refusals": 0, "restored_controls": 0, "native_callbacks": 0, "mismatches": 0}
	route := "gpt:00000001-0000-0000-0000-000000000000:1:2048:4096"
	other := "gpt:00000002-0000-0000-0000-000000000000:1:2048:4096"
	fingerprints := map[string]string{}
	for _, layout := range []string{"layout-A", "layout-B", "layout-C"} {
		for _, media := range []string{"usb-A", "usb-B", "usb-C"} {
			for _, secure := range []string{"enabled", "disabled", "unknown"} {
				for _, entry := range []uint16{4, 9} {
					for _, attrs := range []byte{1, 3, 9} {
						counts["states"]++
						raw := option(1)
						raw[0] = attrs
						s := Snapshot{UEFI: true, Layout: layout, MediaID: media, SecureBoot: secure, Partitions: []string{route, other}, Entries: map[uint16][]byte{entry: raw}}
						p := makePlanForHost(s, "linux")
						if !p.Direct || p.Entry != entry || len(p.Fingerprint) != 64 || len(p.checks) != 3 {
							t.Fatalf("positive exact route failed: %+v", p)
						}
						counts["positive_plans"]++
						for _, check := range p.checks {
							if check.State != "pass" {
								t.Fatalf("ready plan has non-pass: %+v", check)
							}
						}
						key := fmt.Sprintf("%s/%s/%s/%d/%d", layout, media, secure, entry, attrs)
						if previous, ok := fingerprints[p.Fingerprint]; ok {
							t.Fatalf("changed authority did not change fingerprint: %s == %s", previous, key)
						}
						fingerprints[p.Fingerprint] = key
						s.Partitions = []string{other, route}
						if got := makePlanForHost(s, "linux"); got.Fingerprint != p.Fingerprint {
							t.Fatal("partition order changed authority")
						}
						counts["order_controls"]++
						s.Entries[entry+20] = option(3)
						if got := makePlanForHost(s, "linux"); got.Fingerprint != p.Fingerprint {
							t.Fatal("unrelated entry changed chosen authority")
						}
						counts["unrelated_entry_controls"]++
						for _, change := range []string{"windows", "missing-uefi", "missing-media", "missing-partition", "pending", "duplicate", "malformed", "permission", "timeout", "cancelled"} {
							copy := s
							copy.Entries = map[uint16][]byte{entry: append([]byte(nil), raw...)}
							host := "linux"
							switch change {
							case "windows":
								host = "windows"
							case "missing-uefi":
								copy.UEFI = false
							case "missing-media":
								copy.MediaID = ""
							case "missing-partition":
								copy.Partitions = []string{other}
							case "pending":
								copy.Pending = true
							case "duplicate":
								copy.Entries[entry+1] = append([]byte(nil), raw...)
							case "malformed":
								copy.Entries[entry] = raw[:len(raw)-1]
							case "permission":
								copy.Problem = "firmware"
							case "timeout":
								copy.Problem = "timeout"
							case "cancelled":
								copy.Problem = "cancelled"
							}
							refused := makePlanForHost(copy, host)
							if refused.Direct || refused.Fingerprint != "" || refused.Problem == "" {
								t.Fatalf("incomplete authority %s accepted: %+v", change, refused)
							}
							counts["refusals"]++
							if restored := makePlanForHost(s, "linux"); restored.Fingerprint != p.Fingerprint {
								t.Fatal("refusal contaminated valid retry")
							}
							counts["restored_controls"]++
						}
					}
				}
			}
		}
	}
	counts["sensitive_field_changes"] = len(fingerprints) - 1
	sources := map[string]string{}
	for _, name := range []string{"desktop/boot.go", "desktop/readiness.go", "desktop/boot_test.go"} {
		data, err := os.ReadFile(filepath.Join("..", name))
		if err != nil {
			t.Fatal(err)
		}
		h := sha256.Sum256(data)
		sources[name] = hex.EncodeToString(h[:])
	}
	encoded, err := json.MarshalIndent(map[string]any{"counts": counts, "source_sha256": sources, "scope": "Actual plan/readiness functions; fake EFI entries and snapshots only; supporting model, not extra canonical coverage"}, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile("/workspace/beamo-tools/audit-pass11-20261021/boot/plan-freshness-matrix.json", append(encoded, '\n'), 0600); err != nil {
		t.Fatal(err)
	}
	t.Logf("counts: %+v", counts)
}
