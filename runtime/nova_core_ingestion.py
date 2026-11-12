"""Server-only NeoCell -> NOVA Core observation transport.

No HTTP route is exposed here. Invoke only from trusted backend code after the
producer is authenticated and registered site/source/asset identifiers are
resolved. Cloudflare Access credentials must never reach the browser.
"""
from __future__ import annotations

import http.client
import json
import os
from typing import Any, Callable
from urllib.parse import urlsplit


MAX_REQUEST_BYTES = 32_768


import math
import re
from datetime import datetime, timedelta, timezone

EXPECTED_MODULE = "neocell"
MODULES = {"nova-core", "neoagro", "neogrid", "neocell"}
METHODS = {"sensor", "manual", "provider_api", "satellite", "model", "derived"}
QUALITY_FLAGS = {
    "estimated", "sensor_calibration_due", "sensor_fault", "outlier_suspected",
    "provider_fill_value", "manually_entered", "gridded_or_reanalysis", "time_alignment_uncertain",
}
TOP_LEVEL_KEYS = {
    "site_id", "asset_id", "source_id", "module", "metric", "value", "unit",
    "observed_at", "idempotency_key", "provenance", "quality_flags",
}
PROVENANCE_KEYS = {"provider", "acquisition_method", "source_record_ref"}
METRIC_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{0,119}$")
UNIT_PATTERN = re.compile(r"^[A-Za-z0-9%°µμ/._ -]{1,48}$")
RFC3339_PATTERN = re.compile(
    r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
)


def _required_string(value: Any, maximum: int, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value.strip() != value or len(value) > maximum:
        raise NovaCoreIngestionError("nova_core_invalid_" + field)


def _validate_observation_payload(payload: dict[str, Any]) -> None:
    """Mirror Core's v1 envelope checks; Core remains the authority."""
    if not isinstance(payload, dict) or not set(payload).issubset(TOP_LEVEL_KEYS):
        raise NovaCoreIngestionError("nova_core_invalid_payload_shape")
    for field in ("site_id", "source_id", "idempotency_key"):
        _required_string(payload.get(field), {"site_id": 120, "source_id": 120, "idempotency_key": 200}[field], field)
    if payload.get("asset_id") is not None:
        _required_string(payload["asset_id"], 120, "asset_id")
    if payload.get("module") != EXPECTED_MODULE or payload.get("module") not in MODULES:
        raise NovaCoreIngestionError("nova_core_invalid_module")
    metric = payload.get("metric")
    if not isinstance(metric, str) or not METRIC_PATTERN.fullmatch(metric):
        raise NovaCoreIngestionError("nova_core_invalid_metric")
    value = payload.get("value")
    try:
        finite_value = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        finite_value = False
    if not finite_value:
        raise NovaCoreIngestionError("nova_core_invalid_value")
    unit = payload.get("unit")
    if not isinstance(unit, str) or not UNIT_PATTERN.fullmatch(unit):
        raise NovaCoreIngestionError("nova_core_invalid_unit")
    observed_at = payload.get("observed_at")
    if not isinstance(observed_at, str) or not RFC3339_PATTERN.fullmatch(observed_at):
        raise NovaCoreIngestionError("nova_core_invalid_observed_at")
    try:
        parsed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timezone_required")
        if parsed > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError("future_timestamp")
    except ValueError as exc:
        raise NovaCoreIngestionError("nova_core_invalid_observed_at") from exc
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict) or not set(provenance).issubset(PROVENANCE_KEYS):
        raise NovaCoreIngestionError("nova_core_invalid_provenance")
    _required_string(provenance.get("provider"), 120, "provenance_provider")
    if provenance.get("acquisition_method") not in METHODS:
        raise NovaCoreIngestionError("nova_core_invalid_acquisition_method")
    if provenance.get("source_record_ref") is not None:
        _required_string(provenance["source_record_ref"], 240, "source_record_ref")
    flags = payload.get("quality_flags", [])
    if (
        not isinstance(flags, list)
        or len(flags) > 16
        or any(not isinstance(flag, str) or flag not in QUALITY_FLAGS for flag in flags)
        or len(set(flags)) != len(flags)
    ):
        raise NovaCoreIngestionError("nova_core_invalid_quality_flags")


class NovaCoreIngestionError(RuntimeError):
    def __init__(self, code: str, status: int | None = None) -> None:
        self.code = code
        self.status = status
        super().__init__(code if status is None else f"{code} (HTTP {status})")


def _configuration(environ: dict[str, str]) -> tuple[str, int, str, str, str]:
    endpoint = environ.get("NOVA_CORE_INGESTION_URL", "").strip()
    client_id = environ.get("NOVA_CORE_ACCESS_CLIENT_ID", "")
    client_secret = environ.get("NOVA_CORE_ACCESS_CLIENT_SECRET", "")
    if not endpoint or not client_id or not client_secret:
        raise NovaCoreIngestionError("nova_core_ingestion_not_configured")
    if any(char in client_id + client_secret for char in "\r\n"):
        raise NovaCoreIngestionError("nova_core_ingestion_credentials_invalid")
    try:
        parsed = urlsplit(endpoint)
        port = parsed.port or 443
    except ValueError as exc:
        raise NovaCoreIngestionError("nova_core_ingestion_endpoint_invalid") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path != "/api/v1/observations"
    ):
        raise NovaCoreIngestionError("nova_core_ingestion_endpoint_invalid")
    return parsed.hostname, port, parsed.path, client_id, client_secret


def submit_observation(
    payload: dict[str, Any],
    *,
    environ: dict[str, str] | None = None,
    connection_factory: Callable[..., Any] = http.client.HTTPSConnection,
) -> dict[str, Any]:
    """Send a prepared observation; Core remains authoritative for trust checks."""
    host, port, path, client_id, client_secret = _configuration(
        dict(os.environ if environ is None else environ)
    )
    _validate_observation_payload(payload)
    try:
        body = json.dumps(payload, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise NovaCoreIngestionError("nova_core_payload_invalid") from exc
    if len(body) > MAX_REQUEST_BYTES:
        raise NovaCoreIngestionError("nova_core_payload_too_large")
    connection = connection_factory(host, port, timeout=10)
    try:
        connection.request(
            "POST",
            path,
            body=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "CF-Access-Client-Id": client_id,
                "CF-Access-Client-Secret": client_secret,
            },
        )
        response = connection.getresponse()
        raw = response.read(16_385)
        if len(raw) > 16_384:
            raise NovaCoreIngestionError("nova_core_response_too_large", response.status)
        if response.status not in (200, 201):
            raise NovaCoreIngestionError("nova_core_ingestion_rejected", response.status)
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NovaCoreIngestionError("nova_core_response_invalid", response.status) from exc
        if not isinstance(result, dict) or result.get("accepted") is not True:
            raise NovaCoreIngestionError("nova_core_acceptance_unconfirmed", response.status)
        return result
    except NovaCoreIngestionError:
        raise
    except (OSError, TimeoutError, http.client.HTTPException) as exc:
        raise NovaCoreIngestionError("nova_core_ingestion_unavailable") from exc
    finally:
        connection.close()
