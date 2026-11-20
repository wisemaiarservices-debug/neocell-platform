import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const app = readFileSync(new URL('../src/main.tsx', import.meta.url), 'utf8');
const readme = readFileSync(new URL('../../../README.md', import.meta.url), 'utf8');

test('NeoCell app persistently distinguishes demo fixtures from connected infrastructure', () => {
  assert.match(app, /DEMO SCENARIO/);
  assert.match(app, /Deterministic synthetic fixtures only/);
  assert.match(app, /not live sensor, gateway, energy, water or edge telemetry/);
  assert.match(app, /no physical assets connected/);
  assert.match(app, /Health endpoint reachable · no telemetry validation/);
  assert.match(app, /Local deterministic fixtures/);
  assert.doesNotMatch(app, /API live/);
  assert.doesNotMatch(app, /SolarHub Agrivoltaic Demo Site/);
});

test('NeoCell views label readiness, sensors, deployment and reports as illustrative', () => {
  assert.match(app, /not a site assessment or safety certification/);
  assert.match(app, /no field sensors are connected/);
  assert.match(app, /no deployment has been provisioned or executed/);
  assert.match(app, /no live synchronization or asset-state ingestion/);
  assert.match(app, /not operational evidence, compliance certification or measured impact/);
  assert.match(app, /no dispatch, approval workflow or physical action is connected/);
});

test('NeoCell documentation does not confuse health reachability with Core or provider integration', () => {
  assert.match(readme, /health response establishes process reachability only/);
  assert.match(readme, /does not authenticate a tenant/);
  assert.match(readme, /contract reference, not proof/);
  assert.match(readme, /No NOVA Core\/private tenant-gateway integration is established/);
});
