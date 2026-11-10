// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"context"
	"encoding/json"
	"errors"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"sync/atomic"
	"testing"
)

// THIS HOST MUST NEVER RESTART. Every test here uses a fake runner. The
// real runner (platformAdvancedStartup) is never called from a test; the
// tests below prove from the source that tests cannot reach it.

func advancedApp(runner func(context.Context) error) *app {
	a := testApp()
	a.p = Plan{Problem: "windows-manual", AdvancedStartup: true}
	a.revision = 7
	a.advancedStartup = runner
	return a
}

func TestAdvancedStartupGuardRefusesInsideTestBinaries(t *testing.T) {
	if !testing.Testing() {
		t.Fatal("testing.Testing() is false inside go test")
	}
	if err := advancedStartupGuard(); !errors.Is(err, errAdvancedStartupInTest) {
		t.Fatalf("guard = %v; the real runner would not refuse in tests", err)
	}
}

func TestAdvancedStartupCommandIsExact(t *testing.T) {
	got := advancedStartupArgs(`C:\Windows`)
	want := []string{filepath.Join(`C:\Windows`, "System32", "shutdown.exe"), "/r", "/o", "/t", "0"}
	if strings.Join(got, "\x00") != strings.Join(want, "\x00") {
		t.Fatalf("args = %q, want %q", got, want)
	}
	for _, arg := range got[1:] {
		switch strings.ToLower(arg) {
		case "/f", "/fw", "/s", "/p", "/h", "/hybrid", "/m", "/d", "/c", "-f":
			t.Fatalf("forbidden shutdown switch %q", arg)
		}
	}
}

func TestAdvancedStartupNeedsConfirmationCurrentReviewAndOffer(t *testing.T) {
	var calls atomic.Int32
	fake := func(context.Context) error { calls.Add(1); return nil }
	for name, tc := range map[string]struct {
		a    func() *app
		body string
	}{
		"no confirm":     {func() *app { return advancedApp(fake) }, `{"confirm":false,"revision":7}`},
		"stale revision": {func() *app { return advancedApp(fake) }, `{"confirm":true,"revision":6}`},
		"not offered": {func() *app {
			a := advancedApp(fake)
			a.p.AdvancedStartup = false
			return a
		}, `{"confirm":true,"revision":7}`},
		"linux direct plan": {func() *app {
			a := advancedApp(fake)
			a.p = Plan{Direct: true, Fingerprint: strings.Repeat("b", 64)}
			return a
		}, `{"confirm":true,"revision":7}`},
	} {
		if w := request(tc.a(), "/api/advanced-startup", tc.body); w.Code != 409 {
			t.Errorf("%s: code %d", name, w.Code)
		}
	}
	if calls.Load() != 0 {
		t.Fatalf("runner called %d times without a valid request", calls.Load())
	}
}

func TestAdvancedStartupRunsFakeOnceAndExplainsNextScreens(t *testing.T) {
	var calls atomic.Int32
	a := advancedApp(func(ctx context.Context) error {
		if _, ok := ctx.Deadline(); !ok {
			t.Error("runner has no deadline")
		}
		calls.Add(1)
		return nil
	})
	w := request(a, "/api/advanced-startup", `{"confirm":true,"revision":7}`)
	if w.Code != 200 {
		t.Fatalf("code %d %s", w.Code, w.Body)
	}
	var out map[string]string
	if err := json.Unmarshal(w.Body.Bytes(), &out); err != nil {
		t.Fatal(err)
	}
	for _, want := range []string{"Use a device", "EFI USB Device", "Beamo USB"} {
		if !strings.Contains(out["message"], want) {
			t.Errorf("message lacks %q: %q", want, out["message"])
		}
	}
	// Single use: the reviewed plan is gone and the published view says so.
	if w := request(a, "/api/advanced-startup", `{"confirm":true,"revision":8}`); w.Code != 409 || calls.Load() != 1 {
		t.Fatalf("plan reused: code %d calls %d", w.Code, calls.Load())
	}
	if a.current.AdvancedStartup || a.busy {
		t.Fatalf("view still offers the restart: %+v busy=%v", a.current.AdvancedStartup, a.busy)
	}
}

func TestAdvancedStartupFailureFallsBackToBootMenuKey(t *testing.T) {
	for name, runner := range map[string]func(context.Context) error{
		"command failed": func(context.Context) error { return errors.New("exit status 5") },
		"no runner":      nil,
	} {
		a := advancedApp(runner)
		w := request(a, "/api/advanced-startup", `{"confirm":true,"revision":7}`)
		if w.Code != 503 {
			t.Fatalf("%s: code %d", name, w.Code)
		}
		body := w.Body.String()
		for _, want := range []string{"did not restart", "Nothing was changed", "nothing was erased", "boot-menu key", "Use a device"} {
			if !strings.Contains(body, want) {
				t.Errorf("%s: fallback lacks %q: %q", name, want, body)
			}
		}
		if a.busy {
			t.Fatalf("%s: left busy", name)
		}
	}
}

