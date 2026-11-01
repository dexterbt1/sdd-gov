# Module: bands

## Purpose

Reserve a disjoint range of spec numbers for a parallel workstream.

## Enable

```yaml
modules: [bands]
bands_mode: report
bands_expires: 2026-12-31
bands_size: 10
```

## Reserve a band

```sh
sdd-gov/g reserve --size 10 --owner "platform team"
```

The command appends a `bands` entry to `governance/reservations.json`:

```json
{
  "reserved": [],
  "bands": [
    { "start": 264, "end": 273, "owner": "platform team" }
  ]
}
```

`next-id` skips every reserved band.

## Check

- A band has an integer start and end, with `start <= end`.
- A band is no larger than `bands_size`.
- A band has an owner.
- Bands do not overlap.
- A single reserved ID does not fall inside a band.
