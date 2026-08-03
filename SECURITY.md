# Security Policy

## Supported Versions

Security fixes are applied to the [latest stable release](https://github.com/CRSD-Lau/deep-live-cam/releases/latest). Older releases, development branches, and locally modified builds are not supported unless a security advisory explicitly says otherwise.

## Reporting A Vulnerability

Do not open a public issue for an undisclosed vulnerability. Use GitHub's
[private vulnerability reporting form](https://github.com/CRSD-Lau/deep-live-cam/security/advisories/new)
and include:

- affected version and execution profile;
- impact and realistic attack scenario;
- reproduction steps or a minimal proof of concept;
- affected files or functions;
- suggested mitigation, if known.

### Response Targets

- acknowledgement within seven days;
- initial severity and scope assessment within fourteen days when reproducible;
- coordinated remediation and disclosure timing based on impact, packaging, and release complexity.

These are response targets rather than guaranteed resolution times. Please allow time to validate, patch, package, and coordinate disclosure before publishing details.

## In Scope

- model-download consent, transport, and checksum verification;
- processing of untrusted images, videos, model files, and metadata;
- local file access, command execution, or privilege-boundary issues;
- installer, updater, release-asset, and corresponding-source integrity;
- dependency or packaged-runtime vulnerabilities reachable through shipped application behaviour.

Reports about an unshipped development dependency should explain how the vulnerable code reaches the packaged application or release process.

## Out of Scope

- social engineering, phishing, or physical attacks against maintainers;
- denial-of-service tests that create avoidable cost or disruption;
- reports that require publishing private faces, videos, credentials, or model files;
- unsupported operating systems or substantially modified third-party builds;
- findings that identify only a vulnerable version string without a reachable application or release path.

## Security Boundaries

- Model files are downloaded only after explicit consent and are verified by
  SHA-256 before installation.
- Release binaries intentionally exclude model/checkpoint files.
- Treat faces, images, videos, and third-party ONNX models as untrusted input.
- Download releases only from this repository and verify the published
  SHA-256 sums.
- Never include personal media, credentials, private logs, or model binaries
  in a vulnerability report.

Security reports do not override the separate model licences and usage
restrictions documented in `LICENSES/MODEL_LICENSE_AUDIT.md`.

## Safe Harbour

Good-faith research that follows this policy, avoids privacy violations and service disruption, and provides reasonable time for remediation will be treated as authorised security research for this project. This statement cannot authorise activity against third-party services or software.
