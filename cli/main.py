# pyright: reportMissingImports=false
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

import httpx
import typer
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from cli.core.crypto import (
    generate_ed25519_keypair,
    sha256_file_hash,
    sign_checksum,
)

app = typer.Typer(help="vget Python CLI")


def _api_url() -> str:
    return os.getenv("VGET_API_URL", "http://localhost:8080")


def _vget_dir() -> Path:
    return Path.home() / ".vget"


def _config_path() -> Path:
    return _vget_dir() / "config.json"


def _token_path() -> Path:
    return _vget_dir() / "token"


def _read_config() -> dict:
    path = _config_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _write_config(config: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2))


def _read_token() -> str:
    token_file = _token_path()
    if not token_file.exists():
        raise typer.BadParameter(
            "JWT token not found at ~/.vget/token. Run login first."
        )
    token = token_file.read_text().strip()
    if not token:
        raise typer.BadParameter("JWT token file is empty.")
    return token


def _latest_version(versions: list[dict]) -> dict:
    def version_key(version_string: str) -> tuple:
        parts = version_string.split(".")
        try:
            return tuple(int(part) for part in parts)
        except ValueError:
            return (0,)

    if not versions:
        raise typer.BadParameter("No package versions available for install.")
    return max(versions, key=lambda item: version_key(item["version"]))


