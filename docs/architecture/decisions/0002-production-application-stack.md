# ADR-0002: Production application stack

- **Status:** Accepted
- **Date:** 2026-08-23
- **Owners:** KingaWeb maintainers

## Context

KingaWeb needs an accessible, mobile-first customer experience, a strongly validated control plane and isolated security workers. The first team is small, so the platform should minimize unnecessary operational complexity while preserving explicit trust boundaries.

## Decision

- Build the customer application as a Next.js application using TypeScript, React and the App Router.
- Build the control-plane API with FastAPI, Python and Pydantic.
- Keep scanner workers in a separate Python service and communicate through versioned job and observation contracts.
- Use pnpm workspaces for JavaScript/TypeScript packages and standard Python project metadata for Python services.
- Target managed PostgreSQL as the system of record and a queue for signed scan jobs in the next vertical slice.
- Keep identity behind an OIDC boundary so the provider can change without rewriting tenant authorization.

## Consequences

- The web interface receives strict types, server rendering and progressive enhancement.
- API and scanner code share Python's mature networking and security ecosystem without sharing runtime credentials.
- Two language toolchains add some maintenance cost, managed through narrow service contracts and automated checks.
- The API remains independently deployable from the scanner data plane.
- Dependencies must be pinned through lockfiles and continuously reviewed.

## Alternatives considered

- **NestJS for the API:** excellent full-stack TypeScript consistency, but weaker alignment with the planned scanner and security-analysis ecosystem for the initial team.
- **Django monolith:** productive for conventional CRUD, but encourages tighter coupling than desired between the control plane and scanning workflows.
- **Single Next.js application:** simplest deployment, but unsuitable as the execution boundary for outbound security checks.

## Validation and follow-up

Validate the choice through a vertical slice covering health, identity, tenant authorization, verified assets, signed jobs and immutable observations. Revisit if team expertise, performance evidence or operational data shows a material disadvantage.
