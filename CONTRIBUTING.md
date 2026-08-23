# Contributing to KingaWeb

Thank you for helping build KingaWeb responsibly. Security software earns trust through careful engineering, clear evidence and respect for authorization.

## Before you begin

- Read the [security policy](SECURITY.md) and [architecture overview](docs/architecture/README.md).
- Open or join an issue before making a substantial product or architecture change.
- Never test KingaWeb against an asset you do not own or have explicit permission to assess.
- Never include real credentials, customer data, unredacted scan evidence or personal information in commits.

## Development workflow

1. Create a branch from `main`: `feature/<short-name>`, `fix/<short-name>` or `docs/<short-name>`.
2. Keep each change focused and document any security assumptions.
3. Add or update tests for changed behavior.
4. Run the relevant formatting, linting, type-checking and test commands.
5. Update documentation, contracts and the changelog when behavior changes.
6. Open a pull request using the repository template.

Use clear commit messages, preferably following Conventional Commits, for example:

```text
feat(scanner): add bounded TLS certificate observation
fix(api): enforce workspace ownership on finding lookup
docs(adr): record queue signing decision
```

## Definition of done

A change is complete when:

- its acceptance criteria are met;
- automated tests cover normal, failure and authorization paths;
- logs contain no secrets or unnecessary sensitive data;
- accessibility and mobile behavior have been considered;
- telemetry and operational failure handling are defined;
- public interfaces and security decisions are documented;
- the pull request has received the required review.

## Scanner-specific rules

Scanner changes require additional care:

- Verify target authorization before performing checks.
- Revalidate resolved destinations and reject loopback, private, link-local and metadata endpoints.
- Apply strict connection, response-size, redirect and concurrency limits.
- Keep checks non-destructive and record the rule/check version with every observation.
- Separate raw observations from findings and never let AI-generated text become scan evidence.
- Add abuse-case and denial-of-service tests for material changes.

## Architecture decisions

Create an Architecture Decision Record (ADR) for choices that affect trust boundaries, data handling, public contracts, infrastructure, dependencies or long-term maintainability. Copy [`docs/architecture/decisions/0000-template.md`](docs/architecture/decisions/0000-template.md) and use the next available number.

## Reporting vulnerabilities

Do not open a public issue for a vulnerability. Follow [`SECURITY.md`](SECURITY.md). A private reporting address will be published before the public beta; until then, retain sensitive details and contact the repository owner through a private channel.
