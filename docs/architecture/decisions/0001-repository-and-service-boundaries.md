# ADR-0001: Repository and service boundaries

- **Status:** Accepted
- **Date:** 2026-08-23
- **Owners:** KingaWeb maintainers

## Context

KingaWeb needs shared contracts and coordinated releases while maintaining a strong security boundary between its internet-facing control plane and outbound scanner workers. The project is early enough that independent repositories would add operational overhead without creating meaningful isolation by themselves.

## Decision

Use a monorepo with explicit ownership boundaries:

- `apps/web` for the customer-facing web application;
- `services/api` for control-plane APIs and authorization;
- `services/scanner` for isolated security-check workers;
- `packages/contracts` for versioned API and event schemas;
- `infra` for reviewed infrastructure definitions;
- `prototype` for the preserved, non-production proof of concept.

Runtime isolation, credentials, network policy and deployment permissions—not the repository layout—will enforce production trust boundaries.

## Consequences

- Shared contracts can evolve atomically with consumers.
- CI can test cross-component changes before merging.
- Repository permissions alone must never be treated as runtime isolation.
- Build and deployment pipelines must target components independently.
- Code ownership and change review should become stricter as the contributor base grows.

## Alternatives considered

- **Separate repositories:** stronger administrative separation, but excessive coordination and release overhead at this stage.
- **Single deployable application:** simpler initially, but creates unacceptable coupling between customer sessions and outbound scanning.

## Validation and follow-up

Revisit this decision if independent teams, regulatory boundaries or release cadences make separate repositories materially safer or easier to operate.
