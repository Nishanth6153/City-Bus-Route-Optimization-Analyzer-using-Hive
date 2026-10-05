-- ============================================================================
-- City Bus Route Optimization Analyzer - PostgreSQL / PostGIS Schema
-- ============================================================================

-- Enable PostGIS spatial extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Bus Stops (with PostGIS Point Geometry)
CREATE TABLE IF NOT EXISTS bus_stops (
    id              SERIAL PRIMARY KEY,
    stop_code       VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(120) NOT NULL,
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    geom            GEOMETRY(Point, 4326),
    zone            VARCHAR(10) DEFAULT 'A',
    is_terminal     INTEGER DEFAULT 0,
    passenger_load  INTEGER DEFAULT 50
);

-- Trigger to auto-populate geom from lat/lon
CREATE OR REPLACE FUNCTION update_bus_stop_geom()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_bus_stop_geom ON bus_stops;
CREATE TRIGGER trg_bus_stop_geom
BEFORE INSERT OR UPDATE ON bus_stops
FOR EACH ROW EXECUTE FUNCTION update_bus_stop_geom();

-- 2. Bus Routes
CREATE TABLE IF NOT EXISTS bus_routes (
    id          SERIAL PRIMARY KEY,
    route_code  VARCHAR(20) NOT NULL UNIQUE,
    name        VARCHAR(150) NOT NULL,
    frequency   INTEGER DEFAULT 10,   -- buses per hour
    capacity    INTEGER DEFAULT 60,   -- passenger capacity
    status      VARCHAR(20) DEFAULT 'ACTIVE'
);

CREATE OR REPLACE VIEW routes AS SELECT * FROM bus_routes;

-- 3. Route Stops Sequence
CREATE TABLE IF NOT EXISTS route_stops (
    id          SERIAL PRIMARY KEY,
    route_id    INTEGER NOT NULL REFERENCES bus_routes(id) ON DELETE CASCADE,
    stop_id     INTEGER NOT NULL REFERENCES bus_stops(id) ON DELETE CASCADE,
    stop_order  INTEGER NOT NULL DEFAULT 1,
    UNIQUE(route_id, stop_order)
);

-- 4. Route Edges (with PostGIS LineString Geometry)
CREATE TABLE IF NOT EXISTS route_edges (
    id              SERIAL PRIMARY KEY,
    route_id        INTEGER NOT NULL REFERENCES bus_routes(id) ON DELETE CASCADE,
    from_stop_id    INTEGER NOT NULL REFERENCES bus_stops(id) ON DELETE CASCADE,
    to_stop_id      INTEGER NOT NULL REFERENCES bus_stops(id) ON DELETE CASCADE,
    distance_km     DOUBLE PRECISION NOT NULL,
    travel_time_min DOUBLE PRECISION NOT NULL,
    fare            DOUBLE PRECISION NOT NULL,
    congestion      DOUBLE PRECISION DEFAULT 1.0,
    sequence_order  INTEGER DEFAULT 0,
    edge_geom       GEOMETRY(LineString, 4326)
);

-- 5. Fleet Vehicles
CREATE TABLE IF NOT EXISTS buses (
    id              SERIAL PRIMARY KEY,
    bus_number      VARCHAR(30) NOT NULL UNIQUE,
    route_id        INTEGER REFERENCES bus_routes(id) ON DELETE SET NULL,
    model           VARCHAR(80) NOT NULL DEFAULT 'Tata Starbus Ultra',
    capacity        INTEGER NOT NULL DEFAULT 60,
    status          VARCHAR(20) NOT NULL DEFAULT 'ON_ROUTE',
    current_load    INTEGER DEFAULT 0,
    driver_name     VARCHAR(80) DEFAULT 'K. Murugan',
    last_maintenance DATE DEFAULT '2026-09-15'
);

-- 6. Demand Telemetry
CREATE TABLE IF NOT EXISTS demand_data (
    id              SERIAL PRIMARY KEY,
    stop_id         INTEGER NOT NULL REFERENCES bus_stops(id) ON DELETE CASCADE,
    hour_of_day     INTEGER NOT NULL,
    passenger_count INTEGER NOT NULL DEFAULT 0,
    boardings       INTEGER NOT NULL DEFAULT 0,
    alightings      INTEGER NOT NULL DEFAULT 0,
    day_of_week     VARCHAR(20) DEFAULT 'WEEKDAY'
);

-- 7. Congestion Telemetry
CREATE TABLE IF NOT EXISTS congestion_data (
    id                SERIAL PRIMARY KEY,
    edge_id           INTEGER NOT NULL REFERENCES route_edges(id) ON DELETE CASCADE,
    hour_of_day       INTEGER NOT NULL,
    congestion_factor DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    avg_speed_kmh     DOUBLE PRECISION NOT NULL DEFAULT 25.0,
    timestamp         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Optimization Runs
CREATE TABLE IF NOT EXISTS optimization_runs (
    id                   SERIAL PRIMARY KEY,
    from_stop_id         INTEGER NOT NULL REFERENCES bus_stops(id),
    to_stop_id           INTEGER NOT NULL REFERENCES bus_stops(id),
    mode                 VARCHAR(30) NOT NULL DEFAULT 'balanced',
    algorithm            VARCHAR(30) NOT NULL DEFAULT 'astar',
    optimization_time_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    score                DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Optimization Results
CREATE TABLE IF NOT EXISTS optimization_results (
    id              SERIAL PRIMARY KEY,
    run_id          INTEGER NOT NULL REFERENCES optimization_runs(id) ON DELETE CASCADE,
    rank            INTEGER NOT NULL DEFAULT 1,
    cost            DOUBLE PRECISION NOT NULL,
    distance_km     DOUBLE PRECISION NOT NULL,
    time_min        DOUBLE PRECISION NOT NULL,
    fare            DOUBLE PRECISION NOT NULL,
    transfers       INTEGER NOT NULL DEFAULT 0,
    num_stops       INTEGER NOT NULL DEFAULT 0,
    route_path      TEXT NOT NULL,
    score           DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

-- PostGIS Spatial & B-Tree Indexes
CREATE INDEX IF NOT EXISTS idx_stops_geom ON bus_stops USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_edges_geom ON route_edges USING GIST(edge_geom);
CREATE INDEX IF NOT EXISTS idx_edges_from ON route_edges(from_stop_id);
CREATE INDEX IF NOT EXISTS idx_edges_to   ON route_edges(to_stop_id);
CREATE INDEX IF NOT EXISTS idx_edges_route ON route_edges(route_id);
CREATE INDEX IF NOT EXISTS idx_demand_stop ON demand_data(stop_id, hour_of_day);
CREATE INDEX IF NOT EXISTS idx_buses_route ON buses(route_id);
