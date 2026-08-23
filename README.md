<div align="center">

# KingaWeb

### See risks early. Stay protected.

**A mobile-first external security monitoring and remediation platform built for African businesses and the agencies that support them.**

[Product vision](#product-vision) · [Capabilities](#capabilities) · [Architecture](#architecture) · [Roadmap](#roadmap) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

</div>

---

## Project status

> **Foundation / pre-alpha.** KingaWeb is under active development and is not yet suitable for protecting production systems. The current runnable application is a proof of concept preserved in [`prototype/`](prototype/README.md).

| Area | Status |
|---|---|
| Product and engineering master plan | Complete — working baseline |
| Safe HTTPS/TLS/header proof of concept | Complete |
| Customer discovery | Next |
| Production architecture | Planned |
| Private MVP | Planned |
| Public availability | Not released |

## Product vision

KingaWeb helps organizations discover public-facing security risks, understand their business impact and verify that remediation worked. It is designed for teams that need continuous visibility without the complexity and cost of an enterprise security operations centre.

The platform begins with verified domains and websites, then grows into a governed external attack-surface platform covering DNS, TLS, email security posture, exposed assets, suspicious changes and domain impersonation.

### What makes KingaWeb different

- **Action, not alarm:** findings include evidence, business impact, ownership, remediation and verification.
- **African operating fit:** mobile-first UX, low-bandwidth performance, English/Kiswahili architecture and regional pricing.
- **Agency-first operations:** multi-client portfolios, delegated access and client-ready reporting.
- **Explainable intelligence:** transparent rule versions, confidence, evidence timestamps and scoring methodology.
- **Responsible by design:** target verification, bounded checks, isolation, audit logs and abuse prevention.
- **Continuous improvement:** a release can be complete; the security platform continues evolving with threats and customer evidence.

## Capabilities

### Release One

- Verified domain onboarding
- HTTPS and TLS certificate monitoring
- HTTP security-header and cookie analysis
- DNS and email-domain posture checks
- Availability, response-time and change monitoring
- Versioned findings and transparent security scoring
- Finding assignment and remediation workflow
- Verified rescans and evidence history
- Alerts, reports and agency portfolio views
- Workspace roles, audit records and data controls

### AI-powered intelligence

KingaWeb uses deterministic observations as the source of truth. AI assists with correlation and understanding; it does not invent vulnerabilities or autonomously attack or modify customer systems.

- Bilingual Risk Copilot grounded in authorized workspace evidence
- Near-real-time change summaries and event correlation
- Alert grouping and context-aware prioritization
- Historical anomaly detection
- Stack-specific remediation guidance and draft tickets
- Evidence-linked incident timelines
- Executive posture digests
- Feedback-informed ranking with controlled evaluation

High-impact actions always require human approval and deterministic downstream authorization.

## Architecture

KingaWeb separates its customer-facing **control plane** from its isolated **scanning data plane**.

```text
Browser / PWA
      │
      ▼
Web application ──► API ──► PostgreSQL / object storage
                       │
                       ▼
                 Signed job queue
                       │
                       ▼
             Isolated scanner workers
                       │
                       ▼
          Observations ──► Rules ──► Findings
                                  │
                                  ▼
                    Intelligence and policy layer
                                  │
                                  ▼
                    Alerts, reports, remediation
```

Proposed production direction:

| Layer | Direction |
|---|---|
| Web | Next.js, TypeScript and a responsive PWA |
| API | NestJS/TypeScript or FastAPI/Python — decision pending ADR |
| Scanner | Isolated Python workers |
| Data | Managed PostgreSQL, queue/cache and encrypted object storage |
| Identity | Managed OIDC with MFA and secure recovery |
| Observability | OpenTelemetry-compatible logs, metrics and traces |
| Delivery | Containers, infrastructure as code and signed releases |

See the [architecture overview](docs/architecture/README.md) and [decision records](docs/architecture/decisions/).

## Repository structure

```text
kingaweb/
├── apps/
│   └── web/                 # Customer-facing web application
├── services/
│   ├── api/                 # Control-plane API
│   └── scanner/             # Isolated security-check workers
├── packages/
│   └── contracts/           # Shared schemas and API/event contracts
├── infra/                   # Infrastructure as code and environments
├── prototype/               # Current dependency-free proof of concept
├── docs/
│   ├── architecture/        # Architecture and decision records
│   └── ...                  # Master product and engineering plan
└── .github/                 # Contribution and repository workflows
```

The directories represent ownership boundaries. Production implementation begins after the open architecture decisions are approved.

## Quick start: proof of concept

The prototype requires Python 3.10 or newer and intentionally uses no third-party packages.

```bash
cd prototype
python3 server.py
```

Open `http://127.0.0.1:8080`, then enter a public website you own or are authorized to check.

The prototype performs a small HTTPS request, certificate inspection and header analysis. It rejects localhost and private network addresses and does not exploit vulnerabilities, guess credentials or scan arbitrary ports.

## Roadmap

1. **Discovery** — validate the target segment, interview businesses/agencies and recruit a design partner.
2. **Foundation** — establish the production monorepo, design system, identity, CI, threat model and worker isolation.
3. **Private MVP** — verified assets, safe scanning, findings, evidence and manual rescans.
4. **Private beta** — scheduled monitoring, alerts, history, remediation and agency workspaces.
5. **Public V1** — billing, reports, trust centre, support and production operations.
6. **Continuous evolution** — AI correlation, additional signals, integrations, impersonation monitoring and regional expansion.

Detailed gates live in [`docs/ROADMAP.md`](docs/ROADMAP.md) and the [Product & Engineering Master Plan](docs/KingaWeb_Product_and_Engineering_Master_Plan.docx).

## Security and authorization

KingaWeb is a defensive system. Only scan assets you own or have explicit permission to assess.

The production platform will require ownership verification before recurring or expanded checks. Scanner workers will use strict timeouts, response limits, destination revalidation, controlled egress and isolated credentials. See [`SECURITY.md`](SECURITY.md) for reporting and scope.

## Documentation

- [Product & Engineering Master Plan — Word](docs/KingaWeb_Product_and_Engineering_Master_Plan.docx)
- [Product & Engineering Master Plan — PDF](output/pdf/KingaWeb_Product_and_Engineering_Master_Plan.pdf)
- [Roadmap and delivery gates](docs/ROADMAP.md)
- [Architecture overview](docs/architecture/README.md)
- [Architecture Decision Records](docs/architecture/decisions/)
- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)

## Contributing

KingaWeb welcomes responsible contributions. Start with [`CONTRIBUTING.md`](CONTRIBUTING.md), discuss substantial changes before implementation and never test against a system without authorization.

## License

No open-source license has been selected yet. Until a license is added, the repository remains **all rights reserved** and external reuse or redistribution is not granted.

---

<div align="center">

Built responsibly in Tanzania, with an ambition to protect organizations across Africa.

</div>
