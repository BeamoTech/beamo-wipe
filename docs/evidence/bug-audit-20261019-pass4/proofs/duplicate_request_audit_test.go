package main

import (
    "context"
    "testing"
)

func TestPass4DuplicateRestartJSONCannotReplaceConsent(t *testing.T) {
    for _, body := range []string{
        `{"confirm":false,"confirm":true,"revision":7}`,
        `{"confirm":true,"revision":6,"revision":7}`,
        `{"confirm":true,"revision":7,"revision":7}`,
    } {
        t.Run(body, func(t *testing.T) {
            a := testApp()
            a.revision = 7
            calls := 0
            a.restart = func(context.Context,string) error { calls++; return nil }
            response := request(a,"/api/restart",body)
            if response.Code < 400 || calls != 0 {
                t.Fatalf("ambiguous restart consumed consent: status=%d calls=%d",response.Code,calls)
            }
        })
    }
}

func TestPass4UniqueRestartJSONControls(t *testing.T) {
    for _, row := range []struct{body string; want int; calls int}{
        {`{"confirm":true,"revision":7}`,200,1},
        {`{"confirm":false,"revision":7}`,409,0},
        {`{"confirm":true,"revision":6}`,409,0},
    } {
        t.Run(row.body,func(t *testing.T){
            a:=testApp(); a.revision=7; calls:=0
            a.restart=func(context.Context,string)error{calls++;return nil}
            response:=request(a,"/api/restart",row.body)
            if response.Code!=row.want || calls!=row.calls {t.Fatalf("control status=%d calls=%d",response.Code,calls)}
        })
    }
}
