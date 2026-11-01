# Project-owned writer role

The core has four roles: author, builder, reviewer, qa. This example adds a writer
role and a product-docs skill for a project that needs customer-facing
documentation.

Copy the files into your harness, then record the mapping in `sdd-gov/PROJECT.md`
under `## Agent map`. The core does not enforce this role. It is a reference, not a
core opinion.

The source clone stays in `.local/tmp`. Do not copy these files into
`sdd-gov/governance/`; that directory is the vendored core and an upgrade replaces
it.
