use clap::{Parser, Subcommand};
use dialoguer::Password;
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use flate2::read::GzDecoder;
use flate2::write::GzEncoder;
use flate2::Compression;
use rand::rngs::OsRng;
use reqwest::multipart;
use reqwest::StatusCode;
use semver::Version;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::env;
use std::fs;
use std::io::{self, Cursor, Write};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use tar::Archive;
use tar::Builder;

const BASE_URL: &str = "http://localhost:8080";

#[derive(Debug, Deserialize)]
struct DevRegisterResponse {
    developer_id: Option<String>,
    id: Option<String>,
    uuid: Option<String>,
}

#[derive(Debug, Serialize)]
struct DevRegisterRequest {
    username: String,
    public_key: String,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct CliConfig {
    developer_id: Option<String>,
    developer_username: Option<String>,
    private_key_path: Option<String>,
    public_key_path: Option<String>,
}

#[derive(Debug, Serialize)]
struct LoginUserReq {
    username: String,
    password: String,
}

#[derive(Debug, Deserialize)]
struct PackageSummary {
    id: String,
    name: String,
    developer_id: String,
    description: Option<String>,
    created_at: String,
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct PackageVersionResponse {
    id: String,
    package_id: String,
    version: String,
    checksum: String,
    signature: String,
    file_path: String,
    created_at: String,
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct PackageDetail {
    id: String,
    name: String,
    developer_id: String,
    description: Option<String>,
    developer_public_key: String,
    created_at: String,
    versions: Vec<PackageVersionResponse>,
}

#[derive(Parser, Debug)]
#[command(name = "vget")]
#[command(about = "CLI for the data security package ecosystem")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    #[command(about = "User login")]
    Login {
        #[arg(long, help = "Username")]
        username: String,
        #[arg(long, help = "Password (optional; if omitted, prompt securely)")]
        password: Option<String>,
    },

    #[command(about = "User register")]
    Register {
        #[arg(long, help = "Username")]
        username: String,
        #[arg(long, help = "Password (optional; if omitted, prompt securely)")]
        password: Option<String>,
    },

    #[command(name = "dev-register", about = "Developer registration")]
    DevRegister {
        #[arg(long, help = "Developer username")]
        username: Option<String>,
    },

    #[command(about = "Generate Ed25519 keys for developers")]
    Keygen,

    #[command(about = "Developer pushes package")]
    Publish {
        #[arg(long, help = "Path to package directory or file")]
        path: String,
        #[arg(long, help = "Version to publish")]
        version: String,
    },

    #[command(about = "Search for packages")]
    Search {
        #[arg(help = "Search query")]
        query: String,
    },

    #[command(about = "Install a package")]
    Install {
        #[arg(help = "Package name")]
        name: String,
    },

    #[command(about = "Update a package")]
    Update {
        #[arg(help = "Package name")]
        name: String,
    },

    #[command(about = "Delete a package")]
    Delete {
        #[arg(help = "Package name")]
        name: String,
        #[arg(long, help = "Also delete from remote backend")]
        remote: bool,
    },
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Login { username, password } => handle_login(username, password).await,
        Commands::Register { username, password } => handle_register(username, password).await,
        Commands::DevRegister { username } => handle_dev_register(username).await,
        Commands::Keygen => handle_keygen().await,
        Commands::Publish { path, version } => handle_publish(path, version).await,
        Commands::Search { query } => handle_search(query).await,
        Commands::Install { name } => handle_install(name).await,
        Commands::Update { name } => handle_update(name).await,
        Commands::Delete { name, remote } => handle_delete(name, remote).await,
    }
}

async fn handle_register(username: String, password_flag: Option<String>) {
    let password = match password_flag {
        Some(value) => value,
        None => match Password::new()
            .with_prompt("Password")
            .allow_empty_password(false)
            .interact()
        {
            Ok(value) => value,
            Err(err) => {
                eprintln!("Failed to read password: {}", err);
                return;
            }
        },
    };

    let client = reqwest::Client::new();
    let resp = match client
        .post(format!("{BASE_URL}/api/v1/user/register"))
        .json(&LoginUserReq { username, password })
        .send()
        .await
    {
        Ok(r) => r,
        Err(err) => {
            eprintln!("Register request failed: {}", err);
            return;
        }
    };

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        eprintln!("Registration failed ({}): {}", status, body);
        return;
    }

