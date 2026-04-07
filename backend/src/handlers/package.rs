use axum::{
    body::Body,
    extract::{Extension, Path, Query},
    http::{header, HeaderValue, StatusCode},
    response::{IntoResponse, Response},
    Json,
};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct SearchPackagesQuery {
    pub q: String,
}

#[derive(Debug, Serialize)]
pub struct PackageSummary {
    pub id: Uuid,
    pub name: String,
    pub developer_id: Uuid,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
pub struct PackageVersionResponse {
    pub id: Uuid,
    pub package_id: Uuid,
    pub version: String,
    pub checksum: String,
    pub signature: String,
    pub file_path: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
pub struct PackageDetail {
    pub id: Uuid,
    pub name: String,
    pub developer_id: Uuid,
    pub description: Option<String>,
    pub developer_public_key: String,
    pub created_at: DateTime<Utc>,
    pub versions: Vec<PackageVersionResponse>,
}

pub async fn list_packages(Extension(state): Extension<Arc<AppState>>) -> impl IntoResponse {
    let result = sqlx::query!(
        r#"
        SELECT id, name, developer_id, description, created_at
        FROM packages
        ORDER BY name ASC
        "#
    )
    .fetch_all(&state.db)
    .await;

    match result {
        Ok(rows) => {
            let packages = rows
                .into_iter()
                .map(|p| PackageSummary {
                    id: p.id,
                    name: p.name,
                    developer_id: p.developer_id,
                    description: p.description,
                    created_at: p.created_at,
                })
                .collect::<Vec<_>>();

            (StatusCode::OK, Json(packages)).into_response()
        }
        Err(_) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            "Failed to fetch packages",
        )
            .into_response(),
    }
}

pub async fn search_packages(
    Extension(state): Extension<Arc<AppState>>,
    Query(params): Query<SearchPackagesQuery>,
) -> impl IntoResponse {
    let query_text = format!("%{}%", params.q.trim());

    let result = sqlx::query!(
        r#"
        SELECT id, name, developer_id, description, created_at
        FROM packages
        WHERE name ILIKE $1 OR COALESCE(description, '') ILIKE $1
        ORDER BY name ASC
        "#,
        query_text
    )
    .fetch_all(&state.db)
    .await;

    match result {
        Ok(rows) => {
            let packages = rows
                .into_iter()
                .map(|p| PackageSummary {
                    id: p.id,
                    name: p.name,
                    developer_id: p.developer_id,
                    description: p.description,
                    created_at: p.created_at,
                })
                .collect::<Vec<_>>();

            (StatusCode::OK, Json(packages)).into_response()
        }
        Err(_) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            "Failed to search packages",
        )
            .into_response(),
    }
}

pub async fn get_package(
    Extension(state): Extension<Arc<AppState>>,
    Path(name): Path<String>,
) -> impl IntoResponse {
    let package = match sqlx::query!(
        r#"
        SELECT p.id, p.name, p.developer_id, p.description, p.created_at, d.public_key as "developer_public_key!"
        FROM packages
        p
        INNER JOIN developers d ON d.id = p.developer_id
        WHERE p.name = $1
        "#,
        name
    )
    .fetch_optional(&state.db)
    .await
    {
        Ok(Some(pkg)) => pkg,
        Ok(None) => return (StatusCode::NOT_FOUND, "Package not found").into_response(),
        Err(_) => {
            return (StatusCode::INTERNAL_SERVER_ERROR, "Failed to fetch package").into_response()
        }
    };

    let versions = match sqlx::query!(
        r#"
        SELECT id, package_id, version, checksum, signature, file_path, created_at
        FROM package_versions
        WHERE package_id = $1
        ORDER BY created_at DESC
        "#,
        package.id
    )
    .fetch_all(&state.db)
    .await
    {
        Ok(rows) => rows
            .into_iter()
            .map(|v| PackageVersionResponse {
                id: v.id,
                package_id: v.package_id,
                version: v.version,
                checksum: v.checksum,
                signature: v.signature,
                file_path: v.file_path,
                created_at: v.created_at,
            })
            .collect::<Vec<_>>(),
        Err(_) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Failed to fetch versions",
            )
                .into_response()
        }
    };

    let response = PackageDetail {
        id: package.id,
        name: package.name,
        developer_id: package.developer_id,
        description: package.description,
        developer_public_key: package.developer_public_key,
        created_at: package.created_at,
        versions,
    };

    (StatusCode::OK, Json(response)).into_response()
}

pub async fn download_package(
    Extension(state): Extension<Arc<AppState>>,
    Path((name, version)): Path<(String, String)>,
) -> impl IntoResponse {
    let file = match sqlx::query!(
        r#"
        SELECT pv.file_path
        FROM package_versions pv
        INNER JOIN packages p ON p.id = pv.package_id
        WHERE p.name = $1 AND pv.version = $2
        "#,
        name,
        version
    )
    .fetch_optional(&state.db)
    .await
    {
        Ok(Some(record)) => record,
        Ok(None) => return (StatusCode::NOT_FOUND, "Package version not found").into_response(),
        Err(_) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Failed to fetch package file",
            )
                .into_response()
        }
    };

    let data = match tokio::fs::read(&file.file_path).await {
        Ok(bytes) => bytes,
        Err(_) => return (StatusCode::NOT_FOUND, "Package file not found").into_response(),
    };

    let filename = format!("{}-{}.tar.gz", name, version);
    let content_disposition = format!("attachment; filename=\"{}\"", filename);

    let mut response = Response::new(Body::from(data));
    *response.status_mut() = StatusCode::OK;
    response.headers_mut().insert(
        header::CONTENT_TYPE,
        HeaderValue::from_static("application/gzip"),
    );
    if let Ok(value) = HeaderValue::from_str(&content_disposition) {
        response
            .headers_mut()
            .insert(header::CONTENT_DISPOSITION, value);
    }

    response
}
