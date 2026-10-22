// External PASS10 model: fake HTTP/probe/restart callbacks, no native actions.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"runtime"
	"testing"
	"time"
)

func TestPass10RetirementIdleMatrix(t *testing.T) {
	counts := map[string]int{"cases": 0, "new_idle_retirements": 0, "preclosed_idempotence": 0,
		"repeated_retirements": 0, "post_retirement_refusals": 0, "busy_preservations": 0,
		"age_refusals": 0, "normal_checks": 0, "normal_restarts": 0, "preview_restarts": 0,
		"normal_closes": 0, "manual_restart_refusals": 0, "state_reads": 0,
		"native_callbacks": 0, "mismatches": 0}
	ages := []time.Duration{-time.Minute, 0, 299 * time.Second, 5 * time.Minute, 5*time.Minute + 1, 6 * time.Minute}
	for _, variant := range []string{"ready", "manual", "preview"} {
		for _, busy := range []bool{false, true} {
			for _, age := range ages {
				for _, preclosed := range []bool{false, true} {
					if preclosed && busy {
						continue // A successfully retired session cannot own a new active action.
					}
					for _, action := range []string{"state", "check", "restart", "close"} {
						counts["cases"]++
						a, probes, restarts := closeFixturePass10(variant)
						now := time.Unix(100000, 0)
						if preclosed {
							if got := request(a, "/api/close", `{}`); got.Code != 200 {
								t.Fatal("positive prior close failed")
							}
						}
						a.lastSeen = now.Add(-age)
						a.busy = busy
						before, beforePlan, beforeReady := a.revision, a.p, a.current.Ready
						retired := a.retireIfIdle(now)
						want := preclosed || (!busy && age > 5*time.Minute)
						if retired != want {
							t.Fatalf("age=%s busy=%v preclosed=%v retirement=%v", age, busy, preclosed, retired)
						}
						if retired {
							expectedRevision := before + 1
							if preclosed {
								expectedRevision = before
								counts["preclosed_idempotence"]++
							} else {
								counts["new_idle_retirements"]++
							}
							if !a.closed || a.p.Direct || a.current.Ready || a.revision != expectedRevision || a.current.Revision != a.revision {
								t.Fatal("retirement did not consume published authority")
							}
							if !a.retireIfIdle(now.Add(10*time.Hour)) || a.revision != expectedRevision {
								t.Fatal("repeated retirement changed terminal authority")
							}
							counts["repeated_retirements"]++
							got := request(a, "/api/"+action, `{"confirm":true,"revision":7}`)
							if got.Code < 400 || probes.Load() != 0 || restarts.Load() != 0 {
								t.Fatal("post-retirement action reached fake callback")
							}
							counts["post_retirement_refusals"]++
							continue
						}
						if a.closed || a.revision != before || a.p.Direct != beforePlan.Direct || a.p.Fingerprint != beforePlan.Fingerprint || a.p.Problem != beforePlan.Problem || a.current.Ready != beforeReady {
							t.Fatal("non-idle or busy session was retired")
						}
						got := request(a, "/api/"+action, `{"confirm":true,"revision":7}`)
						if busy {
							counts["busy_preservations"]++
							code := 409
							if action == "state" {
								code = 200
							}
							if got.Code != code || a.closed || probes.Load() != 0 || restarts.Load() != 0 {
								t.Fatal("busy action ownership changed")
							}
							continue
						}
						counts["age_refusals"]++
						switch action {
						case "state":
							if got.Code != 200 || probes.Load() != 0 || restarts.Load() != 0 {
								t.Fatal("positive state read failed")
							}
							counts["state_reads"]++
						case "close":
							if got.Code != 200 || !a.closed || a.p.Direct || a.current.Ready || probes.Load() != 0 || restarts.Load() != 0 {
								t.Fatal("positive close failed")
							}
							counts["normal_closes"]++
						case "check":
							if got.Code != 200 || probes.Load() != 1 || restarts.Load() != 0 {
								t.Fatal("positive fake check failed")
							}
							if runtime.GOOS == "windows" {
								assertWindowsManualRestart(t, a)
							} else if !a.current.Ready {
								t.Fatal("positive fake readiness lost")
							}
							counts["normal_checks"]++
						case "restart":
							if variant == "manual" {
								if got.Code != 409 || restarts.Load() != 0 {
									t.Fatal("manual policy restarted")
								}
								counts["manual_restart_refusals"]++
							} else if variant == "preview" {
								if got.Code != 200 || restarts.Load() != 0 {
									t.Fatal("preview restarted")
								}
								counts["preview_restarts"]++
							} else {
								if got.Code != 200 || restarts.Load() != 1 {
									t.Fatal("positive fake restart failed")
								}
								counts["normal_restarts"]++
							}
						}
					}
				}
			}
		}
	}
	if counts["cases"] != 216 || counts["post_retirement_refusals"] != 96 || counts["busy_preservations"] != 72 || counts["normal_checks"] != 12 || counts["normal_restarts"] != 4 {
		t.Fatalf("model coverage changed: %+v", counts)
	}
	sources := map[string]string{}
	for _, name := range []string{"desktop/main.go", "desktop/close_admission_pass10_20261021_test.go"} {
		data, err := os.ReadFile("/workspace/beamo-wipe/" + name)
		if err != nil {
			t.Fatal(err)
		}
		digest := sha256.Sum256(data)
		sources[name] = hex.EncodeToString(digest[:])
	}
	data, err := json.MarshalIndent(map[string]any{"counts": counts, "source_sha256": sources, "scope": "Pure fake API and clock retirement law; no native qualification"}, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile("/workspace/beamo-tools/audit-pass10-20261021/root/retirement-idle-matrix.json", append(data, '\n'), 0600); err != nil {
		t.Fatal(err)
	}
}
