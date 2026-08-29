# Patch Radar: Architecture, Security & Threat Model

This document outlines the high-level architecture of **Patch Radar**, an enterprise patch advisory aggregation system, alongside its foundational Application Security (AppSec) controls. It includes a formal **STRIDE Threat Model**, as well as how **SAST (Semgrep)** and **DAST (OWASP ZAP)** are integrated securely into the Software Development Life Cycle (SDLC).

---

## 1. System Architecture

Patch Radar leverages an **Event-Driven Adapter Pattern** to aggregate patch and firmware metadata from heavily fragmented vendor ecosystems (VMware, Cisco, Dell, HPE, Palo Alto, Fortinet, etc.) without relying on a unified upstream API.

### 1.1 High-Level Component Diagram

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                           INGESTION TIER (Adapters)                         │
 │                                                                             │
 │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
 │  │ Cisco (JSON) │   │ VMware (XML) │   │ Palo Alto    │   │ Fortinet RSS │  │
 │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘  │
 └─────────┼──────────────────┼──────────────────┼──────────────────┼──────────┘
           │                  │                  │                  │
           ▼                  ▼                  ▼                  ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                         NORMALIZATION & VALIDATION                          │
 │  • SemVer / Build Normalizer      • Checksum & Integrity Verifier           │
 │  • CVE / CVSS Enrichment          • Deduplication Engine                    │
 └───────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                            STORAGE & EVENT BUS                              │
 │  • PostgreSQL (Catalog Metadata, Inventory, Audit Logs)                     │
 │  • Redis (Response Caching, Distributed Locks, Rate Limiting)               │
 └───────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                             API & CONSUMPTION                               │
 │  • FastAPI REST Engine (RBAC, Rate-Limited)                                 │
 │  • Next.js Unified Security Dashboard                                       │
 │  • Webhook Dispatcher (Slack, Teams, PagerDuty Events v2)                   │
 └─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Components
* **Backend (FastAPI, Python 3.12)**: Handles ingestion pipelines and serves standard REST APIs.
* **Storage (PostgreSQL 16)**: Strict relational constraints ensure no duplicate patches can exist `(vendor, model, component, normalized_version)`.
* **Caching & Queue (Redis 7)**: Protects the database from query spikes and enforces strict sliding-window rate limits on the API.
* **Frontend (Next.js 14, TailwindCSS)**: Static React UI designed for standalone or SSR deployments.

---

## 2. Threat Modeling (using STRIDE)

Because Patch Radar serves as a security tool (advising on vulnerabilities), compromising the tool itself could blind an organization to critical patches. The system was threat-modeled using the **STRIDE** framework.

| Threat Category | Defined Threat Scenarios in Patch Radar | Mitigations & Controls Implemented |
| :--- | :--- | :--- |
| **(S)poofing** *(Pretending to be someone else)* | 1. An attacker spoofs a vendor's upstream feed to inject malicious advisory data.<br>2. An attacker spoofs a `SecurityAnalyst` JWT token. | • Connections to vendors enforce **mTLS / HTTPS** exclusively. <br>• JWT tokens enforce strict signature validation (HS256 minimum, transition to RS256 with IdP integration). |
| **(T)ampering** *(Modifying data)* | 1. Tampering with patch data in PostgreSQL (e.g., hiding a critical CVE).<br>2. Changing the calculated SHA-256 binary checksums. | • Implemented cryptographic checksum verification at ingestion (`app/normalizer.py`).<br>• The Postgres database executes operations via an ORM using prepared statements, averting SQL injection. |
| **(R)epudiation** *(Claiming no action was taken)* | 1. An `OpsAdmin` forces a manual patch ingestion but denies doing it.<br>2. Webhooks fail silently without a trail. | • **`ingestion_audit` database table** records exactly when an ingestion started, completed, and error output.<br>• Webhook dispatcher utilizes transactional logging for successful/failed alerts. |
| **(I)nformation Disclosure** *(Exposing secrets)* | 1. Exposing the Cisco/Palo Alto OAuth credentials to the frontend UI.<br>2. Emitting stack traces in FastAPI 500 errors. | • Cisco Client/Secrets are kept completely server-side in `.env` / Hashicorp Vault (never exposed to React hooks).<br>• FastAPI production configuration obscures stack traces to users. |
| **(D)enial of Service** *(Exhausting resources)* | 1. Spamming `/api/v1/patches` to DDoS the Postgres database.<br>2. Triggering runaway scraping jobs that block memory. | • **Redis rate-limiting middleware** (`app/main.py`) applied to all paths.<br>• Query caching via Redis reduces DB load.<br>• Distributed locks ensure only 1 worker can ingest a vendor's patches concurrently. |
| **(E)levation of Privilege** *(Gaining high access)* | 1. A `SecurityAnalyst` manipulates the API to trigger destructive admin operations (like cache flush or re-ingest). | • FastAPI dependencies implement rigid Role-Based Access Control (RBAC). The `require_role(rule)` decorator forces strict JWT claim validation. |

---

## 3. Application Security Pipeline

Patch Radar integrates shift-left and shift-right methodologies to assure the codebase remains secure over time. 

### 3.1 SAST (Static Application Security Testing) with Semgrep
Static analysis runs on every Pull Request via GitHub Actions. We selected [Semgrep](https://semgrep.dev/) for its speed and ability to catch context-specific vulnerabilities rapidly.

**Configured Rule Suites:**
* `p/python`: Prevents insecure use of standard libraries, `eval()`, shell injection, and path traversals in the adapters tier.
* `p/fastapi`: Checks for CORS misconfigurations, missing auth decorators, and unhandled SQL string concatenations (ensures SQLAlchemy is used correctly).
* `p/typescript` & `p/react`: Hooks into the Next.js frontend to catch DOM-based XSS or dangerouslySetInnerHTML.
* `p/secrets`: Blocks accidental commits of Cisco API keys, JWT secrets, or Webhook URIs.

**Example SAST Enforcement:**
If a developer accidentally attempts to construct a raw SQL query string in `list_patches`, Semgrep will block the merge citing: *"Detected raw string concatenation in SQL query. Use SQLAlchemy prepared statements."*

### 3.2 DAST (Dynamic Application Security Testing) with OWASP ZAP
Once the containerized application is deployed to a staging environment, an automated **Dynamic Application Security Test (DAST)** executes using the OWASP ZAP (Zed Attack Proxy) baseline scanner against the OpenAPI spec (`/docs` or `/openapi.json`).

**DAST Target Vectors:**
1. **Unauthenticated API Fuzzing**: ZAP bombards endpoints like `POST /api/v1/ingest/cisco` without a Bearer token to ensure it properly returns `401 Unauthorized`.
2. **Rate Limit Efficacy**: Verifies that sending >120 requests/minute to the list endpoints triggers the HTTP 429 Redis rate limiter.
3. **Security Headers Analysis**: Confirms the FastAPI middleware correctly serves `Strict-Transport-Security`, `X-Content-Type-Options`, and appropriate CORS boundaries on the REST framework responses.
4. **Input Fuzzing**: Attempts to inject bizarre payload strings into the Next.js search boxes (e.g., `<script>alert(1)</script>`) to ensure the React UI safely sanitizes inputs and does not reflect raw parameters.

---

## Conclusion
By engineering **Patch Radar** around immutable normalization structures, employing robust **RBAC/Auth protocols**, caching data via **Redis**, and rigorously mapping attack surfaces with **STRIDE**, the system ensures that querying metadata about zero-days does not ironically introduce zero-days into your software pipeline.
