// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"
)

// Only the current test executable is launched. Every descendant is finite and
// leaves a completion receipt before the parent test releases its directory.
func TestBoundedOutputOwnedHelperPass11(t *testing.T) {
	role := os.Getenv("BEAMO_PASS11_CAPTURE_ROLE")
	if role == "" {
		return
	}
	marker := os.Getenv("BEAMO_PASS11_CAPTURE_MARKER")
	switch role {
	case "emit":
		size, err := strconv.Atoi(os.Getenv("BEAMO_PASS11_CAPTURE_SIZE"))
		if err != nil || size < 0 || size > (2<<20)+1 {
			os.Exit(21)
		}
		chunk, _ := strconv.Atoi(os.Getenv("BEAMO_PASS11_CAPTURE_CHUNK"))
		if chunk <= 0 {
			chunk = size
		}
		for remaining := size; remaining > 0; {
			count := min(chunk, remaining)
			fmt.Print(strings.Repeat("x", count))
			remaining -= count
		}
		fmt.Fprint(os.Stderr, "ignored diagnostic")
		code, _ := strconv.Atoi(os.Getenv("BEAMO_PASS11_CAPTURE_EXIT"))
		os.Exit(code)
	case "descendant", "closed-descendant":
		if role == "closed-descendant" {
			_ = os.Stdout.Close()
			_ = os.Stderr.Close()
		}
		if os.WriteFile(marker, []byte("started"), 0600) != nil {
			os.Exit(22)
		}
		time.Sleep(700 * time.Millisecond)
		if os.WriteFile(marker+".done", []byte("finished"), 0600) != nil {
			os.Exit(23)
		}
		os.Exit(0)
	case "parent", "closed-parent":
		executable, err := os.Executable()
		if err != nil {
			os.Exit(24)
		}
		childRole := "descendant"
		if role == "closed-parent" {
			childRole = "closed-descendant"
		}
		child := exec.Command(executable, "-test.run=^TestBoundedOutputOwnedHelperPass11$")
		child.Env = captureHelperEnvironmentPass11(childRole, marker)
		pipe := os.Getenv("BEAMO_PASS11_CAPTURE_PIPE")
		if pipe == "stdout" || pipe == "both" {
			child.Stdout = os.Stdout
		}
		if pipe == "stderr" || pipe == "both" {
			child.Stderr = os.Stderr
		}
		if child.Start() != nil {
			os.Exit(25)
		}
		deadline := time.Now().Add(3 * time.Second)
		for {
			if _, err := os.Stat(marker); err == nil {
				break
			}
			if time.Now().After(deadline) {
				os.Exit(26)
			}
			time.Sleep(time.Millisecond)
		}
		if os.Getenv("BEAMO_PASS11_CAPTURE_TRIGGER") == "cancel" {
			time.Sleep(3 * time.Second)
		}
		os.Exit(0)
	case "direct":
		if os.WriteFile(marker, []byte("started"), 0600) != nil {
			os.Exit(27)
		}
		time.Sleep(3 * time.Second)
		os.Exit(0)
	default:
		os.Exit(28)
	}
}

func captureHelperEnvironmentPass11(role, marker string, settings ...string) []string {
	env := []string{}
	for _, setting := range os.Environ() {
		if !strings.HasPrefix(setting, "BEAMO_PASS11_CAPTURE_") && !strings.HasPrefix(setting, "GORACE=") {
			env = append(env, setting)
		}
	}
	// Remove only the race runtime's one-second exit pause in child fixtures;
	// race detection remains enabled for every instrumented process.
	env = append(env, "GORACE=atexit_sleep_ms=0", "BEAMO_PASS11_CAPTURE_ROLE="+role,
		"BEAMO_PASS11_CAPTURE_MARKER="+marker)
	return append(env, settings...)
}

func captureHelperCommandPass11(t *testing.T, ctx context.Context, role, marker string, settings ...string) *exec.Cmd {
	t.Helper()
	executable, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	cmd := exec.CommandContext(ctx, executable, "-test.run=^TestBoundedOutputOwnedHelperPass11$")
	cmd.Env = captureHelperEnvironmentPass11(role, marker, settings...)
	return cmd
}

