from pathlib import Path
from typing import Optional, Union

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def generate_ed25519_keypair(key_path: Optional[Union[str, Path]] = None) -> str:
    private_key_path = (
        Path(key_path) if key_path else Path.home() / ".vget" / "id_ed25519"
    )
    private_key_path.parent.mkdir(parents=True, exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_key_path.write_bytes(private_bytes)

    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return public_bytes.hex()


def sha256_file_hash(file_path: Union[str, Path]) -> str:
    import hashlib

    path = Path(file_path)
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sign_checksum(
    checksum_hex: str, key_path: Optional[Union[str, Path]] = None
) -> str:
    private_key_path = (
        Path(key_path) if key_path else Path.home() / ".vget" / "id_ed25519"
    )
    private_key_bytes = private_key_path.read_bytes()
    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    checksum_bytes = bytes.fromhex(checksum_hex)
    signature = private_key.sign(checksum_bytes)
    return signature.hex()
