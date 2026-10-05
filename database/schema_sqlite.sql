-- ============================================================================
-- City Bus Route Optimization Analyzer - SQLite Schema
-- ============================================================================

PRAGMA foreign_keys = ON;

-- 1. Bus Stops
CREATE TABLE IF NOT EXISTS bus_stops (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stop_code       TEXT    NOT NULL UNIQUE,
    name            TEXT    NOT NULL,
    latitude        REAL    NOT NULL,
    longitude       REAL    NOT NULL,
    zone            TEXT    DEFAULT 'A',
    is_terminal     INTEGER DEFAULT 0,
    passenger_load  INTEGER DEFAULT 50
);

-- 2. Bus Routes
CREATE TABLE IF NOT EXISTS bus_routes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    route_code      TEXT    NOT NULL UNIQUE,
    name            TEXT    NOT NULL,
    frequency       INTEGER DEFAULT 10,   -- buses per hour
    capacity        INTEGER DEFAULT 60,   -- passenger capacity per bus
    status          TEXT    DEFAULT 'ACTIVE'
);

-- Compatibility View
CREATE VIEW IF NOT EXISTS routes AS SELECT * FROM bus_routes;

-- 3. Route Stops Sequence
CREATE TABLE IF NOT EXISTS route_stops (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id        INTEGER NOT NULL REFERENCES bus_routes(id) ON DELETE CASCADE,
    stop_id         INTEGER NOT NULL REFERENCES bus_stops(id) ON DELETE CASCADE,
    stop_order      INTEGER NOT NULL DEFAULT 1,
    UNIQUE(route_id, stop_order)
);

-- 4. Route Edges (Graph Adjacency Links)
CREATE TABLE IF NOT EXISTS route_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id        INTEGER NOT NULL REFERENCES bus_routes(id) ON DELETE CASCADE,
    from_stop_id    INTEGER NOT NULL REFERENCES bus_stops(id) ON DELETE CASCADE,
    to_stop_id      INTEGER NOT NULL REFERENCES bus_stops(id) ON DELETE CASCADE,
    distance_km     REAL    NOT NULL,
    travel_time_min REAL    NOT NULL,
    fare            REAL    NOT NULL,
    congestion      REAL    DEFAULT 1.0,  -- 1.0 = normal, >1 = congested
    sequence_order  INTEGER DEFAULT 0
);

-- 5. Buses (Fleet Management)
CREATE TABLE IF NOT EXISTS buses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_number      TEXT    NOT NULL UNIQUE,
    route_id        INTEGER REFERENCES bus_routes(id) ON DELETE SET NULL,
    model           TEXT    NOT NULL DEFAULT 'Tata Starbus Ultra',
    capacity        INTEGER NOT NULL DEFAULT 60,
    status          TEXT    NOT NULL DEFAULT 'ON_ROUTE', -- ON_ROUTE, IDLE, MAINTENANCE
    current_load    INTEGER DEFAULT 0,
    driver_name     TEXT    DEFAULT 'K. Murugan',
    last_maintenance TEXT   DEFAULT '2026-09-15'
);

-- 6. Passenger Demand Data
CREATE TABLE IF NOT EXISTS demand_data (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stop_id         INTEGER NOT NULL REFERENCES bus_stops(id) ON DELETE CASCADE,
    hour_of_day     INTEGER NOT NULL, -- 0-23
    passenger_count INTEGER NOT NULL DEFAULT 0,
    boardings       INTEGER NOT NULL DEFAULT 0,
    alightings      INTEGER NOT NULL DEFAULT 0,
    day_of_week     TEXT    DEFAULT 'WEEKDAY'
);

-- 7. Congestion Telemetry Data
CREATE TABLE IF NOT EXISTS congestion_data (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    edge_id           INTEGER NOT NULL REFERENCES route_edges(id) ON DELETE CASCADE,
    hour_of_day       INTEGER NOT NULL, -- 0-23
    congestion_factor REAL    NOT NULL DEFAULT 1.0,
    avg_speed_kmh     REAL    NOT NULL DEFAULT 25.0,
    timestamp         TEXT    DEFAULT CURRENT_TIMESTAMP
);

-- 8. Optimization History Runs
CREATE TABLE IF NOT EXISTS optimization_runs (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    from_stop_id         INTEGER NOT NULL REFERENCES bus_stops(id),
    to_stop_id           INTEGER NOT NULL REFERENCES bus_stops(id),
    mode                 TEXT    NOT NULL DEFAULT 'balanced',
    algorithm            TEXT    NOT NULL DEFAULT 'astar',
    optimization_time_ms REAL    NOT NULL DEFAULT 0.0,
    score                REAL    NOT NULL DEFAULT 0.0,
    created_at           TEXT    DEFAULT CURRENT_TIMESTAMP
);

-- 9. Optimization Results
CREATE TABLE IF NOT EXISTS optimization_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES optimization_runs(id) ON DELETE CASCADE,
    rank            INTEGER NOT NULL DEFAULT 1,
    cost            REAL    NOT NULL,
    distance_km     REAL    NOT NULL,
    time_min        REAL    NOT NULL,
    fare            REAL    NOT NULL,
    transfers       INTEGER NOT NULL DEFAULT 0,
    num_stops       INTEGER NOT NULL DEFAULT 0,
    route_path      TEXT    NOT NULL,
    score           REAL    NOT NULL DEFAULT 0.0
);

-- Indexes for Rapid Querying
CREATE INDEX IF NOT EXISTS idx_edges_from ON route_edges(from_stop_id);
CREATE INDEX IF NOT EXISTS idx_edges_to   ON route_edges(to_stop_id);
CREATE INDEX IF NOT EXISTS idx_edges_route ON route_edges(route_id);
CREATE INDEX IF NOT EXISTS idx_demand_stop ON demand_data(stop_id, hour_of_day);
CREATE INDEX IF NOT EXISTS idx_congestion_edge ON congestion_data(edge_id, hour_of_day);
CREATE INDEX IF NOT EXISTS idx_buses_route ON buses(route_id);
CREATE INDEX IF NOT EXISTS idx_opt_runs ON optimization_runs(created_at);