    let body = resp.text().await.unwrap_or_default();
    if let Some(token) = extract_jwt_from_body(&body) {
        if let Err(err) = save_jwt(&token) {
            eprintln!("Registration succeeded but failed to save JWT: {}", err);
            return;
        }
        println!("Registration successful. JWT saved locally.");
    } else {
        println!("Registration successful. You can now login using `vget login`");
    }
}

async fn handle_login(username: String, password_flag: Option<String>) {
    let password = match password_flag {
        Some(value) => value,
        None => match Password::new()
            .with_prompt("Password")
            .allow_empty_password(false)
            .interact()
        {
            Ok(value) => value,
            Err(err) => {
                eprintln!("Failed to read password: {}", err);
                return;
            }
        },
    };

    let client = reqwest::Client::new();
    let resp = match client
        .post(format!("{BASE_URL}/api/v1/user/login"))
        .json(&LoginUserReq {
            username: username.clone(),
            password,
        })
        .send()
        .await
    {
        Ok(r) => r,
        Err(err) => {
            eprintln!("Login request failed: {}", err);
            return;
        }
    };

    let mut config = load_config();
    config.developer_username = Some(username.clone());
    if let Err(err) = save_config(&config) {
        eprintln!("Login succeeded but failed to save config: {}", err);
        return;
    }

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        eprintln!("Login failed ({}): {}", status, body);
        return;
    }

    let body = resp.text().await.unwrap_or_default();
    match extract_jwt_from_body(&body) {
        Some(token) => match save_jwt(&token) {
            Ok(path) => println!("Login successful. JWT saved to {}", path.display()),
            Err(err) => eprintln!("Login succeeded but failed to save JWT: {}", err),
        },
        None => println!("Login successful (no JWT field returned by backend)."),
    }
}

async fn handle_dev_register(username_flag: Option<String>) {
    let mut config = load_config();
    let (_, default_public_key_path) = default_dev_key_paths();
    let public_key_path = config
        .public_key_path
        .as_deref()
        .map(PathBuf::from)
        .unwrap_or(default_public_key_path);
    let public_key = match fs::read_to_string(&public_key_path) {
        Ok(value) => value.trim().to_string(),
        Err(err) => {
            eprintln!(
                "Failed to read public key {}: {}. Run `keygen` first.",
                public_key_path.display(),
                err
            );
            return;
        }
    };

    if public_key.is_empty() {
        eprintln!("Public key file is empty: {}", public_key_path.display());
        return;
    }

    let username = match username_flag {
        Some(value) => value,
        None => {
            print!("Enter username: ");
            if let Err(err) = io::stdout().flush() {
                eprintln!("Failed to flush stdout: {}", err);
                return;
            }
            let mut input = String::new();
            if let Err(err) = io::stdin().read_line(&mut input) {
                eprintln!("Failed to read username: {}", err);
                return;
            }
            let trimmed = input.trim().to_string();
            if trimmed.is_empty() {
                eprintln!("Username cannot be empty");
                return;
            }
            trimmed
        }
    };

    let client = reqwest::Client::new();
    let resp = match client
        .post(format!("{BASE_URL}/api/v1/developer/register"))
        .json(&DevRegisterRequest {
            username: username.clone(),
            public_key,
        })
        .send()
        .await
    {
        Ok(r) => r,
        Err(err) => {
            eprintln!("Failed to call developer register endpoint: {}", err);
            return;
        }
    };

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        eprintln!("Developer registration failed ({}): {}", status, body);
        return;
    }

    let body: DevRegisterResponse = match resp.json().await {
        Ok(data) => data,
        Err(err) => {
            eprintln!("Failed to parse registration response: {}", err);
            return;
        }
    };

    let developer_id = body
        .developer_id
        .or(body.id)
        .or(body.uuid)
        .unwrap_or_default();

    if developer_id.is_empty() {
        eprintln!("Registration succeeded but no developer ID was returned.");
        return;
    }

    config.developer_id = Some(developer_id.clone());
    config.developer_username = Some(username.clone());
    if config.public_key_path.is_none() {
        config.public_key_path = Some(public_key_path.to_string_lossy().to_string());
    }

    if let Err(err) = save_config(&config) {
        eprintln!("Failed to save config: {}", err);
        return;
    }

    println!("Developer registered successfully. ID: {}", developer_id);
}

