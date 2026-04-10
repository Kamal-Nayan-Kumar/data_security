from datetime import datetime, timedelta, timezone
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

JWT_SECRET = "supersecret_minimum_32_characters_long_for_security"
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def encode_jwt(payload: dict, expires_in_seconds: int = 3600) -> str:
    token_payload = dict(payload)
    token_payload["exp"] = datetime.now(timezone.utc) + timedelta(
        seconds=expires_in_seconds
    )
    return jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def verify_ed25519_signature(
    public_key_hex: str, signature_hex: str, checksum_hex: str
) -> bool:
    try:
        public_key_bytes = bytes.fromhex(public_key_hex)
        signature_bytes = bytes.fromhex(signature_hex)
        checksum_bytes = bytes.fromhex(checksum_hex)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature_bytes, checksum_bytes)
        return True
    except (ValueError, InvalidSignature):
        return False
