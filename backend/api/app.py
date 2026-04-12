from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated, Optional
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core import security
from backend.db.database import AsyncSessionLocal
from backend.db.models import Developer, Package, PackageVersion, User


def _default_uploads_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "uploads"


def create_app(
    *, session_factory=AsyncSessionLocal, uploads_dir: Optional[Path] = None
) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.uploads_dir.mkdir(parents=True, exist_ok=True)
        yield

    app = FastAPI(title="vget-python-backend", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.session_factory = session_factory
    app.state.uploads_dir = uploads_dir or _default_uploads_dir()

    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with app.state.session_factory() as session:
            yield session

    async def get_current_user(
        authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    ) -> dict:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        parts = authorization.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid Authorization header")

        token = parts[1].strip()
        if not token:
            raise HTTPException(status_code=401, detail="Missing bearer token")

        try:
            return security.decode_jwt(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

    class RegisterDeveloperRequest(BaseModel):
        username: str
        public_key: str

    class RegisterUserRequest(BaseModel):
        username: str
        password: str

    class LoginUserRequest(BaseModel):
        username: str
        password: str

    @app.get("/health")
    async def health() -> str:
        return "OK"

    @app.post("/api/v1/developer/register", status_code=201)
    async def register_developer(
        payload: RegisterDeveloperRequest,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> dict:
        username = payload.username.strip()
        public_key = payload.public_key.strip()
        if not username:
            raise HTTPException(status_code=400, detail="username is required")
        if not public_key:
            raise HTTPException(status_code=400, detail="public_key is required")
        try:
            public_key_bytes = bytes.fromhex(public_key)
        except ValueError:
            raise HTTPException(status_code=400, detail="public_key must be valid hex")
        if len(public_key_bytes) != 32:
            raise HTTPException(
                status_code=400,
                detail="public_key must be a 32-byte Ed25519 key encoded as hex",
            )

        existing = await db.scalar(
            select(Developer).where(Developer.username == username)
        )
        if existing is not None:
            raise HTTPException(status_code=409, detail="username already exists")

        developer = Developer(username=username, public_key=public_key)
        db.add(developer)
        await db.commit()
        await db.refresh(developer)
        return {"id": str(developer.id), "username": developer.username}

    @app.post("/api/v1/user/register", status_code=201)
    async def register_user(
        payload: RegisterUserRequest,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> dict:
        username = payload.username.strip()
        password = payload.password
        if not username:
            raise HTTPException(status_code=400, detail="username is required")
        if not password:
            raise HTTPException(status_code=400, detail="password is required")

        existing = await db.scalar(select(User).where(User.username == username))
        if existing is not None:
            raise HTTPException(status_code=409, detail="Username may already exist")

        user = User(username=username, password_hash=security.hash_password(password))
        db.add(user)
        await db.commit()
        return {"status": "created"}

    @app.post("/api/v1/user/login")
    async def login_user(
        payload: LoginUserRequest,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> str:
        user = await db.scalar(
            select(User).where(User.username == payload.username.strip())
        )
        if user is None or not security.verify_password(
            payload.password, user.password_hash
        ):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        token = security.encode_jwt({"sub": str(user.id), "username": user.username})
        return token

    @app.get("/api/v1/packages")
    async def list_packages(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
        stmt = (
            select(Package)
            .options(selectinload(Package.developer), selectinload(Package.versions))
            .order_by(Package.name.asc())
        )
        rows = await db.scalars(stmt)
        return {
            "packages": [
                {
                    "id": str(pkg.id),
                    "name": pkg.name,
                    "developer": pkg.developer.username if pkg.developer else "",
                    "description": pkg.description,
                    "version": pkg.versions[-1].version if pkg.versions else "1.0.0",
                }
                for pkg in rows.all()
            ]
        }

    @app.get("/api/v1/packages/search")
    async def search_packages(
        q: str,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> dict:
        query = q.strip()
        stmt = (
            select(Package)
            .options(selectinload(Package.developer), selectinload(Package.versions))
            .order_by(Package.name.asc())
        )
        if query:
            like_expr = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Package.name.ilike(like_expr),
                    Package.description.ilike(like_expr),
                )
            )
        rows = await db.scalars(stmt)
        return {
            "packages": [
                {
                    "id": str(pkg.id),
                    "name": pkg.name,
                    "developer": pkg.developer.username if pkg.developer else "",
                    "description": pkg.description,
                    "version": pkg.versions[-1].version if pkg.versions else "1.0.0",
                }
                for pkg in rows.all()
            ]
        }

    @app.delete("/api/v1/packages/{name}")
    async def delete_package(
        name: str,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> dict:
        pkg = await db.scalar(select(Package).where(Package.name == name))
        if not pkg:
            raise HTTPException(status_code=404, detail="package not found")
        await db.delete(pkg)
        await db.commit()
        return {"detail": "package deleted"}

    @app.get("/api/v1/packages/{name}")
    async def get_package(
        name: str,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> dict:
        pkg = await db.scalar(
            select(Package)
            .where(Package.name == name)
            .options(
                selectinload(Package.developer),
                selectinload(Package.versions),
            )
        )
        if pkg is None:
            raise HTTPException(status_code=404, detail="Package not found")
        versions = sorted(pkg.versions, key=lambda item: item.version, reverse=True)
        return {
            "id": str(pkg.id),
            "name": pkg.name,
            "developer_id": str(pkg.developer_id),
            "description": pkg.description,
            "developer_public_key": pkg.developer.public_key,
            "versions": [
                {
                    "id": str(version.id),
                    "package_id": str(version.package_id),
                    "version": version.version,
                    "checksum": version.checksum,
                    "signature": version.signature,
                    "file_path": version.file_path,
                }
                for version in versions
            ],
        }

    @app.get("/api/v1/packages/{name}/{version}/download")
    async def download_package(
        name: str,
        version: str,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> Response:
        stmt = (
            select(PackageVersion)
            .join(Package, Package.id == PackageVersion.package_id)
            .where(Package.name == name, PackageVersion.version == version)
        )
        pkg_version = await db.scalar(stmt)
        if pkg_version is None:
            raise HTTPException(status_code=404, detail="Package version not found")

        if pkg_version.file_data is not None:
            return Response(
                content=pkg_version.file_data,
                media_type="application/octet-stream",
            )

        if pkg_version.file_path:
            file_path = Path(pkg_version.file_path)
            if file_path.exists():
                return Response(
                    content=file_path.read_bytes(),
                    media_type="application/octet-stream",
                )

        raise HTTPException(status_code=404, detail="Package file not found")

    @app.post("/api/v1/developer/upload", status_code=201)
    async def upload_package(
        _: Annotated[dict, Depends(get_current_user)],
        file: UploadFile = File(...),
        developer_username: str = Form(...),
        package_name: str = Form(...),
        version: str = Form(...),
        checksum: str = Form(...),
        signature: str = Form(...),
        description: Optional[str] = Form(None),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        developer_username = developer_username.strip()
        package_name = package_name.strip()
        version = version.strip()
        checksum = checksum.strip()
        signature = signature.strip()

        if not developer_username:
            raise HTTPException(
                status_code=400, detail="developer_username is required"
            )
        if not package_name:
            raise HTTPException(status_code=400, detail="package_name is required")
        if not version:
            raise HTTPException(status_code=400, detail="version is required")
        if not checksum:
            raise HTTPException(status_code=400, detail="checksum is required")
        if not signature:
            raise HTTPException(status_code=400, detail="signature is required")

        developer = await db.scalar(
            select(Developer).where(Developer.username == developer_username)
        )
        if developer is None:
            raise HTTPException(status_code=404, detail="developer not found")

        if not security.verify_ed25519_signature(
            developer.public_key, signature, checksum
        ):
            raise HTTPException(status_code=400, detail="signature verification failed")

        package = await db.scalar(select(Package).where(Package.name == package_name))
        if package is None:
            package = Package(
                name=package_name,
                developer_id=developer.id,
                description=(description.strip() if description else None),
            )
            db.add(package)
            await db.flush()
        elif package.developer_id != developer.id:
            raise HTTPException(
                status_code=403,
                detail="package is owned by another developer",
            )
        elif description is not None:
            package.description = description.strip() or None

        existing_version = await db.scalar(
            select(PackageVersion).where(
                PackageVersion.package_id == package.id,
                PackageVersion.version == version,
            )
        )
        if existing_version is not None:
            raise HTTPException(
                status_code=409, detail="package version already exists"
            )

        upload_bytes = await file.read()

        pkg_version = PackageVersion(
            package_id=package.id,
            version=version,
            checksum=checksum,
            signature=signature,
            file_path=None,
            file_data=upload_bytes,
        )
        db.add(pkg_version)
        await db.commit()
        await db.refresh(pkg_version)

        return {
            "package_id": str(package.id),
            "version_id": str(pkg_version.id),
            "package_name": package.name,
            "version": pkg_version.version,
            "file_path": pkg_version.file_path,
        }

    return app


app = create_app()
