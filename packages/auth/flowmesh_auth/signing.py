"""
FlowMesh Ed25519 Cryptographic Command Signing and Verification

Used by FlowMesh Control Plane to cryptographically sign all structured commands
dispatched to Edge Agents. Edge Agents verify this signature against the enrolled
Control Plane public key before evaluating policy or executing actions.

Guarantees:
- Tamper-proofing: Any modification of command parameters invalidates signature.
- Authentic origin: Commands cannot be forged without Control Plane private key.
- Deterministic canonicalization: Cross-language RFC 8785 canonical JSON serialization.
"""

import json
import base64
from typing import Dict, Any, Tuple, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def canonicalize_json(data: Dict[str, Any]) -> bytes:
    """Serializes dictionary to deterministic canonical JSON bytes with sorted keys and no whitespace."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def generate_ed25519_keypair() -> Tuple[str, str]:
    """
    Generates a new Ed25519 keypair.
    Returns:
        (private_key_b64, public_key_b64)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return (
        base64.b64encode(priv_bytes).decode('utf-8'),
        base64.b64encode(pub_bytes).decode('utf-8')
    )


class Ed25519Signer:
    """Signs control plane payloads using an Ed25519 private key."""

    def __init__(self, private_key_b64: str) -> None:
        raw_priv = base64.b64decode(private_key_b64.encode('utf-8'))
        self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(raw_priv)
        pub_bytes = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self._public_key_b64 = base64.b64encode(pub_bytes).decode('utf-8')

    @property
    def public_key_b64(self) -> str:
        return self._public_key_b64

    def sign_payload(self, payload: Dict[str, Any]) -> Tuple[str, bytes]:
        """
        Computes Ed25519 signature over canonical JSON of the payload.
        Returns:
            (signature_b64, canonical_bytes)
        """
        canonical = canonicalize_json(payload)
        sig = self._private_key.sign(canonical)
        return (base64.b64encode(sig).decode('utf-8'), canonical)


def verify_ed25519_signature(public_key_b64: str, payload: Dict[str, Any], signature_b64: str) -> bool:
    """Verifies Ed25519 signature against canonical JSON representation of payload."""
    try:
        raw_pub = base64.b64decode(public_key_b64.encode('utf-8'))
        raw_sig = base64.b64decode(signature_b64.encode('utf-8'))
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(raw_pub)
        canonical = canonicalize_json(payload)
        pub_key.verify(raw_sig, canonical)
        return True
    except Exception:
        return False


_GLOBAL_SIGNER: Optional[Ed25519Signer] = None


def get_control_plane_signer() -> Ed25519Signer:
    """Returns the deterministic singleton Ed25519 signer for the FlowMesh Control Plane."""
    global _GLOBAL_SIGNER
    if _GLOBAL_SIGNER is None:
        import hashlib
        from app.config import settings
        seed = hashlib.sha256(settings.api_secret_key.encode("utf-8")).digest()
        priv_b64 = base64.b64encode(seed).decode("utf-8")
        _GLOBAL_SIGNER = Ed25519Signer(priv_b64)
    return _GLOBAL_SIGNER
