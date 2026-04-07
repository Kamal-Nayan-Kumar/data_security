-- Add migration script here
CREATE TABLE developers (
    id UUID PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    public_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE packages (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    developer_id UUID NOT NULL REFERENCES developers(id),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE package_versions (
    id UUID PRIMARY KEY,
    package_id UUID NOT NULL REFERENCES packages(id),
    version VARCHAR(50) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    signature TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(package_id, version)
);
