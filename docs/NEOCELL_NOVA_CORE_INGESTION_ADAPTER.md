# NeoCell → NOVA Core server-side observation adapter

## Status

This PR adds a strict NOVA Core v1 transport helper and contract-conformance tests. It does not connect the NeoCell demo UI or producer loops, and it does not claim live telemetry.

## Trust boundary

- Invoke `runtime/nova_core_ingestion.py` only from trusted backend code after authenticating the producer and resolving registered site/source/asset identifiers.
- Keep Cloudflare Access service-token credentials in server-side secrets only. Never expose them through browser bundles, public environment variables, HTML, local storage, logs or client responses.
- The adapter validates the exact NOVA Core v1 envelope, bounds request/response sizes, uses HTTPS, applies a timeout and normalizes upstream errors.
- Ingestion requires explicit opt-in with `NOVA_CORE_INGESTION_ENABLED=true`; the environment example defaults to `false`.
- The producer must not send `tenant_id`. NOVA Core derives tenant ownership from the active registered site/source/asset records and writes the observation and audit event under that tenant.
- Synthetic/demo values must never be forwarded as observations. Accepted records remain `unverified` until independently reviewed.

## Server environment

- `NOVA_CORE_INGESTION_ENABLED`: keep `false` until all activation gates pass.
- `NOVA_CORE_INGESTION_URL`: exact HTTPS URL ending in `/api/v1/observations` on a dedicated Access-protected custom hostname. Public `workers.dev` and preview URLs are disabled for the ingestion Worker.
- `NOVA_CORE_ACCESS_CLIENT_ID`: Cloudflare Access service-token client ID.
- `NOVA_CORE_ACCESS_CLIENT_SECRET`: Cloudflare Access service-token secret.

All credentials are blank in the example. Missing configuration or disabled opt-in fails closed. No browser route is provided by this helper.

## Activation gates

1. Deploy the tenant-aware NOVA Core ingestion Worker only after account plan/quota review; keep `workers_dev=false` and `preview_urls=false`.
2. Provision D1 and apply the ordered migrations `0001_initial.sql` through `0004_tenant_ownership_immutability.sql`; bind it as `DB`.
3. Create a dedicated custom hostname and Cloudflare Access Service Auth policy restricted to the intended service identity.
4. Register real NeoCell site, gateways, devices, cells and registered sensor sources; never reuse demo IDs.
5. Configure exact service → module → source grants and store the service token only in the trusted backend runtime.
6. Add an authenticated producer workflow with rate limits, idempotency and monitoring; do not enable the flag before this exists.
7. Run live acceptance tests for valid ingestion, wrong source/module, unknown or cross-tenant ownership, disabled source, retries, changed-payload conflict and D1 outage.

## Current limitation

The helper is not called by an active producer path. No D1, Access application/policy, credentials, source records, custom hostname, Worker deployment or live ingestion has been provisioned. CI verifies the adapter contract and module build only.