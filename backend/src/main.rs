pub mod handlers;
pub mod models;

use axum::{
    extract::DefaultBodyLimit,
    routing::{get, post},
    Extension, Router,
};
use sqlx::postgres::PgPoolOptions;
use std::sync::Arc;
use tokio::net::TcpListener;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[derive(Clone)]
pub struct AppState {
    pub db: sqlx::PgPool,
    pub jwt_secret: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    dotenvy::dotenv().ok();

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info,backend=debug".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let db_url = std::env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let jwt_secret = std::env::var("JWT_SECRET").expect("JWT_SECRET must be set");

    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&db_url)
        .await?;

    tracing::info!("Connected to database");

    tracing::info!("Running database migrations...");
    sqlx::migrate!("./migrations").run(&pool).await?;
    tracing::info!("Migrations complete!");

    tokio::fs::create_dir_all("uploads").await?;

    let state = Arc::new(AppState {
        db: pool,
        jwt_secret,
    });

    let app = Router::new()
        .route("/health", get(health_check))
        .route(
            "/api/v1/developer/register",
            post(handlers::developer::register),
        )
        .route(
            "/api/v1/developer/upload",
            post(handlers::developer::upload_package),
        )
        .route("/api/v1/user/register", post(handlers::user::register_user))
        .route("/api/v1/user/login", post(handlers::user::login_user))
        .route("/api/v1/packages", get(handlers::package::list_packages))
        .route(
            "/api/v1/packages/search",
            get(handlers::package::search_packages),
        )
        .route(
            "/api/v1/packages/:name",
            get(handlers::package::get_package),
        )
        .route(
            "/api/v1/packages/:name/:version/download",
            get(handlers::package::download_package),
        )
        .layer(DefaultBodyLimit::max(50 * 1024 * 1024))
        .layer(Extension(state));

    let listener = TcpListener::bind("0.0.0.0:8080").await?;
    tracing::info!("Server listening on {}", listener.local_addr()?);
    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check() -> &'static str {
    "OK"
}
