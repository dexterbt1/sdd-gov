---
name: secure-coding
description: Apply a secure coding checklist to a change that touches input, auth, secrets, crypto, transport, or supply chain.
---

# Secure coding

Use this skill when the `security` module is active and the change touches a trust boundary.

## Checklist

- **Injection:** use a parameterized query or a safe API. Do not build a query from a string.
- **XSS:** escape output. Do not inject untrusted HTML. Use the framework sanitizer.
- **AuthN:** verify the credential on every protected route. Do not trust a client claim.
- **AuthZ:** check the scope: workspace, account, or global. Do not rely on a hidden control.
- **Secrets:** do not log, return, or commit a secret. Read it from the secret store.
- **Crypto:** use a vetted library and a current algorithm. Do not invent a scheme.
- **SSRF:** allowlist the host. Do not fetch an arbitrary URL.
- **Transport:** require TLS. Verify the certificate.
- **Logging:** log the actor, the action, and the target. Do not log the secret or the token.
- **Supply chain:** pin a version or a digest. Update the lock file. Run the scan.

## Rules

- A security claim needs a test or a command result.
- A new risk needs an owner and an expiry in `RISKS.md`.
- A missing control is a blocker, not a note.