async fn handle_keygen() {
    let mut config = load_config();
    let (private_path, public_path) = default_dev_key_paths();
    let key_dir = private_path
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(vget_dir);

    if let Err(err) = fs::create_dir_all(&key_dir) {
        eprintln!("Failed to create key directory {}: {}", key_dir.display(), err);
        return;
    }

    let mut rng = OsRng;
    let signing_key = SigningKey::generate(&mut rng);
    let verifying_key = signing_key.verifying_key();

    let private_hex = hex::encode(signing_key.to_bytes());
    let public_hex = hex::encode(verifying_key.to_bytes());

    if let Err(err) = fs::write(&private_path, format!("{}\n", private_hex)) {
        eprintln!("Failed to write private key {}: {}", private_path.display(), err);
        return;
    }

    if let Err(err) = fs::write(&public_path, format!("{}\n", public_hex)) {
        eprintln!("Failed to write public key {}: {}", public_path.display(), err);
        return;
    }

    config.private_key_path = Some(private_path.to_string_lossy().to_string());
    config.public_key_path = Some(public_path.to_string_lossy().to_string());
    if let Err(err) = save_config(&config) {
        eprintln!("Failed to save config: {}", err);
        return;
    }

    println!("Generated keypair:");
    println!("  {}", private_path.display());
    println!("  {}", public_path.display());
    println!("Public key: {}", public_hex);
}

async fn handle_publish(path: String, version: String) {
    let config = load_config();
    let developer_username = match config.developer_username {
        Some(value) if !value.trim().is_empty() => value,
        _ => {
            eprintln!(
                "Developer username is not configured. Run `vget dev-register --username <name>` or `vget login --username <name>` first."
            );
            return;
        }
    };

    let (private_key_path, _) = default_dev_key_paths();

    let signing_key = match read_signing_key(&private_key_path) {
        Ok(key) => key,
        Err(err) => {
            eprintln!(
                "Failed to read signing key at {}: {}. Run `vget keygen` first.",
                private_key_path.display(),
                err
            );
            return;
        }
    };

    let jwt = match read_jwt_token() {
        Ok(value) => value,
        Err(err) => {
            eprintln!("{}", err);
            return;
        }
    };

    let source_path = PathBuf::from(&path);
    if !source_path.exists() {
        eprintln!("--path does not exist: {}", source_path.display());
        return;
    }

    let package_name = extract_package_name(&source_path);
    if package_name.is_empty() {
        eprintln!("Could not infer package_name from --path.");
        return;
    }

    let archive_path = temp_archive_path(&package_name, &version);
    if let Err(err) = create_tar_gz(&source_path, &archive_path) {
        eprintln!("Failed to create archive: {}", err);
        remove_if_exists(&archive_path);
        return;
    }
    let archive = TempArchive::new(archive_path);

    let file_bytes = match fs::read(archive.path()) {
        Ok(bytes) => bytes,
        Err(err) => {
            eprintln!(
                "Failed to read package file {}: {}",
                archive.path().display(),
                err
            );
            return;
        }
    };

    let checksum: [u8; 32] = Sha256::digest(&file_bytes).into();
    let checksum_hex = hex::encode(checksum);
    let signature = signing_key.sign(&checksum);
    let signature_hex = hex::encode(signature.to_bytes());
    let archive_name = format!("{}-{}.tar.gz", package_name, version);

    let part = match multipart::Part::bytes(file_bytes)
        .file_name(archive_name)
        .mime_str("application/gzip")
    {
        Ok(p) => p,
        Err(err) => {
            eprintln!("Failed to build multipart file part: {}", err);
            return;
        }
    };

    let form = multipart::Form::new()
        .text("developer_username", developer_username)
        .text("package_name", package_name)
        .text("version", version)
        .text("checksum", checksum_hex.clone())
        .text("signature", signature_hex)
        .part("file", part);

    let client = reqwest::Client::new();
    let resp = match client
        .post(format!("{BASE_URL}/api/v1/developer/upload"))
        .bearer_auth(jwt)
        .multipart(form)
        .send()
        .await
    {
        Ok(r) => r,
        Err(err) => {
            eprintln!("Failed to upload package: {}", err);
            return;
        }
    };

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        eprintln!("Publish failed ({}): {}", status, body);
        return;
    }

    let response_body = resp.text().await.unwrap_or_default();
    println!(
        "Publish successful. SHA256: {}. Server response: {}",
        checksum_hex, response_body
    );
}