func waitCaptureReceiptPass11(t *testing.T, path string) {
	t.Helper()
	deadline := time.Now().Add(4 * time.Second)
	for {
		if _, err := os.Stat(path); err == nil {
			return
		}
		if time.Now().After(deadline) {
			t.Fatal("owned helper did not produce receipt", path)
		}
		time.Sleep(time.Millisecond)
	}
}

func TestBoundedOutputBoundsInheritedPipesPass11(t *testing.T) {
	for _, trigger := range []string{"cancel", "parent-exit"} {
		for _, pipe := range []string{"stdout", "stderr", "both"} {
			for _, delay := range []time.Duration{0, 40 * time.Millisecond} {
				t.Run(fmt.Sprintf("%s/%s/%s", trigger, pipe, delay), func(t *testing.T) {
					marker := filepath.Join(t.TempDir(), "started")
					ctx, cancel := context.WithCancel(context.Background())
					defer cancel()
					cmd := captureHelperCommandPass11(t, ctx, "parent", marker,
						"BEAMO_PASS11_CAPTURE_PIPE="+pipe, "BEAMO_PASS11_CAPTURE_TRIGGER="+trigger)
					cmd.WaitDelay = delay
					done := make(chan error, 1)
					go func() { _, err := boundedOutput(cmd, 1024); done <- err }()
					waitCaptureReceiptPass11(t, marker)
					t.Cleanup(func() { waitCaptureReceiptPass11(t, marker+".done") })
					started := time.Now()
					if trigger == "cancel" {
						cancel()
					}
					err := <-done
					elapsed := time.Since(started)
					t.Logf("trigger=%s pipe=%s configured=%s return=%s error=%v", trigger, pipe, delay, elapsed, err)
					if err == nil || elapsed > 500*time.Millisecond {
						t.Fatalf("incomplete inherited-pipe capture did not refuse promptly: %s %v", elapsed, err)
					}
					if trigger == "parent-exit" && !errors.Is(err, exec.ErrWaitDelay) {
						t.Fatalf("parent-exit incomplete capture lost its wait-delay error: %v", err)
					}
					wantDelay := delay
					if wantDelay == 0 {
						wantDelay = 100 * time.Millisecond
					}
					if cmd.WaitDelay != wantDelay {
						t.Fatalf("drain limit changed unexpectedly: %s want %s", cmd.WaitDelay, wantDelay)
					}
				})
			}
		}
	}
}

