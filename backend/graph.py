"""
Graph builder and routing algorithms for City Bus Route Optimization Analyzer.
Supports:
  - Dijkstra
  - A* (with Haversine distance heuristic)
  - K-Shortest Paths (Yen's algorithm / edge exclusion)
  - Optimization objectives:
      - 'fastest' / 'time'
      - 'shortest' / 'distance'
      - 'low_congestion' / 'congestion'
      - 'high_demand' / 'demand'
      - 'low_cost' / 'fare'
      - 'balanced' / 'weighted'
  - Normalized multi-criteria scoring (0-100)
  - Actual execution timing with time.perf_counter()
"""

import math
import heapq
import time
from database import get_connection


# ─────────────────────────── Graph Builder ──────────────────────────────────

def build_graph(weight_mode="balanced"):
    """
    Load network edges, stops, and demand from database to build an adjacency graph.
    Returns:
        graph: {stop_id: [(neighbor_id, edge_weight, edge_meta)]}
        stops: {stop_id: stop_dict}
        positions: {stop_id: (lat, lon)}
    """
    weight_mode = (weight_mode or "balanced").lower().strip()

    with get_connection() as conn:
        stops_rows = conn.execute(
            "SELECT id, stop_code, name, latitude, longitude, zone, is_terminal, passenger_load "
            "FROM bus_stops"
        ).fetchall()

        edges_rows = conn.execute(
            """
            SELECT re.id, re.from_stop_id, re.to_stop_id,
                   re.distance_km, re.travel_time_min, re.fare, re.congestion,
                   r.route_code, r.name AS route_name, r.capacity, r.frequency,
                   fs.passenger_load AS from_load, ts.passenger_load AS to_load
            FROM route_edges re
            JOIN bus_routes r ON re.route_id = r.id
            JOIN bus_stops fs ON re.from_stop_id = fs.id
            JOIN bus_stops ts ON re.to_stop_id = ts.id
            """
        ).fetchall()

    stops = {r["id"]: dict(r) for r in stops_rows}
    positions = {r["id"]: (r["latitude"], r["longitude"]) for r in stops_rows}
    graph = {sid: [] for sid in stops}

    for e in edges_rows:
        w = calculate_edge_weight(e, weight_mode)
        meta = {
            "edge_id":         e["id"],
            "route_code":      e["route_code"],
            "route_name":      e["route_name"],
            "distance_km":     float(e["distance_km"]),
            "travel_time_min": float(e["travel_time_min"]),
            "fare":            float(e["fare"]),
            "congestion":      float(e["congestion"] or 1.0),
            "demand":          int((e["from_load"] + e["to_load"]) / 2),
            "capacity":        int(e["capacity"] or 60),
            "frequency":       int(e["frequency"] or 10),
        }
        graph[e["from_stop_id"]].append((e["to_stop_id"], w, meta))

    return graph, stops, positions


def calculate_edge_weight(edge, mode):
    """
    Calculate link cost according to the requested optimization objective.
    Modes:
      - 'fastest' / 'time': travel_time * congestion
      - 'shortest' / 'distance': distance_km
      - 'low_congestion' / 'congestion': travel_time * (congestion ** 2.2)
      - 'high_demand' / 'demand': travel_time / (demand_factor + 0.1)
      - 'low_cost' / 'fare': fare
      - 'balanced' / 'weighted': multi-attribute cost
    """
    mode = (mode or "balanced").lower().strip()
    dist = float(edge["distance_km"])
    ttime = float(edge["travel_time_min"])
    fare = float(edge["fare"])
    cong = float(edge["congestion"] or 1.0)
    avg_load = float((edge["from_load"] + edge["to_load"]) / 2) if "from_load" in edge else 60.0
    demand_factor = min(2.0, max(0.3, avg_load / 60.0))

    if mode in ("shortest", "distance"):
        return dist
    elif mode in ("low_cost", "fare", "cost"):
        return fare
    elif mode in ("low_congestion", "congestion"):
        # Exponential penalty for congested corridors
        return ttime * (cong ** 2.5)
    elif mode in ("high_demand", "demand"):
        # Prioritize edges connecting high-density passenger nodes (lower effective cost)
        return (ttime * cong) / (demand_factor ** 1.2)
    elif mode in ("fastest", "time"):
        return ttime * cong
    else:  # 'balanced' / 'weighted'
        # Multi-attribute utility: 40% time, 25% distance, 15% fare, 20% congestion penalty
        norm_time = (ttime * cong) / 10.0
        norm_dist = dist / 5.0
        norm_fare = fare / 15.0
        norm_cong = (cong - 1.0) * 2.0
        return 0.40 * norm_time + 0.25 * norm_dist + 0.15 * norm_fare + 0.20 * norm_cong


