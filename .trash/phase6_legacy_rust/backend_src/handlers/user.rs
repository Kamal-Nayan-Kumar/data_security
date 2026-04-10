use axum::{extract::Extension, http::StatusCode, response::IntoResponse, Json};
use bcrypt::{hash, verify, DEFAULT_COST};
use chrono::{Duration, Utc};
use jsonwebtoken::{encode, EncodingKey, Header};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

use crate::AppState;

#[derive(Deserialize)]
pub struct RegisterUserReq {
    pub username: String,
    pub password: String,
}

#[derive(Deserialize)]
pub struct LoginUserReq {
    pub username: String,
    pub password: String,
}

#[derive(Serialize)]
pub struct TokenResponse {
    pub token: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub exp: usize,
}

pub async fn register_user(
    Extension(state): Extension<Arc<AppState>>,
    Json(payload): Json<RegisterUserReq>,
) -> impl IntoResponse {
    let id = Uuid::new_v4();

    let password_hash = match hash(&payload.password, DEFAULT_COST) {
        Ok(value) => value,
        Err(_) => {
            return (StatusCode::INTERNAL_SERVER_ERROR, "Failed to hash password").into_response()
        }
    };

    let result = sqlx::query!(
        r#"
        INSERT INTO users (id, username, password_hash)
        VALUES ($1, $2, $3)
        "#,
        id,
        payload.username,
        password_hash
    )
    .execute(&state.db)
    .await;

    match result {
        Ok(_) => StatusCode::CREATED.into_response(),
        Err(_) => (StatusCode::CONFLICT, "Username may already exist").into_response(),
    }
}

pub async fn login_user(
    Extension(state): Extension<Arc<AppState>>,
    Json(payload): Json<LoginUserReq>,
) -> impl IntoResponse {
    let user = match sqlx::query!(
        r#"
        SELECT id, password_hash
        FROM users
        WHERE username = $1
        "#,
        payload.username
    )
    .fetch_one(&state.db)
    .await
    {
        Ok(user) => user,
        Err(_) => {
            return (StatusCode::UNAUTHORIZED, "Invalid username or password").into_response()
        }
    };

    let is_valid = verify(&payload.password, &user.password_hash).unwrap_or(false);
    if !is_valid {
        return (StatusCode::UNAUTHORIZED, "Invalid username or password").into_response();
    }

    let exp = (Utc::now() + Duration::hours(24)).timestamp() as usize;
    let claims = Claims {
        sub: user.id.to_string(),
        exp,
    };

    let token = match encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(state.jwt_secret.as_bytes()),
    ) {
        Ok(token) => token,
        Err(_) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Failed to generate token",
            )
                .into_response()
        }
    };

    (StatusCode::OK, Json(TokenResponse { token })).into_response()
}
