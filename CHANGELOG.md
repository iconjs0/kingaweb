# Changelog

All notable changes to KingaWeb will be documented here. The project intends to follow [Semantic Versioning](https://semver.org/) once its first versioned release is published.

## [Unreleased]

### Added

- Product and Engineering Master Plan in Word and PDF formats.
- Dependency-free HTTPS, TLS and security-header proof of concept.
- Production-oriented monorepo boundaries for web, API, scanner, contracts and infrastructure.
- Initial architecture, roadmap, contribution, conduct and security documentation.
- AI intelligence architecture with evidence grounding and human approval boundaries.
- Next.js and TypeScript production web foundation with a responsive landing experience.
- FastAPI control-plane foundation with validated configuration and health endpoint tests.
- ADR-0002 recording the initial production application stack.
- PostgreSQL-ready identity, workspace, membership, asset and domain-verification models.
- OIDC bearer-token validation boundary and role-based workspace authorization.
- Initial database migration and secured domain-asset registration contract.
- Repeatable zero-container local API setup with migrated SQLite development storage.
- Separate liveness and database-readiness endpoints for operational monitoring.
- Development-only signed sessions with production-enforced RS256 OIDC boundaries.
- Protected workspace dashboard and tenant-scoped workspace/asset read APIs.
- Local sign-in and sign-out flows using short-lived HTTP-only session cookies.
- Authorized domain onboarding with expiring DNS TXT ownership challenges.
- Bounded DNS verification, tenant-role enforcement and verified asset status transitions.