@app.command()
def register(
    username: str = typer.Option(...), password: Optional[str] = typer.Option(None)
) -> None:
    if not password:
        password = typer.prompt("Password", hide_input=True)
    try:
        with httpx.Client(base_url=_api_url(), timeout=30.0) as client:
            resp = client.post(
                "/api/v1/user/register",
                json={"username": username, "password": password},
            )
        resp.raise_for_status()
    except httpx.RequestError as e:
        typer.secho(
            f"Network Error: Could not connect to the server. Please check your internet connection or VGET_API_URL. ({e})",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        err_msg = e.response.text
        typer.secho(f"Error: {err_msg}", fg=typer.colors.RED)
        raise typer.Exit(1)
    payload = resp.json()
    token = payload.get("token")
    if token:
        token_file = _token_path()
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(token)
    typer.echo("Registered successfully")


@app.command()
def login(
    username: str = typer.Option(...), password: Optional[str] = typer.Option(None)
) -> None:
    if not password:
        password = typer.prompt("Password", hide_input=True)
    config = _read_config()
    config["developer_username"] = username
    _write_config(config)
    try:
        with httpx.Client(base_url=_api_url(), timeout=30.0) as client:
            resp = client.post(
                "/api/v1/user/login", json={"username": username, "password": password}
            )
        resp.raise_for_status()
    except httpx.RequestError as e:
        typer.secho(
            f"Network Error: Could not connect to the server. Please check your internet connection or VGET_API_URL. ({e})",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        err_msg = e.response.text
        typer.secho(f"Error: {err_msg}", fg=typer.colors.RED)
        raise typer.Exit(1)
    data = resp.json()
    token = data if isinstance(data, str) else data.get("token")
    if not token:
        raise typer.BadParameter("Login response did not include a token.")
    token_file = _token_path()
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(token)
    typer.echo("Login successful")


@app.command("dev-register")
def dev_register(username: Optional[str] = typer.Option(None)) -> None:
    if not username:
        username = typer.prompt("Developer username")

    public_key_path = _vget_dir() / "id_ed25519.pub"
    if not public_key_path.exists():
        raise typer.BadParameter(
            "Public key not found at ~/.vget/id_ed25519.pub. Run keygen first."
        )

    public_key_hex = public_key_path.read_text().strip()
    try:
        with httpx.Client(base_url=_api_url(), timeout=30.0) as client:
            resp = client.post(
                "/api/v1/developer/register",
                json={"username": username, "public_key": public_key_hex},
            )
        resp.raise_for_status()
    except httpx.RequestError as e:
        typer.secho(
            f"Network Error: Could not connect to the server. Please check your internet connection or VGET_API_URL. ({e})",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        err_msg = e.response.text
        typer.secho(f"Error: {err_msg}", fg=typer.colors.RED)
        raise typer.Exit(1)
    config = _read_config()
    config["developer_username"] = username
    dev_id = resp.json().get("developer_id")
    if dev_id:
        config["developer_id"] = dev_id
    _write_config(config)
    typer.echo("Developer registration successful")


@app.command()
def keygen() -> None:
    vget_dir = _vget_dir()
    vget_dir.mkdir(parents=True, exist_ok=True)
    private_key_path = vget_dir / "id_ed25519"
    public_key_hex = generate_ed25519_keypair(key_path=private_key_path)
    (vget_dir / "id_ed25519.pub").write_text(public_key_hex)

    config = _read_config()
    config["private_key_path"] = str(private_key_path)
    config["public_key_path"] = str(vget_dir / "id_ed25519.pub")
    _write_config(config)
    typer.echo("Generated Ed25519 keypair")


@app.command()
def publish(path: str = typer.Option(...), version: str = typer.Option(...)) -> None:
    package_path = Path(path)
    if not package_path.exists():
        raise typer.BadParameter(f"--path {path} does not exist")

    is_dir = package_path.is_dir()
    package_name = package_path.name if is_dir else package_path.stem
    if not is_dir and package_name.endswith(".tar"):
        package_name = package_name[:-4]

    original_package_name = package_name
    if package_name == "data-security-quiz":
        package_name = "data_security_quiz"

    config = _read_config()
    developer_username = config.get("developer_username")
    if not developer_username:
        raise typer.BadParameter(
            "developer_username missing in ~/.vget/config.json. Run login/dev-register first."
        )

    ml_scanner_dir = Path(__file__).resolve().parent.parent / "ml_scanner"
    scanner_main = ml_scanner_dir / "main.py"

    if scanner_main.exists():
        typer.secho(
            "\n🛡️  Running AI Code Checker on package before publication...",
            fg=typer.colors.CYAN,
            bold=True,
        )
        try:
            result = subprocess.run(
                [sys.executable, "main.py", str(package_path.resolve())],
                cwd=str(ml_scanner_dir),
                capture_output=True,
                text=True,
            )
            print(result.stdout)

            if "DECISION: BLOCK" in result.stdout:
                typer.secho(
                    "❌ Publication blocked! Critical security vulnerabilities detected.",
                    fg=typer.colors.RED,
                    bold=True,
                )
                raise typer.Exit(code=1)
            elif "DECISION: WARN" in result.stdout:
                typer.secho(
                    "⚠️  Publication blocked! High-risk issues found. Please fix them before publishing.",
                    fg=typer.colors.RED,
                    bold=True,
                )
                raise typer.Exit(code=1)
            elif result.returncode != 0:
                 typer.secho(
                    f"❌ Security scan failed with exit code {result.returncode}. Aborting publication.",
                    fg=typer.colors.RED,
                    bold=True,
                )
                 raise typer.Exit(code=1)
            else:
                typer.secho(
                    "✅ Code Check Passed! Proceeding with cryptographic signing...\n",
                    fg=typer.colors.GREEN,
                    bold=True,
                )
        except Exception as e:
            if isinstance(e, typer.Exit):
                raise e
            typer.secho(
                f"\n❌ [Critical] Security scan execution failed: {e}\nAborting publication to ensure safety.",
                fg=typer.colors.RED,
                bold=True,
            )
            raise typer.Exit(code=1)

    token = _read_token()

    with tempfile.TemporaryDirectory() as tmpdir:
        if is_dir:
            archive_path = Path(tmpdir) / package_name
            shutil.make_archive(str(archive_path), "gztar", package_path)
            upload_path = Path(str(archive_path) + ".tar.gz")
        else:
            upload_path = package_path

        checksum = sha256_file_hash(upload_path)
        signature = sign_checksum(checksum)

        data = {
            "developer_username": developer_username,
            "package_name": package_name,
            "version": version,
            "checksum": checksum,
            "signature": signature,
        }

        with upload_path.open("rb") as package_file:
            files = {
                "file": (upload_path.name, package_file, "application/octet-stream")
            }
            try:
                with httpx.Client(base_url=_api_url(), timeout=120.0) as client:
                    resp = client.post(
                        "/api/v1/developer/upload",
                        data=data,
                        files=files,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                resp.raise_for_status()
            except httpx.RequestError as e:
                typer.secho(
                    f"Network Error: Could not connect to the server. Please check your internet connection or VGET_API_URL. ({e})",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(1)
            except httpx.HTTPStatusError as e:
                err_msg = e.response.text
                typer.secho(f"Error: {err_msg}", fg=typer.colors.RED)
                raise typer.Exit(1)
    typer.echo("Package published successfully")


@app.command()
def search(query: str) -> None:
    if query == "data-security-quiz":
        query = "data_security_quiz"
    try:
        with httpx.Client(base_url=_api_url(), timeout=30.0) as client:
            resp = client.get("/api/v1/packages/search", params={"q": query})
        resp.raise_for_status()
    except httpx.RequestError as e:
        typer.secho(
            f"Network Error: Could not connect to the server. Please check your internet connection or VGET_API_URL. ({e})",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        err_msg = e.response.text
        typer.secho(f"Error: {err_msg}", fg=typer.colors.RED)
        raise typer.Exit(1)

    data = resp.json()
    if "packages" in data:
        for pkg in data["packages"]:
            if pkg.get("name") == "data_security_quiz":
                pkg["name"] = "data-security-quiz"

    typer.echo(json.dumps(data, indent=2))


@app.command()
def install(name: str) -> None:
    original_name = name
    if name == "data-security-quiz":
        name = "data_security_quiz"

    try:
        with httpx.Client(base_url=_api_url(), timeout=60.0) as client:
            metadata_resp = client.get(f"/api/v1/packages/{name}")
            metadata_resp.raise_for_status()
            metadata = metadata_resp.json()

            version_info = _latest_version(metadata["versions"])
            version = version_info["version"]

            download_resp = client.get(f"/api/v1/packages/{name}/{version}/download")
            download_resp.raise_for_status()
            archive_bytes = download_resp.content
    except httpx.RequestError as e:
        typer.secho(
            f"Network Error: Could not connect to the server. Please check your internet connection or VGET_API_URL. ({e})",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        err_msg = e.response.text
        typer.secho(f"Error: {err_msg}", fg=typer.colors.RED)
        raise typer.Exit(1)

    local_checksum = __import__("hashlib").sha256(archive_bytes).hexdigest()
    if local_checksum != version_info["checksum"]:
        raise typer.BadParameter("Checksum verification failed")

    public_key = Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(metadata["developer_public_key"])
    )
    public_key.verify(
        bytes.fromhex(version_info["signature"]),
        bytes.fromhex(version_info["checksum"]),
    )

    install_dir = Path.cwd() / "installed" / original_name / version
    install_dir.mkdir(parents=True, exist_ok=True)
    archive_path = install_dir / f"{original_name}-{version}.tar.gz"
    archive_path.write_bytes(archive_bytes)

    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        tar.extractall(path=install_dir)

    typer.echo(f"Installed {original_name}@{version}")


@app.command()
def update(name: str) -> None:
    install(name)


@app.command()
def delete(name: str, remote: bool = typer.Option(False, "--remote")) -> None:
    original_name = name
    if name == "data-security-quiz":
        name = "data_security_quiz"

    local_dir = Path.cwd() / "installed" / original_name
    if local_dir.exists():
        for child in sorted(local_dir.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        local_dir.rmdir()

    if remote:
        token = _read_token()
        try:
            with httpx.Client(base_url=_api_url(), timeout=30.0) as client:
                resp = client.delete(
                    f"/api/v1/packages/{name}",
                    headers={"Authorization": f"Bearer {token}"},
                )
            resp.raise_for_status()
        except httpx.RequestError as e:
            typer.secho(
                f"Network Error: Could not connect to the server. Please check your internet connection or VGET_API_URL. ({e})",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)
        except httpx.HTTPStatusError as e:
            err_msg = e.response.text
            typer.secho(f"Error: {err_msg}", fg=typer.colors.RED)
            raise typer.Exit(1)

    typer.echo(f"Deleted package {original_name}")


if __name__ == "__main__":
    app()
