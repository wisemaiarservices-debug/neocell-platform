# NeoCell → NOVA Core server-side ingestion adapter

## Status

This is a transport helper and mock-transport test suite only. It is not called
by the current NeoCell demo runtime and does not imply that device/gateway
telemetry is connected.

## Trust boundary

- Invoke \`runtime/nova_core_ingestion.py\` only from trusted backend code after
  authenticating the producer and resolving registered site/source/asset IDs.
- Keep Cloudflare Access credentials in server-only runtime secrets. Never use
  \`NEXT_PUBLIC_\`, browser storage, HTML or client responses.
- NOVA Core remains authoritative for Access JWT verification, service/module/
  source grants, payload validation, ownership, idempotency, audit records and
  server-assigned \`unverified\` status.
- Synthetic demo values must never be forwarded as observations.

## Server environment

- \`NOVA_CORE_INGESTION_URL\`: exact HTTPS URL ending in \`/api/v1/observations\`
- \`NOVA_CORE_ACCESS_CLIENT_ID\`: Cloudflare Access service-token client ID
- \`NOVA_CORE_ACCESS_CLIENT_SECRET\`: Cloudflare Access service-token secret

All values are intentionally blank in the example. Missing configuration fails
closed. The client does not follow redirects, limits response size, and avoids
logging or returning upstream response bodies.

## Enablement gates

1. Deploy the isolated NOVA Core ingestion Worker and configure Cloudflare Access
   Service Auth on its dedicated hostname.
2. Provision D1, apply the reviewed migration and bind it as \`DB\`.
3. Register actual NeoCell sites, gateways, devices, assets and source IDs.
4. Grant each producer only \`neocell\` and its exact registered source IDs.
5. Store service credentials only in the protected backend runtime.
6. Implement an authenticated producer path with rate limits and monitoring.
7. Run live acceptance tests for authorization, ownership, idempotency, conflict
   and storage outage behavior.

Until those gates pass, this is an unconfigured integration foundation. No
production behavior or public endpoint is changed.

## Client-side envelope preflight

The transport helper mirrors NOVA Core's current v1 observation envelope checks before opening a network connection:

- Exact allowlisted top-level and provenance keys; required site, source and idempotency identifiers.
- Module is fixed to this adapter's own module identifier.
- Finite numeric value, bounded metric/unit strings and timezone-qualified RFC 3339 observation timestamp (not more than five minutes in the future).
- Allowlisted acquisition method and quality flags; bounded provenance fields.
- Bounded serialized request body; no credentials in the payload.

This is an early rejection layer, not an authorization or verification mechanism. Core revalidates every request and alone assigns persistence and verification status. Keep this mirror aligned with apps/ingestion-worker/src/observation-contract.mjs in NOVA Core when the contract changes.


## Forward compatibility: measurement quality and calibration v2

NOVA Core has a design-only proposal for structured device, sampling, calibration-evidence, uncertainty, method/version and spatial-support metadata in `NOVA_CORE_MEASUREMENT_QUALITY_CALIBRATION_V2_PROPOSAL.md`. This proposal is not accepted by the current v1 endpoint. This adapter intentionally sends only the strict v1 envelope; do not add proposed fields or infer missing calibration/device metadata until a separately versioned Core endpoint and migration are approved and implemented. A successful v1 submission remains unverified and is not evidence of calibration or scientific eligibility.
