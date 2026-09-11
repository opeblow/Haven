# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within Haven, please send an email to
security@haven-agent.org. All security vulnerabilities will be promptly addressed.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response SLA

- **Acknowledgment**: within 24 hours
- **Initial assessment**: within 48 hours
- **Fix or mitigation**: within 7 days for critical, 30 days for others

## Threat Model

### Trust Boundaries

1. **External → Haven API**: AWS Cognito (admin UI only), optional API-key gate, input validation
2. **Haven API → Agents**: Internal network, IAM-based access
3. **Agents → AWS Services**: IAM roles, least-privilege policies
4. **Agents → External (Twilio)**: API key authentication, webhook validation

### Data Classification

- **Public**: Organization name, pantry locations, hours
- **Internal**: Agent reasoning traces, system metrics
- **Confidential**: Recipient PII, volunteer contact info
- **Restricted**: API keys, credentials, encryption keys

### Security Controls

**Implemented**

- AWS Cognito user pool with optional MFA for admin access (CDK resource defined)
- Optional `X-API-Key` gate on mutating API endpoints (`HAVEN_API_KEY` env var; disabled when unset)
- DynamoDB client-side encryption via AWS SDK default encryption
- Secrets returned from environment / AWS Secrets Manager (never in source)
- `DELETE /api/recipients/{id}` endpoint for recipient right-to-delete
- CORS origin allowlist via `HAVEN_CORS_ORIGINS`

**Planned / not yet enforced**

- JWT validation on every API route (only Cognito is wired in CDK today)
- Rate limiting (100 req/min per IP)
- TLS 1.3 enforced at API Gateway (currently not deployed)
- CSP headers on web responses
- DynamoDB KMS encryption at rest with explicit CMK
- 90-day minimum retention policy

## Recipient Data Protection

Recipient data is treated with the highest sensitivity:
- Pseudonymized in logs and audit trails
- Minimum retention (90 days default) — not yet enforced in DynamoDB TTL
- Right-to-delete endpoint: `DELETE /api/recipients/{id}`
- No data sold or shared with third parties
