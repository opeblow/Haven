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

1. **External → Haven API**: Cognito authentication, rate limiting, input validation
2. **Haven API → Agents**: Internal network, IAM-based access
3. **Agents → AWS Services**: IAM roles, least-privilege policies
4. **Agents → External (Twilio)**: API key authentication, webhook validation

### Data Classification

- **Public**: Organization name, pantry locations, hours
- **Internal**: Agent reasoning traces, system metrics
- **Confidential**: Recipient PII, volunteer contact info
- **Restricted**: API keys, credentials, encryption keys

### Security Controls

- Cognito with MFA for admin access
- DynamoDB encryption at rest with KMS
- TLS 1.3 for all data in transit
- JWT validation on all API endpoints
- Rate limiting (100 req/min per IP)
- CSP headers on all web responses
- Secrets in AWS Secrets Manager (never in code)

## Recipient Data Protection

Recipient data is treated with the highest sensitivity:
- Pseudonymized in logs and audit trails
- Minimum retention (90 days default)
- Right-to-delete endpoint: `DELETE /api/recipients/{id}`
- No data sold or shared with third parties
