package crypto

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
)

func CanonicalizeJSON(v interface{}) ([]byte, error) {
	return json.Marshal(v)
}

func VerifySignature(publicKeyB64 string, data []byte, signatureB64 string) (bool, error) {
	pubKeyBytes, err := base64.StdEncoding.DecodeString(publicKeyB64)
	if err != nil {
		return false, fmt.Errorf("invalid base64 public key: %w", err)
	}
	if len(pubKeyBytes) != ed25519.PublicKeySize {
		return false, fmt.Errorf("invalid public key length: expected %d bytes, got %d", ed25519.PublicKeySize, len(pubKeyBytes))
	}

	sigBytes, err := base64.StdEncoding.DecodeString(signatureB64)
	if err != nil {
		return false, fmt.Errorf("invalid base64 signature: %w", err)
	}
	if len(sigBytes) != ed25519.SignatureSize {
		return false, fmt.Errorf("invalid signature length: expected %d bytes, got %d", ed25519.SignatureSize, len(sigBytes))
	}

	if !ed25519.Verify(pubKeyBytes, data, sigBytes) {
		return false, errors.New("cryptographic signature verification failed: signature does not match payload")
	}

	return true, nil
}

func VerifyCommandPayload(publicKeyB64 string, command interface{}, signatureB64 string) (bool, error) {
	canonicalBytes, err := CanonicalizeJSON(command)
	if err != nil {
		return false, fmt.Errorf("failed to canonicalize command: %w", err)
	}
	return VerifySignature(publicKeyB64, canonicalBytes, signatureB64)
}
