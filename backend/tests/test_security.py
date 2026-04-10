import hashlib
import sys
from pathlib import Path

import pytest
from jwt import InvalidTokenError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.core.security import (
    decode_jwt,
    encode_jwt,
    hash_password,
    verify_ed25519_signature,
    verify_password,
)
from cli.core.crypto import generate_ed25519_keypair, sign_checksum


def test_password_hash_and_verify():
    password = "s3cur3-password"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_jwt_encode_decode_roundtrip():
    token = encode_jwt({"sub": "alice", "role": "developer"})
    decoded = decode_jwt(token)

    assert decoded["sub"] == "alice"
    assert decoded["role"] == "developer"
    assert "exp" in decoded


def test_jwt_decode_invalid_signature_raises():
    token = encode_jwt({"sub": "alice"})
    # Tamper with the first character of the signature part to guarantee a failure
    parts = token.split(".")
    sig = parts[2]
    tampered_sig = ("a" if sig[0] != "a" else "b") + sig[1:]
    tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"

    with pytest.raises(InvalidTokenError):
        decode_jwt(tampered_token)


def test_verify_ed25519_signature_accepts_cli_signature(tmp_path):
    key_path = tmp_path / "id_ed25519"
    public_key_hex = generate_ed25519_keypair(key_path=key_path)
    checksum_hex = hashlib.sha256(b"package-content-v1").hexdigest()
    signature_hex = sign_checksum(checksum_hex, key_path=key_path)

    assert verify_ed25519_signature(public_key_hex, signature_hex, checksum_hex) is True


def test_verify_ed25519_signature_rejects_tampered_checksum(tmp_path):
    key_path = tmp_path / "id_ed25519"
    public_key_hex = generate_ed25519_keypair(key_path=key_path)
    checksum_hex = hashlib.sha256(b"original-content").hexdigest()
    signature_hex = sign_checksum(checksum_hex, key_path=key_path)
    tampered_checksum_hex = hashlib.sha256(b"tampered-content").hexdigest()

    assert (
        verify_ed25519_signature(public_key_hex, signature_hex, tampered_checksum_hex)
        is False
    )


def test_verify_ed25519_signature_rejects_malformed_hex():
    assert verify_ed25519_signature("zz", "00", "00") is False