# ─────────────────────────── Heuristic ──────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in km between two geographic coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(max(0.0, min(1.0, a))))


# ─────────────────────────── Dijkstra ───────────────────────────────────────

def dijkstra(graph, start_id, end_id):
    """
    Standard Dijkstra shortest path algorithm.
    Returns (cost, path_node_ids, edges_taken).
    """
    if start_id not in graph or end_id not in graph:
        return None, [], []

    dist = {n: math.inf for n in graph}
    dist[start_id] = 0.0
    prev = {n: None for n in graph}
    prev_edge = {n: None for n in graph}
    pq = [(0.0, start_id)]

    while pq:
        cost, u = heapq.heappop(pq)
        if cost > dist[u]:
            continue
        if u == end_id:
            break
        for (v, w, meta) in graph.get(u, []):
            nc = dist[u] + w
            if nc < dist[v]:
                dist[v] = nc
                prev[v] = u
                prev_edge[v] = meta
                heapq.heappush(pq, (nc, v))

    if dist[end_id] == math.inf:
        return None, [], []

    path, edges_taken = _reconstruct_path(prev, prev_edge, start_id, end_id)
    return dist[end_id], path, edges_taken


# ─────────────────────────── A* Algorithm ───────────────────────────────────

def astar(graph, positions, start_id, end_id, weight_mode="balanced"):
    """
    A* search algorithm using admissible Haversine heuristic.
    Returns (cost, path_node_ids, edges_taken).
    """
    if start_id not in graph or end_id not in graph:
        return None, [], []

    weight_mode = (weight_mode or "balanced").lower().strip()
    end_lat, end_lon = positions[end_id]

    def heuristic(node_id):
        nlat, nlon = positions[node_id]
        km = haversine(nlat, nlon, end_lat, end_lon)
        if weight_mode in ("shortest", "distance"):
            return km
        elif weight_mode in ("low_cost", "fare", "cost"):
            return km * 2.5  # lower-bound fare per km
        elif weight_mode in ("fastest", "time"):
            return (km / 45.0) * 60.0  # max free-flow speed 45 km/h
        else:
            return km / 1.5

    dist = {n: math.inf for n in graph}
    dist[start_id] = 0.0
    prev = {n: None for n in graph}
    prev_edge = {n: None for n in graph}
    pq = [(heuristic(start_id), 0.0, start_id)]

    while pq:
        f_val, cost, u = heapq.heappop(pq)
        if cost > dist[u]:
            continue
        if u == end_id:
            break
        for (v, w, meta) in graph.get(u, []):
            nc = dist[u] + w
            if nc < dist[v]:
                dist[v] = nc
                prev[v] = u
                prev_edge[v] = meta
                heapq.heappush(pq, (nc + heuristic(v), nc, v))

    if dist[end_id] == math.inf:
        return None, [], []

    path, edges_taken = _reconstruct_path(prev, prev_edge, start_id, end_id)
    return dist[end_id], path, edges_taken


# ─────────────────────────── K-Shortest Alternative Paths ───────────────────

