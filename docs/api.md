# REST API Reference

The backend provides a comprehensive RESTful API exposed on port `8080`.

## Base URL
```
http://localhost:8080/api
```

## Endpoints

### 1. System & Health
- **`GET /health`**
  - Returns backend service health, database status, and current timestamp.
  - Response: `{"status": "ok", "service": "...", "database": "..."}`
- **`GET /graph/stats`**
  - Returns topology vertex count, edge count, fleet size, and component connectivity.
- **`GET /network`**
  - Returns complete network topology including all stops, routes, and directed edges with coordinates.

### 2. Bus Stops
- **`GET /stops`**: List all stops.
- **`GET /stops/<id>`**: Retrieve specific stop by integer ID.
- **`POST /stops`**: Create new transit stop.
  - Payload: `{"stop_code": "S23", "name": "Stop Name", "latitude": 11.02, "longitude": 76.96, "zone": "A"}`
  - Returns: HTTP 201 Created.
- **`PUT /stops/<id>`**: Update stop attributes.
- **`DELETE /stops/<id>`**: Delete stop.

### 3. Bus Routes
- **`GET /routes`**: List all active routes.
- **`GET /routes/<id>`**: Get route details with ordered stop sequence.
- **`POST /routes`**: Register new route.
- **`PUT /routes/<id>`**: Update route.
- **`DELETE /routes/<id>`**: Delete route.
- **`GET /edges`**: Retrieve all directed route corridor edges.

### 4. Fleet Management
- **`GET /buses`**: List all active vehicles with live occupancy loads and maintenance status.
- **`GET /buses/<id>`**: Specific bus telemetry.

### 5. Demand & Congestion Analytics
- **`GET /demand`**: Hourly commuter volume across the 24-hour distribution.
- **`GET /congestion`**: Roadway congestion factors and recorded transit speeds.
- **`GET /analytics/dashboard`**: Executive KPIs (on-time rate, active fleet, network health).
- **`GET /analytics/demand`**: Top 10 high-density stops and hourly distribution.
- **`GET /analytics/congestion`**: High-delay bottleneck corridor hotspots.

### 6. Route Optimization
- **`POST /optimization/route`**
  - Main unified optimization solver.
  - Request Body:
    ```json
    {
      "from_stop_id": 1,
      "to_stop_id": 2,
      "mode": "balanced",
      "algorithm": "astar"
    }
    ```
  - Supported Modes: `balanced`, `fastest`, `shortest`, `low_congestion`, `high_demand`, `low_cost`.
  - Supported Algorithms: `astar`, `dijkstra`, `alternatives`.
  - Response:
    ```json
    {
      "status": "success",
      "algorithm": "astar",
      "optimization_mode": "balanced",
      "optimization_time_ms": 0.185,
      "cost": 6.2,
      "score": 99.4,
      "total_distance_km": 1.6,
      "total_time_min": 5.5,
      "total_fare": 8.0,
      "transfers": 0,
      "num_stops": 2,
      "routes_used": ["R02"],
      "stop_names": ["Central Bus Stand", "Railway Station"],
      "coordinates": [...],
      "alternatives": [...]
    }
    ```
- **`POST /dijkstra`**: Direct Dijkstra solver endpoint.
- **`POST /astar`**: Direct A* solver endpoint.
- **`POST /alternatives`**: Direct K-Shortest path solver endpoint.

### 7. Optimization History
- **`GET /optimization/history?limit=20`**: Recent optimization runs.
- **`GET /optimization/<run_id>`**: Detailed breakdown of a historical run.
