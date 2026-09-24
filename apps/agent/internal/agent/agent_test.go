package agent

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"sync/atomic"
	"testing"
	"time"

	"github.com/flowmesh/flowmesh/apps/agent/internal/buffer"
	"github.com/flowmesh/flowmesh/apps/agent/internal/crypto"
	"github.com/flowmesh/flowmesh/apps/agent/internal/policy"
)

func setupTestAgent(t *testing.T) (*Agent, ed25519.PrivateKey, string, *buffer.Buffer, func()) {

	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("failed to generate key: %v", err)
	}
	pubB64 := base64.StdEncoding.EncodeToString(pub)

	tempDir, err := os.MkdirTemp("", "agent_test_*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	buf, err := buffer.New(filepath.Join(tempDir, "agent.db"))
	if err != nil {
		t.Fatalf("failed to init buffer: %v", err)
	}

	pe := policy.NewEngine()
	pe.AddRule("postgres", "orders-db", policy.PolicyRule{
		AllowedOperations: []string{"read", "query"},
		AllowedResources:  []string{"orders", "customers"},
		MaxLimit:          100,
	})

	cfg := Config{
		ID:                    "test-agent-01",
		TenantID:              "tenant_test",
		Name:                  "Test Agent",
		Version:               "v0.5.0",
		ControlPlanePublicKey: pubB64,
		HeartbeatInterval:     100 * time.Millisecond,
		PollInterval:          100 * time.Millisecond,
	}

	ag := New(cfg, pe, buf)

	cleanup := func() {
		buf.Close()
		os.RemoveAll(tempDir)
	}

	return ag, priv, pubB64, buf, cleanup
}

func signCommand(t *testing.T, priv ed25519.PrivateKey, cmd policy.Command) string {
	raw, err := crypto.CanonicalizeJSON(cmd)
	if err != nil {
		t.Fatalf("failed to canonicalize: %v", err)
	}
	sig := ed25519.Sign(priv, raw)
	return base64.StdEncoding.EncodeToString(sig)
}

func TestAgent_ProcessCommand_ValidSignatureAndPolicy(t *testing.T) {
	ag, priv, _, _, cleanup := setupTestAgent(t)
	defer cleanup()

	cmd := policy.Command{
		ID:           "cmd-valid-1",
		Connector:    "postgres",
		ConnectionID: "orders-db",
		Operation:    "query",
		Resource:     "orders",
		Limit:        50,
	}

	sig := signCommand(t, priv, cmd)
	envelope := SignedCommandEnvelope{Command: cmd, Signature: sig}

	res := ag.ProcessCommand(envelope)
	if res.Status != "COMPLETED" {
		t.Fatalf("expected COMPLETED, got status: %s, error: %s", res.Status, res.Error)
	}
	if res.CommandID != "cmd-valid-1" {
		t.Errorf("expected command ID 'cmd-valid-1', got %s", res.CommandID)
	}
}

func TestAgent_ProcessCommand_RejectedInvalidSignature(t *testing.T) {
	ag, _, _, _, cleanup := setupTestAgent(t)
	defer cleanup()

	cmd := policy.Command{
		ID:           "cmd-tampered-1",
		Connector:    "postgres",
		ConnectionID: "orders-db",
		Operation:    "query",
		Resource:     "orders",
		Limit:        50,
	}

	_, roguePriv, _ := ed25519.GenerateKey(rand.Reader)
	sig := signCommand(t, roguePriv, cmd)

	envelope := SignedCommandEnvelope{Command: cmd, Signature: sig}
	res := ag.ProcessCommand(envelope)

	if res.Status != "REJECTED_SIGNATURE" {
		t.Fatalf("expected REJECTED_SIGNATURE, got %s", res.Status)
	}
}

func TestAgent_ProcessCommand_RejectedPolicyViolation(t *testing.T) {
	ag, priv, _, _, cleanup := setupTestAgent(t)
	defer cleanup()

	cmd := policy.Command{
		ID:           "cmd-forbidden-op",
		Connector:    "postgres",
		ConnectionID: "orders-db",
		Operation:    "drop",
		Resource:     "orders",
	}

	sig := signCommand(t, priv, cmd)
	envelope := SignedCommandEnvelope{Command: cmd, Signature: sig}

	res := ag.ProcessCommand(envelope)
	if res.Status != "REJECTED_POLICY" {
		t.Fatalf("expected REJECTED_POLICY, got %s", res.Status)
	}
}

func TestAgent_OfflineBufferingAndDrain(t *testing.T) {
	ag, priv, _, buf, cleanup := setupTestAgent(t)
	defer cleanup()

	var receivedResult atomic.Bool

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/v1/agents/test-agent-01/commands/cmd-buffered-1/result" {
			receivedResult.Store(true)
			w.WriteHeader(http.StatusOK)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	ag.cfg.ControlPlaneURL = "http://127.0.0.1:1"

	cmd := policy.Command{
		ID:           "cmd-buffered-1",
		Connector:    "postgres",
		ConnectionID: "orders-db",
		Operation:    "query",
		Resource:     "orders",
		Limit:        10,
	}
	sig := signCommand(t, priv, cmd)
	res := ag.ProcessCommand(SignedCommandEnvelope{Command: cmd, Signature: sig})

	ctx := context.Background()

	ag.ReportResult(ctx, res)

	count, err := buf.Count()
	if err != nil || count != 1 {
		t.Fatalf("expected 1 buffered item in SQLite, got %d, err: %v", count, err)
	}

	ag.cfg.ControlPlaneURL = server.URL

	ag.DrainBuffer(ctx)

	if !receivedResult.Load() {
		t.Errorf("expected server to have received the drained command result")
	}

	count, _ = buf.Count()
	if count != 0 {
		t.Errorf("expected 0 buffered items after drain, got %d", count)
	}
}
