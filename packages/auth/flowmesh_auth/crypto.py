"""
FlowMesh Envelope Encryption Service

Implements enterprise-grade envelope encryption:
1. Master KEK (Key Encryption Key): 256-bit key from environment/KMS.
2. Tenant DEK (Data Encryption Key): Unique 256-bit AES key per tenant.
3. Payload Encryption: Connection secrets are encrypted with the tenant DEK
   using AES-256-GCM with a unique 96-bit nonce and authentication tag.
4. Secrets are write-only over the API: plaintext secrets are never returned,
   never logged, and old ciphertext is unrecoverable after credential rotation.
"""

import os
import json
import base64
from typing import Tuple, Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


def get_master_kek() -> bytes:
    """Derives 32-byte (256-bit) Master Key Encryption Key from configuration."""
    raw = settings.encryption_master_key

    if len(raw) == 64:
        try:
            return bytes.fromhex(raw)
        except ValueError:
            pass
    import hashlib
    return hashlib.sha256(raw.encode("utf-8")).digest()


class EnvelopeCrypto:
    """Enterprise envelope encryption provider using AES-256-GCM."""

    def __init__(self, master_kek: Optional[bytes] = None) -> None:
        self.master_kek = master_kek or get_master_kek()
        if len(self.master_kek) != 32:
            raise ValueError(f"Master KEK must be exactly 32 bytes (256 bits), got {len(self.master_kek)}")

    def generate_dek(self) -> bytes:
        """Generates a random 256-bit Data Encryption Key."""
        return AESGCM.generate_key(bit_length=256)

    def wrap_dek(self, dek: bytes, tenant_id: str) -> str:
        """Encrypts a tenant DEK with the Master KEK, binding it to tenant_id via Associated Data."""
        aesgcm = AESGCM(self.master_kek)
        nonce = os.urandom(12)
        aad = tenant_id.encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, dek, aad)

        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def unwrap_dek(self, wrapped_dek_b64: str, tenant_id: str) -> bytes:
        """Decrypts a wrapped tenant DEK using Master KEK and verifies tenant_id."""
        raw = base64.b64decode(wrapped_dek_b64.encode("utf-8"))
        nonce = raw[:12]
        ciphertext = raw[12:]
        aad = tenant_id.encode("utf-8")
        aesgcm = AESGCM(self.master_kek)
        return aesgcm.decrypt(nonce, ciphertext, aad)

    def encrypt_secret(self, dek: bytes, secret_data: Dict[str, Any], connection_id: str) -> str:
        """Encrypts secret payload with tenant DEK using AES-256-GCM with connection_id binding."""
        aesgcm = AESGCM(dek)
        nonce = os.urandom(12)
        plaintext = json.dumps(secret_data).encode("utf-8")
        aad = connection_id.encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt_secret(self, dek: bytes, encrypted_b64: str, connection_id: str) -> Dict[str, Any]:
        """Decrypts and authenticates secret payload with tenant DEK."""
        raw = base64.b64decode(encrypted_b64.encode("utf-8"))
        nonce = raw[:12]
        ciphertext = raw[12:]
        aad = connection_id.encode("utf-8")
        aesgcm = AESGCM(dek)
        plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
        return json.loads(plaintext.decode("utf-8"))


envelope_crypto = EnvelopeCrypto()