async fn handle_search(query: String) {
    let client = reqwest::Client::new();
    let resp = match client
        .get(format!("{BASE_URL}/api/v1/packages/search"))
        .query(&[("q", query.as_str())])
        .send()
        .await
    {
        Ok(r) => r,
        Err(err) => {
            eprintln!("Search request failed: {}", err);
            return;
        }
    };

    if resp.status() != StatusCode::OK {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        eprintln!("Search failed ({}): {}", status, body);
        return;
    }

    let packages: Vec<PackageSummary> = match resp.json().await {
        Ok(data) => data,
        Err(err) => {
            eprintln!("Failed to parse search response: {}", err);
            return;
        }
    };

    if packages.is_empty() {
        println!("No packages found.");
        return;
    }

    for pkg in packages {
        println!("{}", pkg.name);
        println!("  id: {}", pkg.id);
        println!("  developer_id: {}", pkg.developer_id);
        println!(
            "  description: {}",
            pkg.description.unwrap_or_else(|| "<none>".to_string())
        );
        println!("  created_at: {}", pkg.created_at);
    }
}

async fn handle_install(name: String) {
    let client = reqwest::Client::new();

    let package = match fetch_package_detail(&client, &name).await {
        Ok(data) => data,
        Err(err) => {
            eprintln!("{}", err);
            return;
        }
    };

    let latest = match select_latest_version(&package.versions) {
        Some(v) => v,
        None => {
            eprintln!("No versions available for package '{}'.", package.name);
            return;
        }
    };


    let bytes = match download_package_bytes(&client, &package.name, &latest.version).await {
        Ok(value) => value,
        Err(err) => {
            eprintln!("{}", err);
            return;
        }
    };

    if bytes.is_empty() {
        eprintln!("Downloaded package is empty. Aborting install.");
        return;
    }

    let computed_digest: [u8; 32] = Sha256::digest(&bytes).into();
    let computed_checksum = hex::encode(computed_digest);

    let expected_checksum_bytes = match hex::decode(latest.checksum.trim()) {
        Ok(value) => value,
        Err(err) => {
            eprintln!("Invalid checksum encoding in package metadata: {}", err);
            return;
        }
    };

    if expected_checksum_bytes.len() != 32 {
        eprintln!("Invalid checksum length in package metadata.");
        return;
    }

    if computed_digest.as_slice() != expected_checksum_bytes.as_slice() {
        eprintln!(
            "Checksum verification failed: expected {}, got {}",
            latest.checksum, computed_checksum
        );
        return;
    }

    let public_key_bytes = match hex::decode(&package.developer_public_key) {
        Ok(bytes) => bytes,
        Err(err) => {
            eprintln!("Invalid developer public key encoding: {}", err);
            return;
        }
    };
    if public_key_bytes.len() != 32 {
        eprintln!("Invalid developer public key length.");
        return;
    }

    let signature_bytes = match hex::decode(&latest.signature) {
        Ok(bytes) => bytes,
        Err(err) => {
            eprintln!("Invalid signature encoding: {}", err);
            return;
        }
    };
    if signature_bytes.len() != 64 {
        eprintln!("Invalid signature length.");
        return;
    }

    let pub_key: [u8; 32] = match public_key_bytes.as_slice().try_into() {
        Ok(arr) => arr,
        Err(_) => {
            eprintln!("Could not parse public key bytes.");
            return;
        }
    };

    let sig_arr: [u8; 64] = match signature_bytes.as_slice().try_into() {
        Ok(arr) => arr,
        Err(_) => {
            eprintln!("Could not parse signature bytes.");
            return;
        }
    };

    let verifying_key = match VerifyingKey::from_bytes(&pub_key) {
        Ok(key) => key,
        Err(err) => {
            eprintln!("Invalid verifying key: {}", err);
            return;
        }
    };

    let signature = Signature::from_bytes(&sig_arr);
    if let Err(err) = verifying_key.verify(&computed_digest, &signature) {
        eprintln!("Signature verification failed: {}", err);
        return;
    }

    let install_dir = PathBuf::from("installed").join(&package.name).join(&latest.version);
    if let Err(err) = fs::create_dir_all(&install_dir) {
        eprintln!(
            "Failed to create install directory {}: {}",
            install_dir.display(),
            err
        );
        return;
    }

    let decoder = GzDecoder::new(Cursor::new(bytes));
    let mut archive = Archive::new(decoder);
    if let Err(err) = archive.unpack(&install_dir) {
        eprintln!("Failed to extract archive: {}", err);
        return;
    }

    println!(
        "Installed {}@{} into {}",
        package.name,
        latest.version,
        install_dir.display()
    );
}

