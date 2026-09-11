# Haven Architecture

## Overview

Haven is a multi-agent AI system that coordinates food bank operations through five specialized agents orchestrated by a Supervisor. The system is designed for reliability, scale, and human trust.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                    HAVEN SYSTEM                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  SMS/V   │  │  Web UI  │  │  Email   │          │
│  │ (Twilio) │  │ (Next.js)│  │  (SES)   │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                │
│       └──────────────┼──────────────┘                │
│                      ▼                               │
│           ┌──────────────────┐                       │
│           │   Supervisor     │                       │
│           │     Agent        │                       │
│           └────────┬─────────┘                       │
│                    │                                 │
│       ┌────────────┼────────────┐                    │
│       ▼            ▼            ▼                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ Donor   │ │Volunteer│ │Recipient│               │
│  │ Agent   │ │  Agent  │ │  Agent  │               │
│  └────┬────┘ └────┬────┘ └────┬────┘               │
│       │           │           │                      │
│       ▼           ▼           ▼                      │
│  ┌─────────┐ ┌─────────┐                            │
│  │Logistics│ │Compli-  │                            │
│  │  Agent  │ │ ance    │                            │
│  └─────────┘ └─────────┘                            │
│                                                      │
├─────────────────────────────────────────────────────┤
│                    AWS SERVICES                       │
│  Bedrock · DynamoDB · S3 · OpenSearch · Cognito     │
│  Polly · Transcribe · Translate · EventBridge       │
├─────────────────────────────────────────────────────┤
│                  EXTERNAL SERVICES                    │
│              Twilio · Langfuse · Google Maps         │
└─────────────────────────────────────────────────────┘
```

## Data Flow

### Donation Offer Flow

```
1. Donor texts "I have 200 lbs of vegetables to donate"
     │
2. Twilio webhook → EventBridge → Supervisor
     │
3. Supervisor routes to DonorAgent
     │
4. DonorAgent:
   ├── parse_donation_offer() → structured data
   ├── check_cold_chain_requirements() → needs refrigeration
   ├── accept_donation() → status updated
   └── generate_tax_receipt() → receipt queued
     │
5. Supervisor triggers LogisticsAgent
   ├── optimize_route() → multi-stop route
   ├── generate_manifest() → driver instructions
   └── dispatch_driver() → SMS to driver
     │
6. ComplianceAgent logs audit trail entry
     │
7. Dashboard updates in real time
```

### Recipient Inquiry Flow

```
1. Person calls in Spanish: "¿Tienen fórmula para bebé?"
     │
2. Twilio Voice → Transcribe → EventBridge → Supervisor
     │
3. Supervisor routes to RecipientAgent
     │
4. RecipientAgent:
   ├── translate_response() → English
   ├── find_nearest_pantry() → location-based search
   ├── check_pantry_hours() → open now
   ├── list_available_items() → baby formula in stock
   └── translate_response() → Spanish response
     │
5. Response sent via Polly (voice) + SMS
     │
6. ComplianceAgent logs audit trail
```

## Agent Design Principles

### Single Responsibility
Each agent does one thing well. The DonorAgent never tries to match volunteers. The LogisticsAgent never tries to generate tax receipts.

### Human-in-the-Loop
Agents escalate to humans when:
- Decision is novel or ambiguous
- Value exceeds threshold ($5,000+)
- Safety concern detected
- Recipient complaint
- Agent confidence below 70%

### Observability
Every agent action is traced via Langfuse:
- LLM calls with full prompts and responses
- Tool invocations with parameters and results
- Decision reasoning at each step
- Latency and error metrics

### Graceful Degradation
If one agent fails, others continue. The Supervisor detects failures and retries with exponential backoff. Critical failures trigger human notification.

## Technology Decisions

### Strands Agents SDK
- **Agent hierarchies**: Supervisor → Specialists maps to food bank org structure
- **Tool composition**: `@tool` decorator for clean, composable tools
- **Swarm patterns**: Multiple agents coordinating on shared goals
- **Model flexibility**: Different models for reasoning vs routing

### Bedrock AgentCore
- Production-grade deployment without infrastructure management
- Built-in scaling, monitoring, and security
- Direct access to Claude and Nova models
- Bonus points for hackathon judging

### DynamoDB
- Pay-per-request for unpredictable food bank traffic patterns
- Point-in-time recovery for compliance requirements
- TTL for temporary data (session tokens, cached results)
- Global tables for future multi-region expansion

### OpenSearch Serverless
- Semantic search for recipient resource matching
- "I need help with baby formula" matches to baby supplies category
- Multilingual search across 8 languages
- No cluster management with serverless

## Security Architecture

### Authentication
- Cognito UserPool for admin access
- JWT validation on all API endpoints
- MFA required for production deployments

### Data Protection
- DynamoDB encryption at rest (KMS)
- TLS 1.3 for all data in transit
- Recipient PII pseudonymized in logs
- Minimum data retention (90 days default)
- Right-to-delete endpoint

### Network
- CORS locked to production domain
- CSP headers via Next.js middleware
- Rate limiting: 100 req/min per IP
- API keys in AWS Secrets Manager

## Scaling Considerations

### Current (MVP)
- Single-region deployment
- Pay-per-request DynamoDB
- Serverless OpenSearch
- Bedrock on-demand inference

### Production (Future)
- Multi-region with DynamoDB Global Tables
- Bedrock provisioned throughput for peak hours
- ElastiCache for session and rate limiting
- SQS for async agent communication
- Step Functions for complex multi-agent workflows

## Monitoring

### Metrics (CloudWatch)
- Agent response time (p50, p95, p99)
- Tool invocation success rate
- LLM token usage and cost
- EventBridge delivery latency

### Tracing (Langfuse + X-Ray)
- End-to-end request tracing
- Agent reasoning chains
- Tool call breakdowns
- Error root cause analysis

### Alerting
- Agent failure rate > 5% → PagerDuty
- Cold chain temperature breach → Immediate SMS
- Response time > 30s → Slack notification
- Cost anomaly → Email to admin
