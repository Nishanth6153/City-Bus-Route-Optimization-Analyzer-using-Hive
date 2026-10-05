# Database Schema & Data Model

The platform utilizes a relational transit network schema compatible with both SQLite and PostgreSQL/PostGIS.

## Entity Relationship Overview

```
[bus_stops] 1 ---- * [route_stops] * ---- 1 [bus_routes]
     |                                          |
     +--- (from_stop_id)                        +--- (route_id)
     |          \                              /
     |           * [route_edges] * -----------+
     +--- (to_stop_id)         |
                               | (edge_id)
                               *
                      [congestion_data]

[bus_stops] 1 ---- * [demand_data]
[bus_routes] 1 ---- * [buses]

[bus_stops] (from/to) ---- * [optimization_runs] 1 ---- * [optimization_results]
```

## Table Definitions

### 1. `bus_stops`
Represents physical passenger embarkation and disembarkation locations.
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Unique identifier |
| `stop_code` | TEXT UNIQUE | Standard code (e.g. `S01`) |
| `name` | TEXT | Human-readable name |
| `latitude` | REAL | WGS84 Latitude |
| `longitude` | REAL | WGS84 Longitude |
| `zone` | TEXT | Fare and service zone (`A`, `B`, `C`) |
| `is_terminal` | INTEGER | 1 if terminal depot, 0 otherwise |
| `passenger_load` | INTEGER | Average boarding density |

### 2. `bus_routes`
Represents scheduled bus transit lines and corridors.
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Unique identifier |
| `route_code` | TEXT UNIQUE | Line designation (e.g. `R01`) |
| `name` | TEXT | Corridor title |
| `frequency` | INTEGER | Buses dispatched per hour |
| `capacity` | INTEGER | Vehicle passenger capacity |
| `status` | TEXT | `ACTIVE`, `SUSPENDED` |

### 3. `route_stops`
Maintains sequential stop ordering per transit line.
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Unique identifier |
| `route_id` | INTEGER FK | References `bus_routes(id)` |
| `stop_id` | INTEGER FK | References `bus_stops(id)` |
| `stop_order` | INTEGER | Order sequence integer |

### 4. `route_edges`
Directed physical graph links connecting consecutive stops.
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Unique identifier |
| `route_id` | INTEGER FK | References `bus_routes(id)` |
| `from_stop_id` | INTEGER FK | Origin stop |
| `to_stop_id` | INTEGER FK | Destination stop |
| `distance_km` | REAL | Segment road distance in kilometers |
| `travel_time_min` | REAL | Base free-flow travel time in minutes |
| `fare` | REAL | Segment passenger tariff in INR (₹) |
| `congestion` | REAL | Traffic delay multiplier (1.0 = nominal) |
| `sequence_order` | INTEGER | Ordering on the corridor |

### 5. `buses`
Active fleet vehicle registry.
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Unique identifier |
| `bus_number` | TEXT UNIQUE | License plate number |
| `route_id` | INTEGER FK | Assigned route |
| `model` | TEXT | Vehicle chassis specification |
| `capacity` | INTEGER | Seating + standing capacity |
| `status` | TEXT | `ON_ROUTE`, `IDLE`, `MAINTENANCE` |
| `current_load` | INTEGER | Current passenger occupancy |
| `driver_name` | TEXT | Assigned operator |
| `last_maintenance` | TEXT | Date string |

### 6. `demand_data`
Hourly passenger boarding distributions across the 24-hour cycle.
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Unique identifier |
| `stop_id` | INTEGER FK | References `bus_stops(id)` |
| `hour_of_day` | INTEGER | 0 to 23 |
| `passenger_count`| INTEGER | Aggregate commuters |
| `boardings` | INTEGER | Boarding count |
| `alightings` | INTEGER | Alighting count |
| `day_of_week` | TEXT | `WEEKDAY`, `WEEKEND` |

### 7. `congestion_data`
Hourly corridor telemetry capturing speed and congestion factors.

### 8. `optimization_runs` & `optimization_results`
Audit log recording every computed optimization query, selected objectives, measured execution latencies, and candidate metric rankings.
