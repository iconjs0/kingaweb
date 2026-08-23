# KingaWeb Delivery Roadmap

This roadmap is gate-based rather than date-driven. A phase advances only when its evidence and safety conditions are satisfied.

## Phase 0 — Discovery

- [ ] Interview at least 15 Tanzanian businesses and digital agencies.
- [ ] Confirm the first paying segment and top three recurring security pains.
- [ ] Recruit one design partner with explicitly authorized test assets.
- [ ] Validate English/Kiswahili terminology and mobile reporting needs.
- [ ] Test pricing and support expectations.

**Exit gate:** repeated customer evidence supports the problem, buyer, workflow and willingness to pay.

## Phase 1 — Engineering foundation

- [ ] Approve the API/backend architecture ADR.
- [ ] Establish web, API, scanner and contract workspaces.
- [ ] Implement CI quality and security checks.
- [ ] Complete threat modelling and scanner abuse cases.
- [ ] Implement managed identity, MFA and tenant authorization tests.
- [ ] Create isolated scanner workers and signed job contracts.
- [ ] Add structured telemetry, audit events and secret management.

**Exit gate:** a reviewed vertical slice can safely accept an authorized target, schedule a bounded check and store an immutable observation.

## Phase 2 — Private MVP

- [ ] Domain ownership verification.
- [ ] HTTPS/TLS, header, cookie, DNS and email-posture observations.
- [ ] Versioned rules that convert observations into explainable findings.
- [ ] Finding lifecycle, ownership, notes and verified rescans.
- [ ] Workspace roles and complete audit trail.
- [ ] Responsive dashboard with accessible mobile journeys.

**Exit gate:** the design partner resolves a real finding and KingaWeb proves the remediation using preserved evidence.

## Phase 3 — Private beta

- [ ] Scheduled monitoring and change detection.
- [ ] Alert preferences, deduplication and escalation.
- [ ] Agency portfolios and delegated client access.
- [ ] Exportable executive and technical reports.
- [ ] English/Kiswahili content quality review.
- [ ] AI summaries and remediation guidance with evidence citations.
- [ ] Operational runbooks, backup restoration and incident exercises.

**Exit gate:** invited customers receive useful alerts with acceptable false-positive rates and operations meet defined service targets.

## Phase 4 — Public V1

- [ ] Subscriptions, invoicing and entitlements.
- [ ] Onboarding, support and in-product feedback workflows.
- [ ] Trust centre, privacy terms and coordinated disclosure channel.
- [ ] Capacity, isolation and disaster-recovery validation.
- [ ] Release signing, rollback and change-management controls.

**Exit gate:** security, product, support and commercial readiness reviews are approved.

## Phase 5 — Continuous development

- [ ] Additional external attack-surface signals.
- [ ] Domain impersonation and certificate-transparency monitoring.
- [ ] Context-aware correlation and anomaly detection.
- [ ] Ticketing, messaging and managed-service integrations.
- [ ] Regional localization, data-residency options and partner channels.
- [ ] Public API and automation after authorization controls mature.

Every release must publish measurable outcomes, reliability evidence, security review results and known limitations.
