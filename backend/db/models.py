import uuid
from typing import Optional

from sqlalchemy import ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)


class Developer(Base):
    __tablename__ = "developers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)

    packages: Mapped[list["Package"]] = relationship(
        back_populates="developer", cascade="all, delete-orphan"
    )


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    developer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("developers.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    developer: Mapped["Developer"] = relationship(back_populates="packages")
    versions: Mapped[list["PackageVersion"]] = relationship(
        back_populates="package", cascade="all, delete-orphan"
    )


class PackageVersion(Base):
    __tablename__ = "package_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    package_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("packages.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    checksum: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    package: Mapped["Package"] = relationship(back_populates="versions")