async fn fetch_package_detail(client: &reqwest::Client, name: &str) -> Result<PackageDetail, String> {
    let urls = [
        format!("{BASE_URL}/api/packages/{name}"),
        format!("{BASE_URL}/api/v1/packages/{name}"),
    ];

    let mut errors = Vec::new();
    for url in urls {
        let resp = match client.get(&url).send().await {
            Ok(r) => r,
            Err(err) => {
                errors.push(format!("{} -> request failed: {}", url, err));
                continue;
            }
        };

        if resp.status() == StatusCode::OK {
            return resp
                .json::<PackageDetail>()
                .await
                .map_err(|err| format!("{} -> invalid metadata response: {}", url, err));
        }

        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        errors.push(format!("{} -> HTTP {}: {}", url, status, body));
    }

    Err(format!(
        "Failed to fetch package metadata for '{}'. Tried endpoints:\n{}",
        name,
        errors.join("\n")
    ))
}

async fn download_package_bytes(
    client: &reqwest::Client,
    name: &str,
    version: &str,
) -> Result<Vec<u8>, String> {
    let urls = [
        format!("{BASE_URL}/api/packages/{name}/{version}/download"),
        format!("{BASE_URL}/api/v1/packages/{name}/{version}/download"),
    ];

    let mut errors = Vec::new();
    for url in urls {
        let resp = match client.get(&url).send().await {
            Ok(r) => r,
            Err(err) => {
                errors.push(format!("{} -> request failed: {}", url, err));
                continue;
            }
        };

        if resp.status() == StatusCode::OK {
            return resp
                .bytes()
                .await
                .map(|b| b.to_vec())
                .map_err(|err| format!("{} -> failed to read download bytes: {}", url, err));
        }

        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        errors.push(format!("{} -> HTTP {}: {}", url, status, body));
    }

    Err(format!(
        "Failed to download package '{}@{}'. Tried endpoints:\n{}",
        name,
        version,
        errors.join("\n")
    ))
}

fn home_dir() -> PathBuf {
    dirs::home_dir().unwrap_or_else(|| PathBuf::from("."))
}

fn vget_dir() -> PathBuf {
    home_dir().join(".vget")
}

fn config_path() -> PathBuf {
    vget_dir().join("config.json")
}

fn default_dev_key_paths() -> (PathBuf, PathBuf) {
    let key_dir = vget_dir();
    (key_dir.join("id_ed25519"), key_dir.join("id_ed25519.pub"))
}

