-- NeoCell Schema v1

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS neocell_deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    deployment_name TEXT NOT NULL,
    deployment_class TEXT NOT NULL,
    variant TEXT NOT NULL,
    status TEXT DEFAULT 'planned',
    installed_at TIMESTAMPTZ,
    commissioned_at TIMESTAMPTZ,
    location GEOMETRY(POINT, 4326),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS infrastructure_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
    deployment_id UUID REFERENCES neocell_deployments(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,
    module_type TEXT NOT NULL,
    module_name TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    health_score NUMERIC,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS edge_gateways (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    deployment_id UUID REFERENCES neocell_deployments(id) ON DELETE CASCADE,
    gateway_name TEXT NOT NULL,
    connection_status TEXT DEFAULT 'unknown',
    last_seen TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sensor_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    deployment_id UUID REFERENCES neocell_deployments(id) ON DELETE CASCADE,
    gateway_id UUID REFERENCES edge_gateways(id) ON DELETE SET NULL,
    node_name TEXT NOT NULL,
    node_type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    battery_level_pct NUMERIC,
    signal_strength NUMERIC,
    last_seen TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS maintenance_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
    deployment_id UUID REFERENCES neocell_deployments(id) ON DELETE SET NULL,
    module_id UUID REFERENCES infrastructure_modules(id) ON DELETE SET NULL,
    gateway_id UUID REFERENCES edge_gateways(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    severity TEXT DEFAULT 'medium',
    description TEXT,
    status TEXT DEFAULT 'open',
    scheduled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);