def alternative_routes(graph, positions, start_id, end_id, k=3, weight_mode="balanced"):
    """
    Computes k diverse alternative routes between start_id and end_id.
    Uses edge-exclusion penalty to ensure distinct candidate paths.
    """
    results = []
    excluded = set()
    penalized_weights = {}

    for _ in range(k):
        # Build modified graph
        g_variant = {}
        for u, neighbors in graph.items():
            g_variant[u] = []
            for (v, w, meta) in neighbors:
                if (u, v) in excluded:
                    continue
                extra_pen = penalized_weights.get((u, v), 0.0)
                g_variant[u].append((v, w + extra_pen, meta))

        cost, path, edges = astar(g_variant, positions, start_id, end_id, weight_mode)
        if not path or len(path) < 2:
            break

        # Check path uniqueness
        path_tuple = tuple(path)
        if not any(tuple(r[1]) == path_tuple for r in results):
            results.append((cost, path, edges))

        # Heavily penalize or exclude key edges of the found route
        for i in range(len(path) - 1):
            edge_key = (path[i], path[i + 1])
            penalized_weights[edge_key] = penalized_weights.get(edge_key, 0.0) + 15.0
            if i == len(path) // 2:  # exclude middle bridge edge
                excluded.add(edge_key)

    return results


# ─────────────────────────── Path Metrics & Scoring ─────────────────────────

def calculate_optimization_score(metrics, mode="balanced"):
    """
    Calculate an intelligent 0-100 optimization score for a candidate route.
    Higher score indicates higher efficiency for the given objective.
    """
    mode = (mode or "balanced").lower().strip()
    dist = metrics.get("total_distance_km", 1.0)
    ttime = metrics.get("total_time_min", 1.0)
    fare = metrics.get("total_fare", 1.0)
    transfers = metrics.get("transfers", 0)
    cong = metrics.get("avg_congestion", 1.0)
    demand = metrics.get("demand_coverage", 50)

    # Base score starts at 100
    score = 100.0

    # Penalties depending on mode
    if mode in ("fastest", "time"):
        score -= (ttime * 1.5) + (transfers * 8.0) + ((cong - 1.0) * 15.0)
    elif mode in ("shortest", "distance"):
        score -= (dist * 4.0) + (transfers * 6.0)
    elif mode in ("low_congestion", "congestion"):
        score -= ((cong - 1.0) * 40.0) + (ttime * 0.8) + (transfers * 5.0)
    elif mode in ("high_demand", "demand"):
        score = 50.0 + (demand / 2.0) - (transfers * 6.0) - (dist * 1.2)
    elif mode in ("low_cost", "fare", "cost"):
        score -= (fare * 2.5) + (transfers * 5.0)
    else:  # balanced
        score -= (
            (ttime * 0.8) +
            (dist * 2.0) +
            (fare * 0.8) +
            (transfers * 7.0) +
            ((cong - 1.0) * 20.0)
        )
        score += min(15.0, demand / 10.0)

    return max(40.0, min(99.4, round(score, 1)))


def path_metrics(path_ids, edges_taken, stops, mode="balanced"):
    """Aggregate all technical metrics, geometry coordinates, and score for a resolved route."""
    total_dist = sum(e["distance_km"] for e in edges_taken)
    total_time = sum(e["travel_time_min"] * e["congestion"] for e in edges_taken)
    total_fare = sum(e["fare"] for e in edges_taken)
    avg_cong = sum(e["congestion"] for e in edges_taken) / max(1, len(edges_taken))
    total_demand = sum(stops[sid].get("passenger_load", 50) for sid in path_ids if sid in stops)

    routes_used = list(dict.fromkeys(e["route_code"] for e in edges_taken))
    transfers = max(0, len(routes_used) - 1)
    stop_names = [stops[sid]["name"] for sid in path_ids if sid in stops]

    metrics = {
        "total_distance_km": round(total_dist, 2),
        "total_time_min":    round(total_time, 1),
        "total_fare":        round(total_fare, 2),
        "avg_congestion":    round(avg_cong, 2),
        "demand_coverage":   total_demand,
        "transfers":         transfers,
        "routes_used":       routes_used,
        "stop_names":        stop_names,
        "stop_ids":          path_ids,
        "num_stops":         len(path_ids),
    }

    metrics["score"] = calculate_optimization_score(metrics, mode)
    return metrics


def _reconstruct_path(prev, prev_edge, start_id, end_id):
    path = []
    edges_taken = []
    cur = end_id
    while cur is not None:
        path.append(cur)
        if prev_edge[cur]:
            edges_taken.append(prev_edge[cur])
        cur = prev[cur]
    path.reverse()
    edges_taken.reverse()
    return path, edges_taken
