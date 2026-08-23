# KingaWeb Proof of Concept

This directory preserves the current dependency-free prototype. It demonstrates a small, bounded website posture check and the initial interface direction; it is not the production architecture.

## Run locally

Requirements: Python 3.10 or newer.

```bash
cd prototype
python3 server.py
```

Then open `http://127.0.0.1:8080`.

## Safety boundaries

Only enter a public website you own or are authorized to check. The server rejects local and private destinations, applies request limits and performs no exploitation, credential guessing or arbitrary port scanning.

Production work belongs in `apps/`, `services/` and `packages/`. Avoid expanding this prototype into the production platform.
