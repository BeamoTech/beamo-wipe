package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http/httptest"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func epochSnapshotPass12(ready bool) Snapshot {
	if !ready {
		return Snapshot{Problem: "media"}
	}
	return Snapshot{Layout: "epoch-layout", UEFI: true, MediaID: "epoch-usb", Partitions: []string{"gpt:00000001-0000-0000-0000-000000000000:1:2048:4096"}, Entries: map[uint16][]byte{4: option(1)}}
}
func epochRequestPass12(a *app, ctx context.Context, path, body string) *httptest.ResponseRecorder {
	r := httptest.NewRequest("POST", "http://"+a.host+path, strings.NewReader(body)).WithContext(ctx)
	r.Header.Set("Origin", "http://"+a.host)
	r.Header.Set("X-Beamo-Token", a.token)
	r.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	a.serve(w, r)
	return w
}
func epochAwaitPass12(t *testing.T, ch <-chan struct{}) {
	t.Helper()
	select {
	case <-ch:
	case <-time.After(3 * time.Second):
		t.Fatal("owned fake worker did not settle")
	}
}
func TestPass12RequestEpochModel(t *testing.T) {
	metrics := map[string]int{"states": 0, "cancelled_publications": 0, "fresh_publications": 0, "stale_restart_refusals": 0, "normal_restart_controls": 0, "closed_session_refusals": 0, "native_callbacks": 0}
	for _, oldReady := range []bool{false, true} {
		for _, newReady := range []bool{false, true} {
			for _, releaseEarly := range []bool{false, true} {
				for _, preview := range []bool{false, true} {
					name := fmt.Sprintf("old=%t/new=%t/early=%t/preview=%t", oldReady, newReady, releaseEarly, preview)
					t.Run(name, func(t *testing.T) {
						metrics["states"]++
						a := testApp()
						a.preview = preview
						a.revision = 7
						a.current = planView(a.p, preview)
						a.current.Revision = 7
						entered, release, workerDone := make(chan struct{}), make(chan struct{}), make(chan struct{})
						var releaseOnce sync.Once
						releaseOld := func() { releaseOnce.Do(func() { close(release) }) }
						defer releaseOld()
						var calls, restarts atomic.Int32
						a.probe = func(context.Context) Snapshot {
							if calls.Add(1) == 1 {
								close(entered)
								<-release
								defer close(workerDone)
								return epochSnapshotPass12(oldReady)
							}
							return epochSnapshotPass12(newReady)
						}
						a.restart = func(context.Context, string) error { restarts.Add(1); return nil }
						ctx, cancel := context.WithCancel(context.Background())
						firstDone := make(chan struct{})
						var first *httptest.ResponseRecorder
						go func() { defer close(firstDone); first = epochRequestPass12(a, ctx, "/api/check", `{}`) }()
						epochAwaitPass12(t, entered)
						cancel()
						epochAwaitPass12(t, firstDone)
						if first.Code != 200 || a.p.Direct || a.p.Problem != "cancelled" || a.revision != 8 || a.current.Ready {
							t.Fatalf("cancelled epoch published authority: code=%d plan=%+v revision=%d", first.Code, a.p, a.revision)
						}
						metrics["cancelled_publications"]++
						if releaseEarly {
							releaseOld()
							epochAwaitPass12(t, workerDone)
						}
						nextDone := make(chan struct{})
						var second *httptest.ResponseRecorder
						go func() {
							defer close(nextDone)
							second = epochRequestPass12(a, context.Background(), "/api/check", `{}`)
						}()
						if !releaseEarly {
							deadline := time.NewTimer(3 * time.Second)
							tick := time.NewTicker(time.Millisecond)
							observed := false
							for !observed {
								a.mu.Lock()
								observed = a.busy
								a.mu.Unlock()
								if !observed {
									select {
									case <-tick.C:
									case <-deadline.C:
										t.Fatal("fresh handler did not enter worker epoch")
									}
								}
							}
							tick.Stop()
							deadline.Stop()
						}
						releaseOld()
						epochAwaitPass12(t, workerDone)
						epochAwaitPass12(t, nextDone)
						if second.Code != 200 || a.p.Direct != newReady || a.current.Ready != newReady || a.revision != 9 || calls.Load() != 2 {
							t.Fatalf("old worker contaminated fresh epoch: code=%d ready=%t want=%t revision=%d calls=%d", second.Code, a.p.Direct, newReady, a.revision, calls.Load())
						}
						metrics["fresh_publications"]++
						stale := epochRequestPass12(a, context.Background(), "/api/restart", `{"confirm":true,"revision":8}`)
						if stale.Code != 409 || restarts.Load() != 0 {
							t.Fatalf("stale revision admitted: code=%d calls=%d", stale.Code, restarts.Load())
						}
						metrics["stale_restart_refusals"]++
						current := epochRequestPass12(a, context.Background(), "/api/restart", `{"confirm":true,"revision":9}`)
						wantCode, wantCalls := 409, int32(0)
						if newReady {
							wantCode = 200
							if !preview {
								wantCalls = 1
							}
						}
						if current.Code != wantCode || restarts.Load() != wantCalls {
							t.Fatalf("current control: code=%d want=%d calls=%d want=%d", current.Code, wantCode, restarts.Load(), wantCalls)
						}
						metrics["normal_restart_controls"]++
						if w := epochRequestPass12(a, context.Background(), "/api/close", `{}`); w.Code != 200 {
							t.Fatal("normal close refused")
						}
						for _, path := range []string{"state", "check", "restart", "close"} {
							if w := epochRequestPass12(a, context.Background(), "/api/"+path, `{"confirm":true,"revision":9}`); w.Code != 403 {
								t.Fatalf("closed session accepted %s: %d", path, w.Code)
							}
							metrics["closed_session_refusals"]++
						}
					})
				}
			}
		}
	}
	data, err := json.MarshalIndent(metrics, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile("/workspace/beamo-tools/audit-pass12-20261021/boot/request-epoch-metrics.json", append(data, '\n'), 0600); err != nil {
		t.Fatal(err)
	}
}
