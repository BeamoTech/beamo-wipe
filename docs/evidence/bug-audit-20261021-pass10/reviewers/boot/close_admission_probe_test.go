// External PASS10 proof. Pure httptest callbacks; no platform/native actions.
package main

import (
	"context"
	"encoding/json"
	"io"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestPass10CloseAdmissionProbe(t *testing.T) {
	for _, scenario := range []string{"normal-restart", "normal-check", "busy-close", "closed-restart", "closed-check", "closed-state"} {
		t.Run(scenario, func(t *testing.T) {
			a := testApp()
			a.revision = 7
			a.current = planView(a.p, false)
			a.current.Revision = 7
			probes, restarts := 0, 0
			a.probe = func(context.Context) Snapshot {
				probes++
				return Snapshot{Layout: "fake-layout", UEFI: true, MediaID: "fake-usb",
					Partitions: []string{"gpt:00000001-0000-0000-0000-000000000000:1:2048:4096"},
					Entries:    map[uint16][]byte{4: option(1)}}
			}
			a.restart = func(context.Context, string) error { restarts++; return nil }
			if scenario == "normal-restart" {
				got := request(a, "/api/restart", `{"confirm":true,"revision":7}`)
				if got.Code != 200 || restarts != 1 {
					t.Fatalf("positive restart: code=%d calls=%d", got.Code, restarts)
				}
				return
			}
			if scenario == "normal-check" {
				got := request(a, "/api/check", `{}`)
				if got.Code != 200 || probes != 1 || !a.current.Ready {
					t.Fatalf("positive check: code=%d calls=%d ready=%v", got.Code, probes, a.current.Ready)
				}
				return
			}
			if scenario == "busy-close" {
				a.busy = true
				if got := request(a, "/api/close", `{}`); got.Code != 409 {
					t.Fatalf("busy close=%d", got.Code)
				}
				select {
				case <-a.close:
					t.Fatal("busy action was abandoned")
				default:
				}
				return
			}
			if got := request(a, "/api/close", `{}`); got.Code != 200 {
				t.Fatalf("close=%d", got.Code)
			}
			select {
			case <-a.close:
			default:
				t.Fatal("normal close not published")
			}
			switch scenario {
			case "closed-restart":
				got := request(a, "/api/restart", `{"confirm":true,"revision":7}`)
				if got.Code < 400 || restarts != 0 {
					t.Fatalf("restart admitted after successful close: code=%d calls=%d", got.Code, restarts)
				}
			case "closed-check":
				got := request(a, "/api/check", `{}`)
				if got.Code < 400 || probes != 0 {
					t.Fatalf("check admitted after successful close: code=%d calls=%d", got.Code, probes)
				}
			case "closed-state":
				got := request(a, "/api/state", `{}`)
				if got.Code >= 400 {
					return
				}
				var v view
				if err := json.Unmarshal(got.Body.Bytes(), &v); err != nil {
					t.Fatal(err)
				}
				if v.Ready {
					t.Fatal("successful close retained published restart authority")
				}
			}
		})
	}
}

type pass10DelayedEOF struct {
	data    string
	entered chan struct{}
	release chan struct{}
}

func (r *pass10DelayedEOF) Read(p []byte) (int, error) {
	if r.data != "" {
		n := copy(p, r.data)
		r.data = r.data[n:]
		return n, nil
	}
	select {
	case <-r.entered:
	default:
		close(r.entered)
	}
	<-r.release
	return 0, io.EOF
}

func TestPass10CloseInflightAdmissionProbe(t *testing.T) {
	for _, closed := range []bool{false, true} {
		name := "normal-inflight"
		if closed {
			name = "closed-inflight"
		}
		t.Run(name, func(t *testing.T) {
			a := testApp()
			a.revision = 7
			restarts := 0
			a.restart = func(context.Context, string) error { restarts++; return nil }
			body := &pass10DelayedEOF{data: `{"confirm":true,"revision":7}`, entered: make(chan struct{}), release: make(chan struct{})}
			var once sync.Once
			release := func() { once.Do(func() { close(body.release) }) }
			defer release()
			r := httptest.NewRequest("POST", "http://"+a.host+"/api/restart", body)
			r.Header.Set("Origin", "http://"+a.host)
			r.Header.Set("X-Beamo-Token", strings.Repeat("a", 64))
			r.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()
			done := make(chan struct{})
			go func() { defer close(done); a.serve(w, r) }()
			select {
			case <-body.entered:
			case <-time.After(5 * time.Second):
				t.Fatal("fake request did not reach admission barrier")
			}
			if closed {
				if got := request(a, "/api/close", `{}`); got.Code != 200 {
					t.Fatalf("close=%d", got.Code)
				}
			}
			release()
			select {
			case <-done:
			case <-time.After(5 * time.Second):
				t.Fatal("owned fake handler did not settle")
			}
			if closed {
				if w.Code < 400 || restarts != 0 {
					t.Fatalf("inflight restart survived successful close: code=%d calls=%d", w.Code, restarts)
				}
			} else if w.Code != 200 || restarts != 1 {
				t.Fatalf("normal inflight control: code=%d calls=%d", w.Code, restarts)
			}
		})
	}
}
