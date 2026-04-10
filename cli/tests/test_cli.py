# pyright: reportMissingImports=false
import hashlib
import json
import sys
from pathlib import Path

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cli import main as cli_main


runner = CliRunner()


def test_keygen_creates_expected_files_and_config(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    result = runner.invoke(cli_main.app, ["keygen"])

    assert result.exit_code == 0
    assert "Generated Ed25519 keypair" in result.stdout

    vget_dir = tmp_path / ".vget"
    private_key = vget_dir / "id_ed25519"
    public_key = vget_dir / "id_ed25519.pub"
    config_path = vget_dir / "config.json"

    assert private_key.exists()
    assert public_key.exists()
    assert config_path.exists()
    assert len(private_key.read_bytes()) == 32
    assert len(bytes.fromhex(public_key.read_text().strip())) == 32

    config = json.loads(config_path.read_text())
    assert config["private_key_path"] == str(private_key)
    assert config["public_key_path"] == str(public_key)


def test_publish_sends_expected_multipart_request(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    vget_dir = tmp_path / ".vget"
    vget_dir.mkdir(parents=True)

    package_path = tmp_path / "demo.pkg"
    package_bytes = b"demo package bytes"
    package_path.write_bytes(package_bytes)

    token = "jwt-token-123"
    (vget_dir / "token").write_text(token)

    cli_main.generate_ed25519_keypair(key_path=vget_dir / "id_ed25519")
    (vget_dir / "config.json").write_text(json.dumps({"developer_username": "alice"}))

    captured = {}

    class DummyResponse:
        status_code = 200

        def raise_for_status(self):
            return None

    class DummyClient:
        def __init__(self, *args, **kwargs):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, data=None, files=None, headers=None):
            captured["url"] = url
            captured["data"] = data
            captured["headers"] = headers
            assert files is not None
            file_tuple = files["file"]
            captured["file_name"] = file_tuple[0]
            captured["file_content"] = file_tuple[1].read()
            captured["file_content_type"] = file_tuple[2]
            return DummyResponse()

    monkeypatch.setattr(cli_main.httpx, "Client", DummyClient)

    result = runner.invoke(
        cli_main.app,
        ["publish", "--path", str(package_path), "--version", "1.2.3"],
    )

    assert result.exit_code == 0
    assert "Package published successfully" in result.stdout
    assert captured["url"] == "/api/v1/developer/upload"
    assert captured["headers"]["Authorization"] == f"Bearer {token}"
    assert captured["data"]["developer_username"] == "alice"
    assert captured["data"]["package_name"] == "demo"
    assert captured["data"]["version"] == "1.2.3"
    assert captured["data"]["checksum"] == hashlib.sha256(package_bytes).hexdigest()
    assert len(bytes.fromhex(captured["data"]["signature"])) == 64
    assert captured["file_name"] == "demo.pkg"
    assert captured["file_content"] == package_bytes
    assert captured["file_content_type"] == "application/octet-stream"
