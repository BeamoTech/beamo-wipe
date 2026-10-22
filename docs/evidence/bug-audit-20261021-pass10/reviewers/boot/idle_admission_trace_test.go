// Historical baseline trace: exact ticker guard before the decision is acted on.
// Not a final-source model. Snapshot SHA binds the production statements replayed.
package main

import (
	"testing"
	"time"
)

func TestPass10IdleAdmissionBaselineTrace(t *testing.T) {
	for _, busy := range []bool{false, true} {
		name := "idle-decision"
		if busy { name = "busy-control" }
		t.Run(name, func(t *testing.T) {
			a, _, restarts := closeFixturePass10("ready")
			a.lastSeen = time.Now().Add(-6*time.Minute)
			a.busy = busy
			// Exact existing run() ticker statements. A handler can take the
			// unlocked mutex here before run() acts on cached idle=true.
			a.mu.Lock()
			idle := time.Since(a.lastSeen) > 5*time.Minute && !a.busy
			a.mu.Unlock()
			if busy {
				if idle { t.Fatal("busy action was declared idle") }
				return
			}
			if !idle { t.Fatal("positive old idle decision not reached") }
			got := request(a, "/api/restart", `{"confirm":true,"revision":7}`)
			if got.Code < 400 || restarts.Load() != 0 {
				t.Fatalf("cached idle decision can abandon admitted action: status=%d calls=%d", got.Code, restarts.Load())
			}
		})
	}
}