func TestAdvancedStartupPreviewNeverCallsRunner(t *testing.T) {
	a := advancedApp(func(context.Context) error { t.Fatal("preview reached a runner"); return nil })
	a.preview = true
	w := request(a, "/api/advanced-startup", `{"confirm":true,"revision":7}`)
	if w.Code != 200 || !strings.Contains(w.Body.String(), "No restart was requested") {
		t.Fatalf("preview = %d %s", w.Code, w.Body)
	}
}

func TestAdvancedStartupOfferedOnlyForIdentifiedUSBOnWindows(t *testing.T) {
	good := Snapshot{UEFI: true, MediaID: "usb:1", Partitions: []string{"gpt:x:1:2048:4096"}, AdvancedStartup: true}
	if p := makePlanForHost(good, "windows"); !p.AdvancedStartup || p.Direct || p.Problem != "windows-manual" {
		t.Fatalf("windows plan = %+v", p)
	}
	v := planView(makePlanForHost(good, "windows"), false)
	if !v.AdvancedStartup || v.Ready || !strings.Contains(v.Checks[2].Next, "Restart to boot options") {
		t.Fatalf("windows view = %+v", v)
	}
	old := good
	old.AdvancedStartup = false // Windows before build 10240
	if p := makePlanForHost(old, "windows"); p.AdvancedStartup {
		t.Fatal("offered on older Windows")
	}
	if v := planView(makePlanForHost(old, "windows"), false); v.AdvancedStartup || strings.Contains(v.Checks[2].Next, "boot options") {
		t.Fatalf("older Windows view = %+v", v)
	}
	for _, problem := range []string{"media", "legacy", "platform", "unattended", "timeout", "cancelled", "runtime"} {
		s := good
		s.Problem = problem
		if p := makePlanForHost(s, "windows"); p.AdvancedStartup {
			t.Errorf("offered with problem %q", problem)
		}
	}
	if p := makePlanForHost(good, "linux"); p.AdvancedStartup {
		t.Fatal("offered on Linux")
	}
	if p := makePlanForHost(good, "darwin"); p.AdvancedStartup {
		t.Fatal("offered on macOS")
	}
}

// parsePackage returns this package's production and test files.
func parsePackage(t *testing.T) (fset *token.FileSet, prod, tests map[string]*ast.File) {
	t.Helper()
	fset = token.NewFileSet()
	prod, tests = map[string]*ast.File{}, map[string]*ast.File{}
	names, err := filepath.Glob("*.go")
	if err != nil || len(names) == 0 {
		t.Fatalf("glob: %v", err)
	}
	for _, name := range names {
		f, err := parser.ParseFile(fset, name, nil, parser.SkipObjectResolution)
		if err != nil {
			t.Fatal(err)
		}
		if strings.HasSuffix(name, "_test.go") {
			tests[name] = f
		} else {
			prod[name] = f
		}
	}
	return fset, prod, tests
}

// enclosingFunc names the top-level function that contains pos.
func enclosingFunc(f *ast.File, pos token.Pos) string {
	for _, d := range f.Decls {
		if fn, ok := d.(*ast.FuncDecl); ok && fn.Pos() <= pos && pos < fn.End() {
			return fn.Name.Name
		}
	}
	return ""
}

