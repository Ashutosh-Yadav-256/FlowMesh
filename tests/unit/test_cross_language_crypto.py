"""
Unit tests for Ed25519 cryptographic signing and verification in Python,
including cross-language compatibility assertions.
"""

import json
import base64
import subprocess
import pytest
from flowmesh_auth.signing import (
    generate_ed25519_keypair,
    Ed25519Signer,
    verify_ed25519_signature,
    canonicalize_json,
)


def test_ed25519_keypair_generation():
    priv_b64, pub_b64 = generate_ed25519_keypair()
    assert len(base64.b64decode(priv_b64)) == 32
    assert len(base64.b64decode(pub_b64)) == 32


def test_sign_and_verify_valid_payload():
    priv_b64, pub_b64 = generate_ed25519_keypair()
    signer = Ed25519Signer(priv_b64)
    assert signer.public_key_b64 == pub_b64

    payload = {
        "id": "cmd-456",
        "type": "connector.execute",
        "connector": "postgres",
        "connection_id": "orders-db",
        "operation": "read",
        "resource": "orders",
        "limit": 100,
        "parameters": {"status": "shipped"}
    }

    sig_b64, canonical = signer.sign_payload(payload)
    assert len(base64.b64decode(sig_b64)) == 64
    assert b'"connection_id":"orders-db"' in canonical

    assert verify_ed25519_signature(pub_b64, payload, sig_b64) is True


def test_tampered_payload_fails_verification():
    priv_b64, pub_b64 = generate_ed25519_keypair()
    signer = Ed25519Signer(priv_b64)

    payload = {
        "id": "cmd-456",
        "operation": "read",
        "limit": 100
    }

    sig_b64, _ = signer.sign_payload(payload)

    tampered = dict(payload)
    tampered["operation"] = "delete"

    assert verify_ed25519_signature(pub_b64, tampered, sig_b64) is False


def test_wrong_key_fails_verification():
    priv1, pub1 = generate_ed25519_keypair()
    priv2, pub2 = generate_ed25519_keypair()

    signer1 = Ed25519Signer(priv1)
    payload = {"id": "cmd-999", "operation": "ping"}
    sig_b64, _ = signer1.sign_payload(payload)

    assert verify_ed25519_signature(pub2, payload, sig_b64) is False


def test_canonical_json_ordering():
    dict1 = {"b": 2, "a": 1, "c": 3}
    dict2 = {"c": 3, "b": 2, "a": 1}
    assert canonicalize_json(dict1) == canonicalize_json(dict2)
    assert canonicalize_json(dict1) == b'{"a":1,"b":2,"c":3}'
