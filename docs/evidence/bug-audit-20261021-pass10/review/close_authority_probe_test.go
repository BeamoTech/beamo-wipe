// Independent PASS10 proof: handler admission only; no platform callbacks.
package main

import (
    "context"
    "testing"
)

func TestPass10RootCloseAuthority(t *testing.T) {
    for _, scenario := range []string{"restart-after-close", "check-after-close", "normal-restart", "busy-close"} {
        t.Run(scenario, func(t *testing.T) {
            a := testApp()
            a.revision = 29
            calls := 0
            a.restart = func(context.Context, string) error { calls++; return nil }
            a.probe = func(context.Context) Snapshot { calls++; return Snapshot{Problem: "fake-unavailable"} }
            if scenario == "normal-restart" {
                if response := request(a, "/api/restart", `{"confirm":true,"revision":29}`); response.Code != 200 || calls != 1 {
                    t.Fatalf("positive restart control: status=%d calls=%d", response.Code, calls)
                }
                return
            }
            if scenario == "busy-close" {
                a.busy = true
                if response := request(a, "/api/close", `{}`); response.Code != 409 { t.Fatalf("active action close status=%d", response.Code) }
                select { case <-a.close: t.Fatal("active action retired"); default: }
                return
            }
            if response := request(a, "/api/close", `{}`); response.Code != 200 { t.Fatalf("close status=%d", response.Code) }
            route := "/api/check"
            if scenario == "restart-after-close" { route = "/api/restart" }
            response := request(a, route, `{"confirm":true,"revision":29}`)
            if response.Code < 400 || calls != 0 {
                t.Fatalf("closed launcher admitted %s: status=%d fake callbacks=%d", route, response.Code, calls)
            }
        })
    }
}
