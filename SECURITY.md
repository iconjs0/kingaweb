# Security Policy

## Current status

KingaWeb is currently **pre-alpha**. It must not be treated as a production security control, compliance guarantee or substitute for professional incident response.

## Reporting a vulnerability

Please do not disclose vulnerabilities through public issues, discussions, social media or demonstrations against third-party systems.

A dedicated security reporting address and encrypted channel will be published before private beta. Until then:

1. Retain the technical details and proof of concept privately.
2. Contact the repository owner through a private, established channel.
3. Include the affected component/version, impact, safe reproduction steps and suggested remediation if known.
4. Remove credentials, personal data and unrelated customer information.

We intend to acknowledge valid reports promptly, communicate remediation progress and credit researchers when requested. Formal response targets will be published before public availability.

## Authorization and safe research

Only assess systems you own or are explicitly authorized to test. Good-faith research must:

- avoid privacy violations, data destruction and service degradation;
- use the minimum access needed to demonstrate impact;
- stop when sensitive data is encountered;
- avoid persistence, credential guessing, social engineering and supply-chain interference;
- give the project reasonable time to investigate and remediate before disclosure.

No statement in this file grants authorization to test third-party infrastructure.

## Product safety boundaries

KingaWeb is designed for bounded, defensive external monitoring. It does not authorize exploit execution, credential attacks, arbitrary port scanning or destructive testing. Production scanning will require verified control of targets and enforce destination, rate, timeout, redirect and response-size controls.

AI features may summarize and prioritize verified observations, but must not create evidence, bypass authorization or autonomously execute high-impact actions.

## Planned production baseline

Before public release, the project will establish:

- a threat model and abuse-case review;
- mandatory MFA and least-privilege access;
- tenant-isolation and authorization tests;
- dependency, secret, static-analysis and container scanning;
- signed build artifacts and controlled deployments;
- encryption, retention and deletion policies;
- audit logging, alerting, backups and restoration exercises;
- incident response and coordinated disclosure procedures.
