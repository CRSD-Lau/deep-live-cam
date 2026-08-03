# Security Policy

## Supported Versions

Security fixes are applied to the latest published release line.

| Version | Supported |
| --- | --- |
| 2.2.x | Yes |
| 2.1.x and older | No; upgrade to the latest release |

## Reporting A Vulnerability

Do not open a public issue for an undisclosed vulnerability. Use GitHub's
[private vulnerability reporting form](https://github.com/CRSD-Lau/deep-live-cam/security/advisories/new)
and include:

- affected version and execution profile;
- impact and realistic attack scenario;
- reproduction steps or a minimal proof of concept;
- affected files or functions;
- suggested mitigation, if known.

You should receive an acknowledgement within seven days. Please allow time to
validate, patch, package, and coordinate disclosure before publishing details.

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
