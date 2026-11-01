# Module: security

## Purpose

Make the security posture, the trust boundary, and the supply chain explicit.

## Enable

```yaml
modules: [security]
security_mode: report
security_expires: 2026-12-31
security_level: P1
security_require_threat_model: true
security_controls: contracts/security/controls.json
security_lockfile: package-lock.json
security_sbom: sbom.json
security_require_image_digest: true
security_scans: [secret, sast, sca, iac, container]
```

## What it checks

- `security_level` is `P0` through `P4`.
- A spec with `trust_boundary: true` has `## Threat Model` and `## Security Impact`.
- The control registry, when set, gives each control an owner and a gate.
- The lock file and the SBOM, when set, exist.
- An image reference carries an `@sha256:` digest when `security_require_image_digest` is true.
- Every declared scan is one of `secret`, `sast`, `sca`, `iac`, or `container`.

The module does not run a scanner. Wire each scan into `PROJECT.md` `checks:` and
run `check --hooks`.

## Rules

- A missing declaration on a boundary-touching spec is an error.
- An invalid level or a missing control registry is `fatal`.
- A risk exception MUST keep an owner and an expiry in `RISKS.md`.
