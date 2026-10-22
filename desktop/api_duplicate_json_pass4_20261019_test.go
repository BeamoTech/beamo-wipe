// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"context"
	"strings"
	"testing"
)

func duplicateRequestApp() (*app, *int, *int) {
	a := testApp()
	a.revision = 7
	restarts, probes := 0, 0
	a.restart = func(context.Context, string) error { restarts++; return nil }
	a.probe = func(context.Context) Snapshot { probes++; return Snapshot{Problem: "media"} }
	return a, &restarts, &probes
}

func TestDuplicateAPIFieldsCannotReplaceConsentOrReview(t *testing.T) {
	bodies := []string{
		`{"confirm":false,"confirm":true,"revision":7}`,
		`{"confirm":true,"revision":6,"revision":7}`,
		`{"confirm":true,"revision":7,"revision":7}`,
		`{"confirm":false,"Confirm":true,"revision":7}`,
		`{"Confirm":true,"confirm":false,"revision":7}`,
		`{"confirm":true,"revision":6,"REVISION":7}`,
		`{"\u0063onfirm":false,"confirm":true,"revision":7}`,
		`{"confirm":true,"revision":6,"revi\u0073ion":7}`,
		`{"confirm":true,"revision":6,"reviſion":7}`,
	}
	for _, action := range []string{"restart", "check", "close", "state"} {
		for _, body := range bodies {
			t.Run(action+body, func(t *testing.T) {
				a, restarts, probes := duplicateRequestApp()
				response := request(a, "/api/"+action, body)
				if response.Code != 400 || *restarts != 0 || *probes != 0 || !a.p.Direct || a.revision != 7 || a.busy {
					t.Fatalf("duplicate changed state: status=%d restarts=%d probes=%d revision=%d", response.Code, *restarts, *probes, a.revision)
				}
				select {
				case <-a.close:
					t.Fatal("duplicate request closed the launcher")
				default:
				}
			})
		}
	}
}

func TestUniqueAPIFieldAliasesPreserveConfirmedRestart(t *testing.T) {
	for _, body := range []string{
		`{"confirm":true,"revision":7}`,
		`{"Confirm":true,"Revision":7}`,
		`{"CONFIRM":true,"REVISION":7}`,
		`{"\u0063onfirm":true,"\u0072evision":7}`,
		`{"confirm":true,"reviſion":7}`,
	} {
		t.Run(body, func(t *testing.T) {
			a, restarts, probes := duplicateRequestApp()
			response := request(a, "/api/restart", body)
			if response.Code != 200 || *restarts != 1 || *probes != 0 {
				t.Fatalf("unique confirmation rejected: status=%d restarts=%d probes=%d", response.Code, *restarts, *probes)
			}
			if request(a, "/api/restart", body).Code != 409 || *restarts != 1 {
				t.Fatal("confirmed plan was reused")
			}
		})
	}
}

func TestAPIRequestOmissionsAndNegativeConsentRemainSafe(t *testing.T) {
	for _, action := range []string{"state", "check"} {
		for _, body := range []string{`{}`, `{"confirm":false}`, `{"revision":7}`, `{"confirm":null,"revision":null}`} {
			t.Run(action+body, func(t *testing.T) {
				a, restarts, probes := duplicateRequestApp()
				wantProbes := 0
				if action == "check" {
					wantProbes = 1
				}
				if response := request(a, "/api/"+action, body); response.Code != 200 || *restarts != 0 || *probes != wantProbes {
					t.Fatalf("harmless omission rejected: status=%d restarts=%d probes=%d", response.Code, *restarts, *probes)
				}
			})
		}
	}
	for _, body := range []string{`{}`, `{"confirm":false,"revision":7}`, `{"confirm":true,"revision":6}`, `{"revision":7}`, `{"confirm":null,"revision":7}`} {
		a, restarts, _ := duplicateRequestApp()
		if response := request(a, "/api/restart", body); response.Code != 409 || *restarts != 0 {
			t.Fatalf("missing/stale consent accepted: %q status=%d restarts=%d", body, response.Code, *restarts)
		}
	}
}

func TestMalformedAPIObjectsCannotInvokeActions(t *testing.T) {
	bodies := []string{
		``, `null`, `[]`, `[{}]`, `true`, `7`, `"request"`, `{`, `{"confirm":`,
		`{"confirm":true`, `{"confirm":true,}`, `{"confirm":"true"}`,
		`{"revision":1.5}`, `{"revision":-1}`, `{"revision":"7"}`,
		`{"revision":18446744073709551616}`, `{"unknown":true}`, `{"confirm":{}}`,
		`{"revision":[]}`, `{} {}`, `{} null`, strings.Repeat(" ", 257) + `{}`,
	}
	for _, action := range []string{"state", "check", "restart", "close"} {
		for _, body := range bodies {
			t.Run(action+body, func(t *testing.T) {
				a, restarts, probes := duplicateRequestApp()
				if response := request(a, "/api/"+action, body); response.Code != 400 || *restarts != 0 || *probes != 0 || a.revision != 7 || !a.p.Direct {
					t.Fatalf("malformed request changed state: status=%d restarts=%d probes=%d", response.Code, *restarts, *probes)
				}
			})
		}
	}
}
