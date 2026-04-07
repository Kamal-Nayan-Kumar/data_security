use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize)]
pub struct Developer {
    pub id: Uuid,
    pub username: String,
    pub public_key: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Package {
    pub id: Uuid,
    pub name: String,
    pub developer_id: Uuid,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PackageVersion {
    pub id: Uuid,
    pub package_id: Uuid,
    pub version: String,
    pub checksum: String,
    pub signature: String,
    pub file_path: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct RegisterDeveloperRequest {
    pub username: String,
    pub public_key: String,
}

#[derive(Debug, Serialize)]
pub struct RegisterDeveloperResponse {
    pub id: Uuid,
    pub username: String,
}

#[derive(Debug, Serialize)]
pub struct UploadPackageResponse {
    pub package_id: Uuid,
    pub version_id: Uuid,
    pub package_name: String,
    pub version: String,
    pub file_path: String,
}
