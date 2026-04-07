use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Arc;

use axum::{
    extract::{Extension, Multipart},
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use serde_json::json;
use tokio::io::AsyncWriteExt;
use uuid::Uuid;

use crate::models::{
    RegisterDeveloperRequest, RegisterDeveloperResponse, UploadPackageResponse,
};
use crate::AppState;

type ApiResult<T> = Result<T, ApiError>;

#[derive(Debug)]
pub struct ApiError {
    status: StatusCode,
    message: String,
}

impl ApiError {
    fn bad_request(message: impl Into<String>) -> Self {
        Self {
            status: StatusCode::BAD_REQUEST,
            message: message.into(),
        }
    }

    fn internal(message: impl Into<String>) -> Self {
        Self {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            message: message.into(),
        }
    }

    fn not_acceptable(message: impl Into<String>) -> Self {
        Self {
            status: StatusCode::NOT_ACCEPTABLE,
            message: message.into(),
        }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (self.status, Json(json!({ "error": self.message }))).into_response()
    }
}

pub async fn register(
    Extension(state): Extension<Arc<AppState>>,
    Json(payload): Json<RegisterDeveloperRequest>,
) -> ApiResult<impl IntoResponse> {
    let username = payload.username.trim();
    let public_key = payload.public_key.trim();

    if username.is_empty() {
        return Err(ApiError::bad_request("username is required"));
    }

    let pk_bytes = hex::decode(public_key)
        .map_err(|_| ApiError::bad_request("public_key must be valid hex"))?;

    if pk_bytes.len() != 32 {
        return Err(ApiError::bad_request(
            "public_key must be a 32-byte Ed25519 key encoded as hex",
        ));
    }

    VerifyingKey::from_bytes(
        &pk_bytes
            .as_slice()
            .try_into()
            .map_err(|_| ApiError::bad_request("invalid Ed25519 public key length"))?,
    )
    .map_err(|_| ApiError::bad_request("invalid Ed25519 public key"))?;

    let developer_id = Uuid::new_v4();

    sqlx::query(
        r#"
        INSERT INTO developers (id, username, public_key)
        VALUES ($1, $2, $3)
        "#,
    )
    .bind(developer_id)
    .bind(username)
    .bind(public_key)
    .execute(&state.db)
    .await
    .map_err(|e| {
        if e.to_string().contains("duplicate key") {
            ApiError {
                status: StatusCode::CONFLICT,
                message: "username already exists".to_string(),
            }
        } else {
            ApiError::internal(format!("failed to create developer: {e}"))
        }
    })?;

    Ok((
        StatusCode::CREATED,
        Json(RegisterDeveloperResponse {
            id: developer_id,
            username: username.to_string(),
        }),
    ))
}

pub async fn upload_package(
    Extension(state): Extension<Arc<AppState>>,
    mut multipart: Multipart,
) -> ApiResult<impl IntoResponse> {
    let mut developer_username: Option<String> = None;
    let mut package_name: Option<String> = None;
    let mut version: Option<String> = None;
    let mut checksum: Option<String> = None;
    let mut signature: Option<String> = None;
    let mut description: Option<String> = None;
    let mut file_bytes: Option<Vec<u8>> = None;
    let mut file_name: Option<String> = None;

    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|e| ApiError::bad_request(format!("invalid multipart payload: {e}")))?
    {
        let name = field.name().unwrap_or_default().to_string();
        match name.as_str() {
            "developer_username" => developer_username = Some(field_text(field).await?),
            "package_name" => package_name = Some(field_text(field).await?),
            "version" => version = Some(field_text(field).await?),
            "checksum" => checksum = Some(field_text(field).await?),
            "signature" => signature = Some(field_text(field).await?),
            "description" => description = Some(field_text(field).await?),
            "file" => {
                file_name = field.file_name().map(|s| s.to_string());
                let bytes = field
                    .bytes()
                    .await
                    .map_err(|e| ApiError::bad_request(format!("failed to read file: {e}")))?;
                file_bytes = Some(bytes.to_vec());
            }
            _ => {}
        }
    }

    let developer_username = developer_username
        .ok_or_else(|| ApiError::bad_request("developer_username is required"))?;
    let package_name = package_name.ok_or_else(|| ApiError::bad_request("package_name is required"))?;
    let version = version.ok_or_else(|| ApiError::bad_request("version is required"))?;
    let checksum = checksum.ok_or_else(|| ApiError::bad_request("checksum is required"))?;
    let signature_hex = signature.ok_or_else(|| ApiError::bad_request("signature is required"))?;
    let file_bytes = file_bytes.ok_or_else(|| ApiError::bad_request("file is required"))?;

    let developer_row: (Uuid, String) = sqlx::query_as(
        "SELECT id, public_key FROM developers WHERE username = $1",
    )
    .bind(&developer_username)
    .fetch_optional(&state.db)
    .await
    .map_err(|e| ApiError::internal(format!("failed to load developer: {e}")))?
    .ok_or_else(|| ApiError {
        status: StatusCode::NOT_FOUND,
        message: "developer not found".to_string(),
    })?;

    verify_signature(&developer_row.1, &checksum, &signature_hex)?;

    if let Some(reason) = run_security_scan(&file_bytes, file_name.as_deref()).await {
        tracing::warn!(
            developer_username = %developer_username,
            package_name = %package_name,
            version = %version,
            reason = %reason,
            "package rejected by security scan"
        );
        return Err(ApiError::not_acceptable(format!(
            "package rejected by security scan: {reason}"
        )));
    }

    let package_id = match sqlx::query_as::<_, (Uuid,)>(
        "SELECT id FROM packages WHERE name = $1",
    )
    .bind(&package_name)
    .fetch_optional(&state.db)
    .await
    .map_err(|e| ApiError::internal(format!("failed to query package: {e}")))?
    {
        Some((id,)) => id,
        None => {
            let id = Uuid::new_v4();
            sqlx::query(
                "INSERT INTO packages (id, name, developer_id, description) VALUES ($1, $2, $3, $4)",
            )
            .bind(id)
            .bind(&package_name)
            .bind(developer_row.0)
            .bind(description.as_deref())
            .execute(&state.db)
            .await
            .map_err(|e| ApiError::internal(format!("failed to create package: {e}")))?;
            id
        }
    };

    let package_owner: (Uuid,) = sqlx::query_as("SELECT developer_id FROM packages WHERE id = $1")
        .bind(package_id)
        .fetch_one(&state.db)
        .await
        .map_err(|e| ApiError::internal(format!("failed to verify package owner: {e}")))?;

    if package_owner.0 != developer_row.0 {
        return Err(ApiError {
            status: StatusCode::FORBIDDEN,
            message: "package is owned by another developer".to_string(),
        });
    }

    let sanitized_name = file_name
        .as_deref()
        .and_then(|n| Path::new(n).file_name().map(|s| s.to_string_lossy().to_string()))
        .filter(|n| !n.is_empty())
        .unwrap_or_else(|| "package.bin".to_string());
    let version_id = Uuid::new_v4();
    let disk_name = format!("{version_id}-{sanitized_name}");
    let relative_path = format!("uploads/{disk_name}");

    let mut file = tokio::fs::File::create(&relative_path)
        .await
        .map_err(|e| ApiError::internal(format!("failed to create upload file: {e}")))?;
    file.write_all(&file_bytes)
        .await
        .map_err(|e| ApiError::internal(format!("failed to write upload file: {e}")))?;
    file.flush()
        .await
        .map_err(|e| ApiError::internal(format!("failed to flush upload file: {e}")))?;

    sqlx::query(
        r#"
        INSERT INTO package_versions (id, package_id, version, checksum, signature, file_path)
        VALUES ($1, $2, $3, $4, $5, $6)
        "#,
    )
    .bind(version_id)
    .bind(package_id)
    .bind(&version)
    .bind(&checksum)
    .bind(&signature_hex)
    .bind(&relative_path)
    .execute(&state.db)
    .await
    .map_err(|e| ApiError::internal(format!("failed to save package version: {e}")))?;

    Ok((
        StatusCode::CREATED,
        Json(UploadPackageResponse {
            package_id,
            version_id,
            package_name,
            version,
            file_path: relative_path,
        }),
    ))
}

