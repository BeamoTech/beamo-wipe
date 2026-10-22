// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"context"
	"io"
	"net/http/httptest"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func closeFixturePass10(variant string) (*app, *atomic.Int32, *atomic.Int32) {
	a := testApp()
	a.revision = 7
	if variant == "manual" {
		a.p = Plan{Problem: "windows-manual"}
	}
	a.preview = variant == "preview"
	a.current = planView(a.p, a.preview)
	a.current.Revision = a.revision
	probes, restarts := new(atomic.Int32), new(atomic.Int32)
	a.probe = func(context.Context) Snapshot {
		probes.Add(1)
		return Snapshot{Layout: "fake-layout", UEFI: true, MediaID: "fake-usb",
			Partitions: []string{"gpt:00000001-0000-0000-0000-000000000000:1:2048:4096"},
			Entries:    map[uint16][]byte{4: option(1)}}
	}
	a.restart = func(context.Context, string) error { restarts.Add(1); return nil }
	return a, probes, restarts
}

func TestCloseRetiresEveryAPIActionPass10(t *testing.T) {
	for _, variant := range []string{"ready", "manual", "preview"} {
		for _, action := range []string{"restart", "check", "state", "close"} {
			t.Run(variant+"/"+action, func(t *testing.T) {
				a, probes, restarts := closeFixturePass10(variant)
				if got := request(a, "/api/close", `{}`); got.Code != 200 {
					t.Fatalf("normal close = %d", got.Code)
				}
				if a.p.Direct || a.current.Ready || a.revision <= 7 || a.current.Revision != a.revision {
					t.Fatal("successful close retained or failed to revise published authority")
				}
				select {
				case <-a.close:
				default:
					t.Fatal("successful close was not published")
				}
				got := request(a, "/api/"+action, `{"confirm":true,"revision":7}`)
				if got.Code < 400 || probes.Load() != 0 || restarts.Load() != 0 {
					t.Fatalf("closed session admitted %s: status=%d probes=%d restarts=%d", action, got.Code, probes.Load(), restarts.Load())
				}
			})
		}
	}
}

type closeReaderPass10 struct {
	data    string
	entered chan struct{}
	release chan struct{}
}

func (r *closeReaderPass10) Read(p []byte) (int, error) {
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

func TestCloseRejectsAlreadyDecodingActionsPass10(t *testing.T) {
	for _, action := range []string{"restart", "check", "state"} {
		t.Run(action, func(t *testing.T) {
			a, probes, restarts := closeFixturePass10("ready")
			body := &closeReaderPass10{data: `{"confirm":true,"revision":7}`, entered: make(chan struct{}), release: make(chan struct{})}
			var once sync.Once
			release := func() { once.Do(func() { close(body.release) }) }
			defer release()
			r := httptest.NewRequest("POST", "http://"+a.host+"/api/"+action, body)
			r.Header.Set("Origin", "http://"+a.host)
			r.Header.Set("X-Beamo-Token", a.token)
			r.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()
			done := make(chan struct{})
			go func() { defer close(done); a.serve(w, r) }()
			select {
			case <-body.entered:
			case <-time.After(5 * time.Second):
				t.Fatal("fake body did not reach admission barrier")
			}
			if got := request(a, "/api/close", `{}`); got.Code != 200 {
				t.Fatalf("normal close = %d", got.Code)
			}
			release()
			select {
			case <-done:
			case <-time.After(5 * time.Second):
				t.Fatal("owned fake action did not settle")
			}
			if w.Code < 400 || probes.Load() != 0 || restarts.Load() != 0 {
				t.Fatalf("decoding action survived close: status=%d probes=%d restarts=%d", w.Code, probes.Load(), restarts.Load())
			}
		})
	}
}

type closeResponsePass10 struct {
	*httptest.ResponseRecorder
	entered chan struct{}
	release chan struct{}
}

func (w *closeResponsePass10) Flush() {
	close(w.entered)
	<-w.release
}

func TestCloseRetiresBeforeResponseFlushPass10(t *testing.T) {
	for _, action := range []string{"restart", "check", "state"} {
		t.Run(action, func(t *testing.T) {
			a, probes, restarts := closeFixturePass10("ready")
			w := &closeResponsePass10{ResponseRecorder: httptest.NewRecorder(), entered: make(chan struct{}), release: make(chan struct{})}
			var once sync.Once
			release := func() { once.Do(func() { close(w.release) }) }
			defer release()
			r := httptest.NewRequest("POST", "http://"+a.host+"/api/close", strings.NewReader(`{}`))
			r.Header.Set("Origin", "http://"+a.host)
			r.Header.Set("X-Beamo-Token", a.token)
			r.Header.Set("Content-Type", "application/json")
			done := make(chan struct{})
			go func() { defer close(done); a.serve(w, r) }()
			select {
			case <-w.entered:
			case <-time.After(5 * time.Second):
				t.Fatal("fake close did not reach response barrier")
			}
			got := request(a, "/api/"+action, `{"confirm":true,"revision":7}`)
			release()
			select {
			case <-done:
			case <-time.After(5 * time.Second):
				t.Fatal("owned fake close did not settle")
			}
			if w.Code != 200 || got.Code < 400 || probes.Load() != 0 || restarts.Load() != 0 {
				t.Fatalf("close response retained action authority: close=%d action=%d probes=%d restarts=%d", w.Code, got.Code, probes.Load(), restarts.Load())
			}
		})
	}
}

func TestClosePreservesOpenAndBusyControlsPass10(t *testing.T) {
	for _, scenario := range []string{"restart", "check", "preview", "busy", "unauthorized", "malformed"} {
		t.Run(scenario, func(t *testing.T) {
			a, probes, restarts := closeFixturePass10("ready")
			switch scenario {
			case "restart":
				if got := request(a, "/api/restart", `{"confirm":true,"revision":7}`); got.Code != 200 || restarts.Load() != 1 {
					t.Fatal("normal confirmed restart was blocked")
				}
			case "check":
				if got := request(a, "/api/check", `{}`); got.Code != 200 || probes.Load() != 1 || !a.current.Ready {
					t.Fatal("normal check was blocked")
				}
			case "preview":
				a.preview = true
				if got := request(a, "/api/restart", `{"confirm":true,"revision":7}`); got.Code != 200 || restarts.Load() != 0 {
					t.Fatal("preview invoked restart or was blocked")
				}
			case "busy":
				a.busy = true
				if got := request(a, "/api/close", `{}`); got.Code != 409 || !a.p.Direct {
					t.Fatal("busy close abandoned an active action")
				}
			case "unauthorized":
				r := httptest.NewRequest("POST", "http://"+a.host+"/api/close", strings.NewReader(`{}`))
				r.Header.Set("Origin", "http://"+a.host)
				r.Header.Set("X-Beamo-Token", "wrong-token")
				r.Header.Set("Content-Type", "application/json")
				w := httptest.NewRecorder()
				a.serve(w, r)
				if w.Code != 403 || !a.p.Direct {
					t.Fatal("unauthorized close changed session authority")
				}
			case "malformed":
				if got := request(a, "/api/close", `{"confirm":true,"revision":7,"unknown":true}`); got.Code < 400 || !a.p.Direct {
					t.Fatal("invalid close changed session authority")
				}
			}
			select {
			case <-a.close:
				t.Fatal("open/busy control unexpectedly closed")
			default:
			}
		})
	}
}
