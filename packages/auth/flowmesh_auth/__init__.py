"""FlowMesh Authentication, RBAC, and Cryptographic Primitives Package."""

from flowmesh_auth.crypto import EnvelopeCrypto
from flowmesh_auth.rbac import Role, Resource, Action, is_allowed
from flowmesh_auth.signing import (
    Ed25519Signer,
    generate_ed25519_keypair,
    verify_ed25519_signature,
    get_control_plane_signer,
)

__all__ = [
    "EnvelopeCrypto",
    "Role",
    "Resource",
    "Action",
    "is_allowed",
    "Ed25519Signer",
    "generate_ed25519_keypair",
    "verify_ed25519_signature",
    "get_control_plane_signer",
]
