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
