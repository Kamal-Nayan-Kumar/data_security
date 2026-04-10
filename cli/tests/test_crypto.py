import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cli.core.crypto import (
    generate_ed25519_keypair,
    sha256_file_hash,
    sign_checksum,
)
from backend.core.security import verify_ed25519_signature


def test_generate_ed25519_keypair_writes_private_key_and_returns_public_hex(tmp_path):
    key_path = tmp_path / "id_ed25519"
    public_key_hex = generate_ed25519_keypair(key_path=key_path)

    assert key_path.exists()
    assert len(key_path.read_bytes()) == 32
    assert isinstance(public_key_hex, str)
    assert len(bytes.fromhex(public_key_hex)) == 32


def test_sha256_file_hash_returns_expected_hex(tmp_path):
    sample_file = tmp_path / "sample.pkg"
    sample_file.write_bytes(b"hello-vget")

    expected = hashlib.sha256(b"hello-vget").hexdigest()
    assert sha256_file_hash(sample_file) == expected


def test_sign_checksum_returns_hex_signature(tmp_path):
    key_path = tmp_path / "id_ed25519"
    generate_ed25519_keypair(key_path=key_path)
    checksum_hex = hashlib.sha256(b"file-content").hexdigest()

    signature_hex = sign_checksum(checksum_hex, key_path=key_path)

    assert isinstance(signature_hex, str)
    assert len(bytes.fromhex(signature_hex)) == 64


def test_cli_signature_validates_with_backend_logic(tmp_path):
    key_path = tmp_path / "id_ed25519"
    public_key_hex = generate_ed25519_keypair(key_path=key_path)
    checksum_hex = hashlib.sha256(b"cross-system-signature-test").hexdigest()
    signature_hex = sign_checksum(checksum_hex, key_path=key_path)

    assert verify_ed25519_signature(public_key_hex, signature_hex, checksum_hex) is True
