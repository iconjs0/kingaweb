# Architecture Overview

KingaWeb is designed as a multi-tenant software-as-a-service platform with strict separation between customer workflows and security-check execution.

## Trust zones

1. **User zone:** browser/PWA and untrusted client input.
2. **Control plane:** identity, workspaces, assets, findings, reports and policy enforcement.
3. **Job boundary:** signed, versioned scan requests with explicit authorization and limits.
4. **Scanning data plane:** isolated workers with controlled network egress and no customer-session credentials.
5. **Evidence zone:** immutable raw observations, normalized results and audit records.
6. **Intelligence zone:** deterministic rules and evidence-grounded AI assistance.

## Core invariants

- Every request and object is scoped to a workspace.
- Recurring or expanded checks require verified target control.
- DNS and redirect destinations are validated immediately before connection.
- Workers receive short-lived, least-privilege credentials.
- Raw observations are preserved separately from derived findings.
- Every finding records its rule and check versions.
- AI output is labelled, traceable to evidence and never treated as scan proof.
- High-impact or state-changing actions require deterministic authorization and human approval.
- Sensitive values are minimized, encrypted, access-controlled and never written to ordinary logs.

## Decision records

Material decisions are documented in [`decisions/`](decisions/). Accepted ADRs are immutable; changed decisions are superseded by a new record.
