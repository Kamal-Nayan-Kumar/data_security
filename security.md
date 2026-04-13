1. Cryptographic Integrity & Authenticity
* SHA-256 Checksums: Every package version is hashed upon publication. The CLI client recalculates and verifies this hash during download to detect any corruption or network tampering.
* Ed25519 Digital Signatures: Developers sign the package checksum using their private key. The system uses public-key cryptography to verify the author's identity before any code is extracted or executed.
* End-to-End Verification: Unlike traditional registries, verification occurs locally on the user's machine. This ensures that even if the central server is compromised, the client will reject any unauthorized or tampered packages.
--- 
2. Authentication & Authorization
* JWT (JSON Web Tokens): All sensitive operations, including developer uploads and session management, are protected via JWTs with a 1-hour expiration.
* bcrypt Password Hashing: User passwords are never stored in plain text; they are hashed with a cryptographic salt using the bcrypt algorithm to protect against brute-force and rainbow table attacks.
* Role-Based Protection: The backend implements strict ownership checks (e.g., verifying that only the original developer of a package can push new versions).
---
3. Integrated Security Scanning (ml_scanner)
The project includes a dedicated security layer that scans packages for threats:

* Static Code Analysis: Detects common insecure coding patterns and vulnerabilities.
* Secret Detection: Automatically identifies hardcoded API keys, database credentials, and private tokens.
* Dependency Auditing: Scans requirements.txt or similar files for known vulnerable third-party libraries.
* Configuration Audit: Checks for insecure settings in environment or configuration files.
* AI-Powered Risk Scoring: Uses a pre-trained Machine Learning model (classifier.pkl) to analyze code behavior and assign a probability-based risk score, flagging potential malware.
---
4. Infrastructure & Pipeline Security
* Deterministic Packaging: Directories are uniformly compressed into .tar.gz archives before signing to ensure bit-perfect consistency for hashing.
* CORS Protection: Access to the API is restricted via Cross-Origin Resource Sharing middleware to prevent unauthorized browser-based requests.
* Environment Isolation: Sensitive secrets (like JWT_SECRET) and database credentials are managed exclusively through .env files to prevent leakage in source control.
* Docker Containerization: The entire stack (PostgreSQL, Backend) is containerized, providing process isolation and a controlled environment.
---
5. Input Validation
* Pydantic Enforcement: All API inputs are strictly validated using Pydantic models to prevent injection attacks and ensure data consistency.
* Key Format Validation: Developer public keys are strictly validated as 32-byte hex strings before registration.