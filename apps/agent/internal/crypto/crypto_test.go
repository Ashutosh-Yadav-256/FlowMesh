package crypto

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"testing"
)

func TestVerifySignature_Valid(t *testing.T) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("failed to generate key: %v", err)
	}

	pubB64 := base64.StdEncoding.EncodeToString(pub)
	payload := []byte(`{"connection_id":"orders-db","connector":"postgres","id":"cmd-1","operation":"read"}`)
	sig := ed25519.Sign(priv, payload)
	sigB64 := base64.StdEncoding.EncodeToString(sig)

	ok, err := VerifySignature(pubB64, payload, sigB64)
	if err != nil || !ok {
		t.Fatalf("expected valid signature, got ok=%v, err=%v", ok, err)
	}
}

func TestVerifySignature_TamperedPayload(t *testing.T) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("failed to generate key: %v", err)
	}

	pubB64 := base64.StdEncoding.EncodeToString(pub)
	payload := []byte(`{"connection_id":"orders-db","connector":"postgres","id":"cmd-1","operation":"read"}`)
	sig := ed25519.Sign(priv, payload)
	sigB64 := base64.StdEncoding.EncodeToString(sig)

	tamperedPayload := []byte(`{"connection_id":"orders-db","connector":"postgres","id":"cmd-1","operation":"drop"}`)

	ok, err := VerifySignature(pubB64, tamperedPayload, sigB64)
	if ok || err == nil {
		t.Fatalf("expected signature verification to fail for tampered payload, got ok=%v, err=%v", ok, err)
	}
}

func TestVerifySignature_WrongKey(t *testing.T) {
	_, priv1, _ := ed25519.GenerateKey(rand.Reader)
	pub2, _, _ := ed25519.GenerateKey(rand.Reader)

	pub2B64 := base64.StdEncoding.EncodeToString(pub2)
	payload := []byte(`{"id":"cmd-1"}`)
	sig := ed25519.Sign(priv1, payload)
	sigB64 := base64.StdEncoding.EncodeToString(sig)

	ok, err := VerifySignature(pub2B64, payload, sigB64)
	if ok || err == nil {
		t.Fatalf("expected verification to fail with wrong public key, got ok=%v, err=%v", ok, err)
	}
}

func TestVerifyCommandPayload_Map(t *testing.T) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("failed to generate key: %v", err)
	}

	pubB64 := base64.StdEncoding.EncodeToString(pub)

	cmd := map[string]interface{}{
		"id":            "cmd-100",
		"connector":     "postgres",
		"connection_id": "orders-db",
		"operation":     "read",
		"limit":         float64(50),
	}

	canonicalBytes, err := CanonicalizeJSON(cmd)
	if err != nil {
		t.Fatalf("canonicalize failed: %v", err)
	}

	sig := ed25519.Sign(priv, canonicalBytes)
	sigB64 := base64.StdEncoding.EncodeToString(sig)

	ok, err := VerifyCommandPayload(pubB64, cmd, sigB64)
	if err != nil || !ok {
		t.Fatalf("expected command payload verification to succeed, got ok=%v, err=%v", ok, err)
	}
}