async fn field_text(field: axum::extract::multipart::Field<'_>) -> ApiResult<String> {
    let text = field
        .text()
        .await
        .map_err(|e| ApiError::bad_request(format!("invalid text field: {e}")))?;
    Ok(text.trim().to_string())
}

fn verify_signature(public_key_hex: &str, checksum: &str, signature_hex: &str) -> ApiResult<()> {
    let public_key_bytes = hex::decode(public_key_hex.trim())
        .map_err(|_| ApiError::bad_request("stored public key is not valid hex"))?;
    let public_key: [u8; 32] = public_key_bytes
        .as_slice()
        .try_into()
        .map_err(|_| ApiError::bad_request("stored public key length is invalid"))?;

    let verify_key = VerifyingKey::from_bytes(&public_key)
        .map_err(|_| ApiError::bad_request("stored public key is invalid"))?;

    let signature_bytes = hex::decode(signature_hex.trim())
        .map_err(|_| ApiError::bad_request("signature must be valid hex"))?;
    let signature: [u8; 64] = signature_bytes
        .as_slice()
        .try_into()
        .map_err(|_| ApiError::bad_request("signature must be 64 bytes (hex-encoded)"))?;

    let signature = Signature::from_bytes(&signature);
    let checksum_bytes = hex::decode(checksum.trim())
        .map_err(|_| ApiError::bad_request("checksum must be valid hex"))?;
    if checksum_bytes.len() != 32 {
        return Err(ApiError::bad_request(
            "checksum must be 32 bytes (hex-encoded)",
        ));
    }

    verify_key
        .verify(&checksum_bytes, &signature)
        .map_err(|_| ApiError::bad_request("signature verification failed"))
}