fn extract_jwt_from_body(body: &str) -> Option<String> {
    let parsed: serde_json::Value = serde_json::from_str(body).ok()?;
    ["token", "jwt", "access_token"]
        .iter()
        .find_map(|key| parsed.get(key).and_then(|v| v.as_str()).map(str::to_string))
}

fn save_jwt(token: &str) -> Result<PathBuf, String> {
    let token_path = vget_dir().join("token");
    if let Some(parent) = token_path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("failed to create {}: {}", parent.display(), e))?;
    }

    fs::write(&token_path, format!("{}\n", token))
        .map_err(|e| format!("failed to write {}: {}", token_path.display(), e))?;
    Ok(token_path)
}

fn read_jwt_token() -> Result<String, String> {
    let token_path = vget_dir().join("token");
    let token = fs::read_to_string(&token_path).map_err(|err| {
        if err.kind() == io::ErrorKind::NotFound {
            format!(
                "JWT token not found at {}. Run `vget login --username <name>` first.",
                token_path.display()
            )
        } else {
            format!("failed to read {}: {}", token_path.display(), err)
        }
    })?;

    let token = token.trim().to_string();
    if token.is_empty() {
        return Err(format!(
            "JWT token file is empty at {}. Run `vget login` again.",
            token_path.display()
        ));
    }

    Ok(token)
}

fn load_config() -> CliConfig {
    let path = config_path();
    match fs::read_to_string(&path) {
        Ok(contents) => serde_json::from_str(&contents).unwrap_or_default(),
        Err(_) => CliConfig::default(),
    }
}

fn save_config(config: &CliConfig) -> Result<(), String> {
    let path = config_path();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("failed to create {}: {}", parent.display(), e))?;
    }

    let serialized = serde_json::to_string_pretty(config)
        .map_err(|e| format!("failed to serialize config: {}", e))?;
    fs::write(&path, format!("{}\n", serialized))
        .map_err(|e| format!("failed to write {}: {}", path.display(), e))
}

fn create_tar_gz(source_path: &Path, archive_path: &Path) -> Result<(), String> {
    let archive_file = fs::File::create(archive_path)
        .map_err(|e| format!("failed to create {}: {}", archive_path.display(), e))?;
    let encoder = GzEncoder::new(archive_file, Compression::default());
    let mut builder = Builder::new(encoder);

    if source_path.is_dir() {
        let base = source_path
            .file_name()
            .and_then(|s| s.to_str())
            .filter(|s| !s.is_empty())
            .unwrap_or("package");
        builder
            .append_dir_all(base, source_path)
            .map_err(|e| format!("failed to archive directory {}: {}", source_path.display(), e))?;
    } else {
        let name = source_path
            .file_name()
            .ok_or_else(|| format!("invalid file path: {}", source_path.display()))?;
        builder
            .append_path_with_name(source_path, name)
            .map_err(|e| format!("failed to archive file {}: {}", source_path.display(), e))?;
    }

    let encoder = builder
        .into_inner()
        .map_err(|e| format!("failed to finish tar stream: {}", e))?;
    encoder
        .finish()
        .map_err(|e| format!("failed to finish gzip stream: {}", e))?;
    Ok(())
}

fn temp_archive_path(package_name: &str, version: &str) -> PathBuf {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or_default();

    env::temp_dir().join(format!("{}-{}-{}.tar.gz", package_name, version, timestamp))
}

struct TempArchive {
    path: PathBuf,
}