// Static proof that a test binary cannot restart this computer.
func TestRealAdvancedStartupRunnerIsUnreachableFromTests(t *testing.T) {
	fset, prod, tests := parsePackage(t)

	// 1. Tests never name the real runner or run() (which wires it).
	for name, f := range tests {
		ast.Inspect(f, func(n ast.Node) bool {
			switch x := n.(type) {
			case *ast.Ident:
				if x.Name == "platformAdvancedStartup" {
					t.Errorf("%s names the real runner", fset.Position(x.Pos()))
				}
			case *ast.CallExpr:
				if id, ok := x.Fun.(*ast.Ident); ok && (id.Name == "run" || id.Name == "main") {
					t.Errorf("%s calls %s()", fset.Position(x.Pos()), id.Name)
				}
			}
			return true
		})
		_ = name
	}

	// 2. In production code the real runner is referenced only by its own
	// definitions and by run().
	refs := 0
	for _, f := range prod {
		ast.Inspect(f, func(n ast.Node) bool {
			id, ok := n.(*ast.Ident)
			if !ok || id.Name != "platformAdvancedStartup" {
				return true
			}
			if fn := enclosingFunc(f, id.Pos()); fn == "run" {
				refs++
			} else if fn != "platformAdvancedStartup" {
				// The declaration's own name sits outside the body.
				for _, d := range f.Decls {
					if decl, ok := d.(*ast.FuncDecl); ok && decl.Name == id {
						return true
					}
				}
				t.Errorf("%s: real runner referenced from %q", fset.Position(id.Pos()), fn)
			}
			return true
		})
	}
	if refs != 1 {
		t.Errorf("run() references the real runner %d times, want 1", refs)
	}

	// 3. Every real runner starts with the test-binary guard, and only the
	// Windows one builds a command, from advancedStartupArgs only.
	found := 0
	for name, f := range prod {
		for _, d := range f.Decls {
			fn, ok := d.(*ast.FuncDecl)
			if !ok || fn.Name.Name != "platformAdvancedStartup" {
				continue
			}
			found++
			src, _ := os.ReadFile(name)
			body := string(src[fset.Position(fn.Body.Pos()).Offset:fset.Position(fn.Body.End()).Offset])
			if strings.Contains(body, "exec.") {
				first, ok := fn.Body.List[0].(*ast.IfStmt)
				if !ok {
					t.Fatalf("%s: first statement is not the guard", name)
				}
				init, ok := first.Init.(*ast.AssignStmt)
				if !ok || len(init.Rhs) != 1 {
					t.Fatalf("%s: first statement is not the guard", name)
				}
				call, ok := init.Rhs[0].(*ast.CallExpr)
				if id, isID := call.Fun.(*ast.Ident); !ok || !isID || id.Name != "advancedStartupGuard" {
					t.Fatalf("%s: first statement is not advancedStartupGuard()", name)
				}
				if !strings.Contains(body, "advancedStartupArgs(") {
					t.Fatalf("%s: command not built by advancedStartupArgs", name)
				}
			}
		}
	}
	if found != 3 {
		t.Fatalf("found %d platformAdvancedStartup definitions, want 3 (windows, linux, other)", found)
	}

	// 4. "shutdown.exe" appears only in advancedStartupArgs.
	for _, f := range prod {
		ast.Inspect(f, func(n ast.Node) bool {
			lit, ok := n.(*ast.BasicLit)
			if !ok || lit.Kind != token.STRING {
				return true
			}
			v, err := strconv.Unquote(lit.Value)
			if err == nil && strings.Contains(strings.ToLower(v), "shutdown.exe") && enclosingFunc(f, lit.Pos()) != "advancedStartupArgs" {
				t.Errorf("%s: shutdown.exe outside advancedStartupArgs", fset.Position(lit.Pos()))
			}
			return true
		})
	}

	// 5. The guard really is a test-binary check.
	if !strings.Contains(sourceOf(t, prod, fset, "advancedStartupGuard"), "testing.Testing()") {
		t.Fatal("advancedStartupGuard no longer checks testing.Testing()")
	}
}

func sourceOf(t *testing.T, prod map[string]*ast.File, fset *token.FileSet, fn string) string {
	t.Helper()
	for name, f := range prod {
		for _, d := range f.Decls {
			if decl, ok := d.(*ast.FuncDecl); ok && decl.Name.Name == fn {
				src, _ := os.ReadFile(name)
				return string(src[fset.Position(decl.Pos()).Offset:fset.Position(decl.End()).Offset])
			}
		}
	}
	t.Fatalf("%s not found", fn)
	return ""
}

// The page sends the revision it showed, with confirm, and only after the
// saved-work box is ticked. Node runs the shipped handler with a fake API.
func TestBrowserBootOptionsSendsShownRevisionOnlyWhenSaved(t *testing.T) {
	node, err := exec.LookPath("node")
	if err != nil {
		t.Skip("Node.js unavailable for browser request behavior")
	}
	source, err := os.ReadFile("web/app.js")
	if err != nil {
		t.Fatal(err)
	}
	js := string(source)
	start := strings.Index(js, `$("boot-options-saved").onchange=`)
	end := strings.Index(js, `$("restart").onclick=()=>action(`)
	if start < 0 || end < start {
		t.Fatal("boot-options browser handler unavailable")
	}
	program := `
let busy = false, bootOptions = true, reviewedRevision = 7, sent = [];
const elements = {"boot-options-saved":{checked:false}, "boot-options-restart":{disabled:true}, status:{}, inspect:{hidden:true}};
const $ = id => elements[id];
function clearChecks() { bootOptions = false; reviewedRevision = 0; }
function action(fn) { return fn(); }
async function api(action, confirm, revision) { sent.push({action, confirm, revision}); return {message:'requested'}; }
` + js[start:end] + `
(async () => {
  elements["boot-options-saved"].onchange();
  if (!elements["boot-options-restart"].disabled) throw Error('enabled without saved work');
  await elements["boot-options-restart"].onclick();
  if (sent.length !== 0) throw Error('sent without saved work');
  elements["boot-options-saved"].checked = true;
  elements["boot-options-saved"].onchange();
  if (elements["boot-options-restart"].disabled) throw Error('not enabled after saved work');
  await elements["boot-options-restart"].onclick();
  if (sent.length !== 1 || sent[0].action !== 'advanced-startup' || sent[0].confirm !== true || sent[0].revision !== 7)
    throw Error('wrong request ' + JSON.stringify(sent));
  if (bootOptions || elements.inspect.hidden) throw Error('offer not cleared after the request');
  await elements["boot-options-restart"].onclick();
  if (sent.length !== 1) throw Error('second request without a new check');
})().catch(error => { console.error(error); process.exitCode = 1; });
`
	output, err := exec.Command(node, "-e", program).CombinedOutput()
	if err != nil {
		t.Fatalf("browser boot-options regression failed: %v\n%s", err, output)
	}
}
