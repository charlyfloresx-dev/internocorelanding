-- Migration: Create Investment Tables
CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    cve_cat VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    valor_terreno_2020 NUMERIC(15, 2),
    valor_const_2020 NUMERIC(15, 2),
    valor_terreno_2026 NUMERIC(15, 2),
    valor_const_2026 NUMERIC(15, 2),
    zona VARCHAR(100),
    lat NUMERIC(10, 7),
    lng NUMERIC(10, 7),
    last_rppc_sync TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS property_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id INTEGER REFERENCES properties(id),
    status VARCHAR(20) DEFAULT 'DETECTED',
    priority VARCHAR(10) DEFAULT 'MEDIUM',
    projected_roi NUMERIC(5, 2),
    assigned_to UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
