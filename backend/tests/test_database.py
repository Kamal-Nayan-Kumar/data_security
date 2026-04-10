import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from backend.db.models import Base, Developer, Package, PackageVersion, User


@pytest.mark.asyncio
async def test_database_models_insert_and_select():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        user = User(username="alice", password_hash="hashed-password")
        developer = Developer(username="dev-alice", public_key="ed25519-public-key")
        package = Package(
            name="sample-pkg", developer=developer, description="demo package"
        )
        package_version = PackageVersion(
            package=package,
            version="1.0.0",
            checksum="abc123",
            signature="sig456",
            file_path="/tmp/sample-pkg-1.0.0.tar.gz",
        )

        session.add_all([user, developer, package, package_version])
        await session.commit()

    async with session_factory() as session:
        result = await session.execute(
            select(PackageVersion)
            .options(
                selectinload(PackageVersion.package).selectinload(Package.developer)
            )
            .where(PackageVersion.version == "1.0.0")
        )
        stored_version = result.scalar_one()

        assert stored_version.checksum == "abc123"
        assert stored_version.package.name == "sample-pkg"
        assert stored_version.package.developer.username == "dev-alice"

    await engine.dispose()