impl TempArchive {
    fn new(path: PathBuf) -> Self {
        Self { path }
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for TempArchive {
    fn drop(&mut self) {
        remove_if_exists(&self.path);
    }
}

fn read_signing_key(path: &Path) -> Result<SigningKey, String> {
    let hex_key = fs::read_to_string(path)
        .map_err(|e| format!("failed to read {}: {}", path.display(), e))?;
    let key_bytes = hex::decode(hex_key.trim())
        .map_err(|e| format!("invalid private key hex in {}: {}", path.display(), e))?;
    let arr: [u8; 32] = key_bytes
        .as_slice()
        .try_into()
        .map_err(|_| format!("invalid private key length in {}", path.display()))?;
    Ok(SigningKey::from_bytes(&arr))
}

fn extract_package_name(path: &Path) -> String {
    let file_name = match path.file_name().and_then(|name| name.to_str()) {
        Some(value) => value,
        None => return String::new(),
    };

    if let Some(stripped) = file_name.strip_suffix(".tar.gz") {
        return stripped.to_string();
    }

    path.file_stem()
        .and_then(|stem| stem.to_str())
        .unwrap_or_default()
        .to_string()
}

fn select_latest_version(versions: &[PackageVersionResponse]) -> Option<&PackageVersionResponse> {
    versions.iter().max_by(|a, b| {
        let va = Version::parse(&a.version);
        let vb = Version::parse(&b.version);

        match (va, vb) {
            (Ok(left), Ok(right)) => left.cmp(&right),
            _ => a.version.cmp(&b.version),
        }
    })
}

fn remove_if_exists(path: &Path) {
    if path.exists() {
        let _ = fs::remove_file(path);
    }
}

fn get_max_installed_version(name: &str) -> Option<String> {
    let pkg_dir = PathBuf::from("installed").join(name);
    let mut max_version: Option<Version> = None;
    if let Ok(entries) = fs::read_dir(pkg_dir) {
        for entry in entries.flatten() {
            if let Ok(file_name) = entry.file_name().into_string() {
                if let Ok(v) = Version::parse(&file_name) {
                    match max_version {
                        None => max_version = Some(v),
                        Some(ref m) if v > *m => max_version = Some(v),
                        _ => {}
                    }
                }
            }
        }
    }
    max_version.map(|v| v.to_string())
}

async fn handle_update(name: String) {
    let client = reqwest::Client::new();
    let package = match fetch_package_detail(&client, &name).await {
        Ok(data) => data,
        Err(err) => {
            eprintln!("{}", err);
            return;
        }
    };

    let latest = match select_latest_version(&package.versions) {
        Some(v) => v,
        None => {
            eprintln!("No versions available for package '{}'.", package.name);
            return;
        }
    };

    if let Ok(latest_ver) = Version::parse(&latest.version) {
        if let Some(installed) = get_max_installed_version(&name) {
            if let Ok(installed_ver) = Version::parse(&installed) {
                if latest_ver <= installed_ver {
                    println!("Package '{}' is already up to date ({} >= {}).", name, installed, latest.version);
                    return;
                }
            }
        }
    } else {
        let install_dir = PathBuf::from("installed").join(&package.name).join(&latest.version);
        if install_dir.exists() {
            println!("Package '{}' is already at the latest version ({}).", name, latest.version);
            return;
        }
    }

    println!("Updating package '{}' to version {}...", name, latest.version);
    handle_install(name).await;
}

async fn handle_delete(name: String, remote: bool) {
    let dir = PathBuf::from("installed").join(&name);
    if dir.exists() {
        if let Err(err) = fs::remove_dir_all(&dir) {
            eprintln!("Failed to remove local package '{}': {}", name, err);
        } else {
            println!("Successfully removed local package '{}'.", name);
        }
    } else {
        println!("Local package '{}' not found.", name);
    }

    if remote {
        let jwt = match read_jwt_token() {
            Ok(token) => token,
            Err(e) => {
                eprintln!("Cannot delete remote package: {}", e);
                return;
            }
        };

        let client = reqwest::Client::new();
        let url = format!("{BASE_URL}/api/v1/packages/{}", name);
        let resp = match client.delete(&url).bearer_auth(&jwt).send().await {
            Ok(r) => r,
            Err(err) => {
                eprintln!("Failed to send delete request: {}", err);
                return;
            }
        };

        if resp.status().is_success() {
            println!("Successfully deleted package '{}' from remote.", name);
        } else {
            eprintln!("Failed to delete package '{}' from remote ({}): {}", name, resp.status(), resp.text().await.unwrap_or_default());
        }
    }
}
