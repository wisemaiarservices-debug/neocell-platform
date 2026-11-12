import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nova_core_ingestion import NovaCoreIngestionError, submit_observation


class FakeResponse:
    def __init__(self, status=201, body=b'{"accepted":true,"verification_status":"unverified"}'):
        self.status, self.body = status, body

    def read(self, size=-1):
        return self.body[:size]


class FakeConnection:
    last = None

    def __init__(self, host, port, timeout):
        self.host, self.port, self.timeout = host, port, timeout
        self.closed = False
        self.request_args = None
        FakeConnection.last = self

    def request(self, method, path, body, headers):
        self.request_args = (method, path, body, headers)

    def getresponse(self):
        return FakeResponse()

    def close(self):
        self.closed = True


class RejectedConnection(FakeConnection):
    def getresponse(self):
        return FakeResponse(403, b'{"error":"request_not_authorized"}')


class NeoCellIngestionTests(unittest.TestCase):
    def setUp(self):
        self.env = {
            "NOVA_CORE_INGESTION_ENABLED": "true",
            "NOVA_CORE_INGESTION_ENABLED": "true",
            "NOVA_CORE_INGESTION_URL": "https://nova-core-ingest.example.workers.dev/api/v1/observations",
            "NOVA_CORE_ACCESS_CLIENT_ID": "cell-client-id",
            "NOVA_CORE_ACCESS_CLIENT_SECRET": "cell-client-secret",
        }
        self.payload = {
            "site_id": "registered-cell-site",
            "asset_id": "gateway-001",
            "source_id": "neocell-gateway-01",
            "module": "neocell",
            "metric": "infrastructure.gateway_temperature",
            "value": 31.2,
            "unit": "°C",
            "observed_at": "2026-11-10T12:00:00Z",
            "idempotency_key": "gateway-event-0001",
            "provenance": {"provider": "registered-edge-gateway", "acquisition_method": "sensor"},
            "quality_flags": [],
        }

    def test_posts_with_server_side_access_headers(self):
        result = submit_observation(self.payload, environ=self.env, connection_factory=FakeConnection)
        method, path, body, headers = FakeConnection.last.request_args
        self.assertEqual((method, path), ("POST", "/api/v1/observations"))
        self.assertEqual(headers["CF-Access-Client-Id"], "cell-client-id")
        self.assertEqual(headers["CF-Access-Client-Secret"], "cell-client-secret")
        self.assertNotIn("cell-client-secret", body.decode())
        self.assertEqual(result["verification_status"], "unverified")
        self.assertTrue(FakeConnection.last.closed)

    def test_rejects_non_object_non_finite_and_oversized_payloads(self):
        for invalid in ([], {"value": float("nan")}, {"value": "x" * 33_000}):
            with self.subTest(payload_type=type(invalid).__name__), self.assertRaises(NovaCoreIngestionError):
                submit_observation(invalid, environ=self.env, connection_factory=FakeConnection)

    def test_core_v1_envelope_is_validated_before_network_request(self):
        invalid_payloads = (
            dict(self.payload, module="another-module"),
            dict(self.payload, module=[]),
            dict(self.payload, metric="Invalid Metric"),
            dict(self.payload, unit=""),
            dict(self.payload, observed_at="2026-11-10T12:00:00"),
            dict(self.payload, observed_at="2099-11-10T12:00:00Z"),
            dict(self.payload, value=True),
            dict(self.payload, idempotency_key=""),
            dict(self.payload, unexpected_field="not-accepted"),
            dict(self.payload, provenance={"provider": "test", "acquisition_method": "sensor", "secret": "no"}),
            dict(self.payload, provenance={"provider": "test", "acquisition_method": []}),
            dict(self.payload, quality_flags=["unknown_flag"]),
        )
        for invalid in invalid_payloads:
            with self.subTest(payload=invalid), self.assertRaises(NovaCoreIngestionError):
                submit_observation(invalid, environ=self.env, connection_factory=FakeConnection)

    def test_ingestion_disabled_without_explicit_opt_in(self):
        FakeConnection.last = None
        env = dict(self.env, NOVA_CORE_INGESTION_ENABLED="false")
        with self.assertRaisesRegex(NovaCoreIngestionError, "ingestion_disabled"):
            submit_observation(self.payload, environ=env, connection_factory=FakeConnection)
        self.assertIsNone(FakeConnection.last)

    def test_ingestion_disabled_without_explicit_opt_in(self):
        FakeConnection.last = None
        env = dict(self.env, NOVA_CORE_INGESTION_ENABLED="false")
        with self.assertRaisesRegex(NovaCoreIngestionError, "ingestion_disabled"):
            submit_observation(self.payload, environ=env, connection_factory=FakeConnection)
        self.assertIsNone(FakeConnection.last)

    def test_missing_credentials_fail_closed(self):
        env = dict(self.env)
        env.pop("NOVA_CORE_ACCESS_CLIENT_SECRET")
        with self.assertRaisesRegex(NovaCoreIngestionError, "not_configured"):
            submit_observation(self.payload, environ=env, connection_factory=FakeConnection)

    def test_rejects_invalid_endpoint_and_header_injection(self):
        for endpoint in (
            "http://nova-core.example/api/v1/observations",
            "https://nova-core.example/other",
            "https://nova-core.example/api/v1/observations?x=1",
            "https://nova-core.example:99999/api/v1/observations",
        ):
            with self.subTest(endpoint=endpoint), self.assertRaises(NovaCoreIngestionError):
                submit_observation(self.payload, environ=dict(self.env, NOVA_CORE_INGESTION_URL=endpoint),
                                   connection_factory=FakeConnection)
        with self.assertRaisesRegex(NovaCoreIngestionError, "credentials_invalid"):
            submit_observation(self.payload, environ=dict(self.env, NOVA_CORE_ACCESS_CLIENT_ID="cell\r\nX: y"),
                               connection_factory=FakeConnection)

    def test_rejected_request_does_not_echo_upstream_body(self):
        with self.assertRaises(NovaCoreIngestionError) as caught:
            submit_observation(self.payload, environ=self.env, connection_factory=RejectedConnection)
        self.assertEqual(caught.exception.status, 403)
        self.assertNotIn("cell-client-secret", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