async fn run_security_scan(file_bytes: &[u8], file_name: Option<&str>) -> Option<String> {
    match run_teammate_scanner(file_bytes, file_name).await {
        Ok(Some(reason)) => return Some(reason),
        Ok(None) => return None,
        Err(err) => {
            tracing::warn!(error = %err, "teammate security scanner unavailable, using fallback");
        }
    }

    detect_static_malware_signature(file_bytes)
}

async fn run_teammate_scanner(
    file_bytes: &[u8],
    file_name: Option<&str>,
) -> Result<Option<String>, String> {
    let script_path = find_teammate_scanner()
        .ok_or_else(|| "teammate scanner script not found".to_string())?;

    let temp_dir = std::env::temp_dir().join(format!("vget-scan-{}", Uuid::new_v4()));
    tokio::fs::create_dir_all(&temp_dir)
        .await
        .map_err(|e| format!("failed to create temp scan dir: {e}"))?;

    let temp_file_name = file_name
        .and_then(|n| Path::new(n).file_name().map(|s| s.to_string_lossy().to_string()))
        .filter(|n| !n.is_empty())
        .unwrap_or_else(|| "uploaded-package.bin".to_string());
    let temp_file_path = temp_dir.join(temp_file_name);

    tokio::fs::write(&temp_file_path, file_bytes)
        .await
        .map_err(|e| format!("failed to write temp package for scan: {e}"))?;

    let output = tokio::task::spawn_blocking({
        let script_path = script_path.clone();
        let temp_dir = temp_dir.clone();
        move || {
            let try_python3 = Command::new("python3")
                .arg(&script_path)
                .arg(&temp_dir)
                .arg("--json")
                .output();

            match try_python3 {
                Ok(output) => Ok(output),
                Err(_) => Command::new("python")
                    .arg(&script_path)
                    .arg(&temp_dir)
                    .arg("--json")
                    .output()
                    .map_err(|e| format!("failed to execute scanner with python/python3: {e}")),
            }
        }
    })
    .await
    .map_err(|e| format!("scanner thread join error: {e}"))??;

    let _ = tokio::fs::remove_dir_all(&temp_dir).await;

    if !output.status.success() {
        return Err(format!(
            "scanner exited with status {}: {}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        ));
    }

    let report: serde_json::Value = serde_json::from_slice(&output.stdout)
        .map_err(|e| format!("failed to parse scanner JSON output: {e}"))?;

    let decision = report
        .get("decision")
        .and_then(|v| v.as_str())
        .unwrap_or_default()
        .to_ascii_uppercase();
    if decision == "BLOCK" {
        let risk_score = report
            .get("risk_score")
            .and_then(|v| v.as_f64())
            .map(|v| format!("{v:.1}"))
            .unwrap_or_else(|| "unknown".to_string());

        return Ok(Some(format!(
            "teammate scanner decision BLOCK (risk score: {risk_score})"
        )));
    }

    Ok(None)
}

fn find_teammate_scanner() -> Option<PathBuf> {
    let candidates = [
        PathBuf::from("ml_scanner/main.py"),
        PathBuf::from("../ml_scanner/main.py"),
    ];

    candidates.into_iter().find(|p| p.exists())
}

fn detect_static_malware_signature(file_bytes: &[u8]) -> Option<String> {
    let text = String::from_utf8_lossy(file_bytes).to_ascii_lowercase();
    let suspicious_patterns = [
        "os.system",
        "exec(",
        "nc -e",
        "subprocess.popen",
        "powershell -enc",
        "curl http://",
    ];

    suspicious_patterns
        .iter()
        .find(|pattern| text.contains(**pattern))
        .map(|pattern| format!("fallback static scanner matched suspicious signature: {pattern}"))
}
