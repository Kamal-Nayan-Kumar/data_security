import hashlib
import importlib
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

create_app = importlib.import_module("backend.api.app").create_app
security = importlib.import_module("backend.core.security")
Base = importlib.import_module("backend.db.models").Base
from cli.core.crypto import generate_ed25519_keypair, sign_checksum


@pytest.fixture
def api_client(tmp_path):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def init_models() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio

    asyncio.run(init_models())

    uploads_dir = tmp_path / "uploads"
    app = create_app(session_factory=session_factory, uploads_dir=uploads_dir)

    with TestClient(app) as client:
        yield client

    asyncio.run(engine.dispose())


def test_health(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == "OK"


def test_user_register_and_login_returns_token_string(api_client):
    register_response = api_client.post(
        "/api/v1/user/register",
        json={"username": "alice", "password": "s3cur3-password"},
    )
    assert register_response.status_code == 201

    login_response = api_client.post(
        "/api/v1/user/login",
        json={"username": "alice", "password": "s3cur3-password"},
    )
    assert login_response.status_code == 200
    token = login_response.json()
    assert isinstance(token, str)
    decoded = security.decode_jwt(token)
    assert decoded["username"] == "alice"


def test_developer_register_and_package_routes(api_client):
    public_key_hex = generate_ed25519_keypair()
    register_dev = api_client.post(
        "/api/v1/developer/register",
        json={"username": "dev-alice", "public_key": public_key_hex},
    )
    assert register_dev.status_code == 201

    list_response = api_client.get("/api/v1/packages")
    assert list_response.status_code == 200
    assert list_response.json() == {"packages": []}

    search_response = api_client.get("/api/v1/packages/search", params={"q": "demo"})
    assert search_response.status_code == 200
    assert search_response.json() == {"packages": []}

    details_response = api_client.get("/api/v1/packages/nonexistent")
    assert details_response.status_code == 404


def test_developer_upload_requires_auth(api_client, tmp_path):
    key_path = tmp_path / "id_ed25519"
    public_key_hex = generate_ed25519_keypair(key_path=key_path)

    register_dev = api_client.post(
        "/api/v1/developer/register",
        json={"username": "dev-auth", "public_key": public_key_hex},
    )
    assert register_dev.status_code == 201

    content = b"package-bytes"
    checksum = hashlib.sha256(content).hexdigest()
    signature = sign_checksum(checksum, key_path=key_path)
    files = {"file": ("sample.tar.gz", io.BytesIO(content), "application/gzip")}
    data = {
        "developer_username": "dev-auth",
        "package_name": "secure-pkg",
        "version": "1.0.0",
        "checksum": checksum,
        "signature": signature,
        "description": "first release",
    }

    upload_response = api_client.post(
        "/api/v1/developer/upload", data=data, files=files
    )
    assert upload_response.status_code == 401


def test_developer_upload_and_download(api_client, tmp_path):
    key_path = tmp_path / "id_ed25519"
    public_key_hex = generate_ed25519_keypair(key_path=key_path)

    register_dev = api_client.post(
        "/api/v1/developer/register",
        json={"username": "dev-publish", "public_key": public_key_hex},
    )
    assert register_dev.status_code == 201

    register_user = api_client.post(
        "/api/v1/user/register",
        json={"username": "publisher", "password": "pub-pass"},
    )
    assert register_user.status_code == 201

    login_response = api_client.post(
        "/api/v1/user/login",
        json={"username": "publisher", "password": "pub-pass"},
    )
    assert login_response.status_code == 200
    token = login_response.json()

    content = b"secure-package-v1"
    checksum = hashlib.sha256(content).hexdigest()
    signature = sign_checksum(checksum, key_path=key_path)

    upload_response = api_client.post(
        "/api/v1/developer/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "developer_username": "dev-publish",
            "package_name": "secure-pkg",
            "version": "1.0.0",
            "checksum": checksum,
            "signature": signature,
            "description": "secure package",
        },
        files={
            "file": (
                "secure-pkg-1.0.0.tar.gz",
                io.BytesIO(content),
                "application/gzip",
            )
        },
    )
    assert upload_response.status_code == 201
    payload = upload_response.json()
    assert payload["package_name"] == "secure-pkg"
    assert payload["version"] == "1.0.0"

    list_response = api_client.get("/api/v1/packages")
    assert list_response.status_code == 200
    packages = list_response.json()["packages"]
    assert len(packages) == 1
    assert packages[0]["name"] == "secure-pkg"

    search_response = api_client.get("/api/v1/packages/search", params={"q": "secure"})
    assert search_response.status_code == 200
    assert len(search_response.json()["packages"]) == 1

    details_response = api_client.get("/api/v1/packages/secure-pkg")
    assert details_response.status_code == 200
    details = details_response.json()
    assert details["name"] == "secure-pkg"
    assert len(details["versions"]) == 1
    assert details["versions"][0]["version"] == "1.0.0"

    download_response = api_client.get("/api/v1/packages/secure-pkg/1.0.0/download")
    assert download_response.status_code == 200
    assert download_response.content == content


def test_developer_upload_rejects_invalid_signature(api_client, tmp_path):
    key_path = tmp_path / "id_ed25519"
    public_key_hex = generate_ed25519_keypair(key_path=key_path)

    register_dev = api_client.post(
        "/api/v1/developer/register",
        json={"username": "dev-invalid-sig", "public_key": public_key_hex},
    )
    assert register_dev.status_code == 201

    register_user = api_client.post(
        "/api/v1/user/register",
        json={"username": "uploader", "password": "pass"},
    )
    assert register_user.status_code == 201

    login = api_client.post(
        "/api/v1/user/login",
        json={"username": "uploader", "password": "pass"},
    )
    token = login.json()

    content = b"secure-package"
    checksum = hashlib.sha256(content).hexdigest()
    bad_signature = "00" * 64

    upload_response = api_client.post(
        "/api/v1/developer/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "developer_username": "dev-invalid-sig",
            "package_name": "bad-sig-pkg",
            "version": "1.0.0",
            "checksum": checksum,
            "signature": bad_signature,
            "description": "bad signature",
        },
        files={
            "file": (
                "bad-sig-pkg-1.0.0.tar.gz",
                io.BytesIO(content),
                "application/gzip",
            )
        },
    )
    assert upload_response.status_code == 400
    assert upload_response.json()["detail"] == "signature verification failed"