func TestBoundedOutputCaptureControlsPass11(t *testing.T) {
	for _, size := range []int{0, 1, 1024, 1025} {
		t.Run(fmt.Sprintf("size-%d", size), func(t *testing.T) {
			cmd := captureHelperCommandPass11(t, context.Background(), "emit", "",
				fmt.Sprintf("BEAMO_PASS11_CAPTURE_SIZE=%d", size), "BEAMO_PASS11_CAPTURE_EXIT=0")
			got, err := boundedOutput(cmd, 1024)
			if size <= 1024 {
				if err != nil || string(got) != strings.Repeat("x", size) {
					t.Fatalf("normal bounded output changed: %d %q %v", size, got, err)
				}
			} else if err == nil || len(got) > 1024 {
				t.Fatalf("oversized output accepted: %d %v", len(got), err)
			}
		})
	}
	t.Run("failed-exit", func(t *testing.T) {
		cmd := captureHelperCommandPass11(t, context.Background(), "emit", "", "BEAMO_PASS11_CAPTURE_SIZE=3", "BEAMO_PASS11_CAPTURE_EXIT=7")
		got, err := boundedOutput(cmd, 1024)
		if err == nil || string(got) != "xxx" {
			t.Fatalf("failed helper result changed: %q %v", got, err)
		}
	})
	t.Run("missing-executable", func(t *testing.T) {
		got, err := boundedOutput(exec.Command(filepath.Join(t.TempDir(), "absent-helper")), 1024)
		if err == nil || len(got) != 0 {
			t.Fatalf("missing helper was accepted: %q %v", got, err)
		}
	})
	t.Run("already-cancelled", func(t *testing.T) {
		ctx, cancel := context.WithCancel(context.Background())
		cancel()
		cmd := captureHelperCommandPass11(t, ctx, "emit", "", "BEAMO_PASS11_CAPTURE_SIZE=1", "BEAMO_PASS11_CAPTURE_EXIT=0")
		got, err := boundedOutput(cmd, 1024)
		if err == nil || len(got) != 0 {
			t.Fatalf("cancelled helper executed: %q %v", got, err)
		}
	})
	t.Run("direct-cancel", func(t *testing.T) {
		marker := filepath.Join(t.TempDir(), "started")
		ctx, cancel := context.WithCancel(context.Background())
		defer cancel()
		cmd := captureHelperCommandPass11(t, ctx, "direct", marker)
		done := make(chan error, 1)
		go func() { _, err := boundedOutput(cmd, 1024); done <- err }()
		waitCaptureReceiptPass11(t, marker)
		started := time.Now()
		cancel()
		if err := <-done; err == nil || time.Since(started) > 500*time.Millisecond {
			t.Fatalf("direct cancellation did not refuse promptly: %v", err)
		}
	})
	t.Run("descendant-releases-pipes", func(t *testing.T) {
		marker := filepath.Join(t.TempDir(), "started")
		cmd := captureHelperCommandPass11(t, context.Background(), "closed-parent", marker,
			"BEAMO_PASS11_CAPTURE_PIPE=both", "BEAMO_PASS11_CAPTURE_TRIGGER=parent-exit")
		t.Cleanup(func() { waitCaptureReceiptPass11(t, marker+".done") })
		started := time.Now()
		got, err := boundedOutput(cmd, 1024)
		if err != nil || len(got) != 0 || time.Since(started) > 500*time.Millisecond {
			t.Fatalf("released pipes delayed or failed normal parent: %q %v", got, err)
		}
	})
}

func TestBoundedOutputDrainLimitControlsPass11(t *testing.T) {
	for _, delay := range []time.Duration{-time.Second, 20 * time.Millisecond, 100 * time.Millisecond, time.Second} {
		t.Run(delay.String(), func(t *testing.T) {
			cmd := captureHelperCommandPass11(t, context.Background(), "emit", "", "BEAMO_PASS11_CAPTURE_SIZE=1", "BEAMO_PASS11_CAPTURE_EXIT=0")
			cmd.WaitDelay = delay
			got, err := boundedOutput(cmd, 1024)
			if err != nil || string(got) != "x" {
				t.Fatalf("normal output changed with caller drain limit: %q %v", got, err)
			}
			want := delay
			if delay <= 0 || delay > 100*time.Millisecond {
				want = 100 * time.Millisecond
			}
			if cmd.WaitDelay != want {
				t.Fatalf("drain limit %s, want %s", cmd.WaitDelay, want)
			}
		})
	}
}

func TestBoundedOutputEnforcesCaptureBudgetPass11(t *testing.T) {
	for _, budget := range []int{0, 1, 1024, 1 << 20} {
		counts := []int{budget, budget + 1}
		if budget > 0 {
			counts = append([]int{0}, counts...)
		}
		for _, size := range counts {
			for _, chunk := range []int{0, 37} {
				t.Run(fmt.Sprintf("budget-%d/bytes-%d/chunk-%d", budget, size, chunk), func(t *testing.T) {
					cmd := captureHelperCommandPass11(t, context.Background(), "emit", "",
						fmt.Sprintf("BEAMO_PASS11_CAPTURE_SIZE=%d", size), "BEAMO_PASS11_CAPTURE_EXIT=0",
						fmt.Sprintf("BEAMO_PASS11_CAPTURE_CHUNK=%d", chunk))
					got, err := boundedOutput(cmd, budget)
					if size <= budget {
						if err != nil || string(got) != strings.Repeat("x", size) {
							t.Fatalf("within-budget output changed: %d/%d %q %v", size, budget, got, err)
						}
					} else if err == nil || len(got) > budget {
						t.Fatalf("capture budget bypassed: input=%d budget=%d captured=%d err=%v", size, budget, len(got), err)
					}
				})
			}
		}
	}
}
