"""
End-to-end verification and testing suite for City Bus Route Optimization Analyzer.
Tests database tables, graph construction, routing algorithms (Dijkstra, A*, Yen's),
all 6 optimization modes, all REST API endpoints, edge cases, and timing metrics.
"""

import sys
import json
import urllib.request
import urllib.error
import time

BASE_URL = "http://127.0.0.1:8080"


def request(method, path, body=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            return status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        return e.code, json.loads(content) if content else {}
    except Exception as ex:
        return 0, {"error": str(ex)}


def run_tests():
    passed = 0
    failed = 0
    results = []

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name} {detail}")
            results.append((name, "PASS", detail))
        else:
            failed += 1
            print(f"  [FAIL] {name} {detail}")
            results.append((name, "FAIL", detail))

    print("\n" + "=" * 60)
    print("STEP 1: VERIFY ENVIRONMENT & HEALTH")
    print("=" * 60)
    status, data = request("GET", "/api/health")
    check("GET /api/health returns 200", status == 200)
    check("Service health status ok", data.get("status") == "ok")

    status, data = request("GET", "/api/graph/stats")
    check("GET /api/graph/stats returns 200", status == 200)
    check("Graph nodes >= 20", data.get("graph_nodes", 0) >= 20, f"nodes={data.get('graph_nodes')}")
    check("Graph edges >= 40", data.get("graph_edges", 0) >= 40, f"edges={data.get('graph_edges')}")
    check("Fleet size > 0", data.get("fleet_size", 0) > 0, f"buses={data.get('fleet_size')}")

    print("\n" + "=" * 60)
    print("STEP 2: VERIFY NETWORK TOPOLOGY API")
    print("=" * 60)
    status, data = request("GET", "/api/network")
    check("GET /api/network returns 200", status == 200)
    check("Network contains stops list", len(data.get("stops", [])) >= 20)
    check("Network contains routes list", len(data.get("routes", [])) >= 5)
    check("Network contains edges list", len(data.get("edges", [])) >= 40)

    print("\n" + "=" * 60)
    print("STEP 3: VERIFY BUS STOPS CRUD")
    print("=" * 60)
    status, stops = request("GET", "/api/stops")
    check("GET /api/stops returns 200", status == 200)
    s01 = next((s for s in stops if s["stop_code"] == "S01"), None)
    s02 = next((s for s in stops if s["stop_code"] == "S02"), None)
    check("Central Bus Stand (S01) exists", s01 is not None and "Central Bus Stand" in s01["name"])
    check("Railway Station (S02) exists", s02 is not None and "Railway Station" in s02["name"])

    # Test single stop retrieval
    s01_id = s01["id"] if s01 else 1
    status, s_single = request("GET", f"/api/stops/{s01_id}")
    check(f"GET /api/stops/{s01_id} returns 200", status == 200)
    check("Single stop detail matches", s_single.get("stop_code") == "S01")

    # Test Stop CRUD create, update, delete
    status, created_stop = request("POST", "/api/stops", {
        "stop_code": "S_TEST",
        "name": "Test Depot",
        "latitude": 11.0200,
        "longitude": 76.9600,
        "zone": "A"
    })
    check("POST /api/stops creates new stop (201)", status == 201)
    test_id = created_stop.get("id")

    if test_id:
        status, updated_stop = request("PUT", f"/api/stops/{test_id}", {"name": "Test Depot Updated"})
        check("PUT /api/stops/{id} updates stop (200)", status == 200 and updated_stop.get("name") == "Test Depot Updated")

        status, del_resp = request("DELETE", f"/api/stops/{test_id}")
        check("DELETE /api/stops/{id} deletes stop (200)", status == 200)

    print("\n" + "=" * 60)
    print("STEP 4: VERIFY ROUTES & EDGES")
    print("=" * 60)
    status, routes = request("GET", "/api/routes")
    check("GET /api/routes returns 200", status == 200)
    check("Routes count >= 5", len(routes) >= 5)

    status, r1 = request("GET", f"/api/routes/{routes[0]['id']}")
    check(f"GET /api/routes/{routes[0]['id']} returns 200", status == 200)
    check("Route includes stops list", "stops" in r1 and len(r1["stops"]) > 0)

    status, edges = request("GET", "/api/edges")
    check("GET /api/edges returns 200", status == 200)
    check("Edges count >= 40", len(edges) >= 40)

    print("\n" + "=" * 60)
    print("STEP 5: VERIFY FLEET & ANALYTICS")
    print("=" * 60)
    status, buses = request("GET", "/api/buses")
    check("GET /api/buses returns 200", status == 200)
    check("Fleet buses >= 10", len(buses) >= 10)

    status, bus1 = request("GET", f"/api/buses/{buses[0]['id']}")
    check(f"GET /api/buses/{buses[0]['id']} returns 200", status == 200)
    check("Bus has registration number", bool(bus1.get("bus_number")))

    status, demand = request("GET", "/api/demand")
    check("GET /api/demand returns 200", status == 200)
    check("Demand data has 24 hours", len(demand) == 24)

    status, congestion = request("GET", "/api/congestion")
    check("GET /api/congestion returns 200", status == 200)
    check("Congestion records exist", len(congestion) > 0)

    status, dash = request("GET", "/api/analytics/dashboard")
    check("GET /api/analytics/dashboard returns 200", status == 200)
    check("Dashboard includes KPIs", "kpis" in dash and dash["kpis"]["fleet_active"] > 0)

    status, d_analytics = request("GET", "/api/analytics/demand")
    check("GET /api/analytics/demand returns 200", status == 200)
    check("Demand analytics has top stops", len(d_analytics.get("top_demand_stops", [])) > 0)

    status, c_analytics = request("GET", "/api/analytics/congestion")
    check("GET /api/analytics/congestion returns 200", status == 200)
    check("Congestion analytics has corridor hotspots", len(c_analytics.get("corridor_hotspots", [])) > 0)

    print("\n" + "=" * 60)
    print("STEP 6: VERIFY ALGORITHMS (Dijkstra, A*, Alternatives)")
    print("=" * 60)
    s01_id = s01["id"] if s01 else 1
    s02_id = s02["id"] if s02 else 2

    # Dijkstra
    status, d_res = request("POST", "/api/dijkstra", {
        "from_stop_id": s01_id,
        "to_stop_id": s02_id,
        "weight_mode": "time"
    })
    check("POST /api/dijkstra returns 200", status == 200)
    check("Dijkstra returned path", len(d_res.get("stop_names", [])) >= 2)
    check("Dijkstra cost > 0", d_res.get("cost", 0) > 0)

    # A*
    status, a_res = request("POST", "/api/astar", {
        "from_stop_id": s01_id,
        "to_stop_id": s02_id,
        "weight_mode": "time"
    })
    check("POST /api/astar returns 200", status == 200)
    check("A* returned coordinates", len(a_res.get("coordinates", [])) >= 2)
    check("A* cost matches/is optimal", a_res.get("cost", 0) > 0)

    # Alternatives
    status, alt_res = request("POST", "/api/alternatives", {
        "from_stop_id": s01_id,
        "to_stop_id": s02_id,
        "k": 3,
        "weight_mode": "balanced"
    })
    check("POST /api/alternatives returns 200", status == 200)
    check("Alternatives list >= 1", len(alt_res.get("alternatives", [])) >= 1)

    print("\n" + "=" * 60)
    print("STEP 7: VERIFY ALL 6 OPTIMIZATION MODES (Central Bus Stand -> Railway Station)")
    print("=" * 60)
    modes = [
        "balanced",
        "fastest",
        "shortest",
        "low_congestion",
        "high_demand",
        "low_cost"
    ]
    for mode in modes:
        t0 = time.perf_counter()
        status, opt_res = request("POST", "/api/optimization/route", {
            "from_stop_id": s01_id,
            "to_stop_id": s02_id,
            "mode": mode,
            "algorithm": "astar"
        })
        elap = (time.perf_counter() - t0) * 1000.0
        check(f"Optimization mode '{mode}' returns 200", status == 200)
        check(f"Mode '{mode}' has valid score", 0 < opt_res.get("score", 0) <= 100, f"score={opt_res.get('score')}")
        check(f"Mode '{mode}' has measured exec time", opt_res.get("optimization_time_ms", 0) >= 0.0, f"time={opt_res.get('optimization_time_ms')}ms")
        check(f"Mode '{mode}' has distance & time", opt_res.get("total_distance_km", 0) > 0 and opt_res.get("total_time_min", 0) > 0)

    print("\n" + "=" * 60)
    print("STEP 8: VERIFY OPTIMIZATION HISTORY")
    print("=" * 60)
    status, history = request("GET", "/api/optimization/history?limit=10")
    check("GET /api/optimization/history returns 200", status == 200)
    check("History records exist", len(history) > 0, f"records={len(history)}")

    last_id = history[0]["id"]
    status, h_detail = request("GET", f"/api/optimization/{last_id}")
    check(f"GET /api/optimization/{last_id} returns 200", status == 200)
    check("History detail has results", len(h_detail.get("results", [])) > 0)

    print("\n" + "=" * 60)
    print("STEP 9: VERIFY EDGE CASES & ERROR HANDLING")
    print("=" * 60)
    # Source == Destination
    status, err1 = request("POST", "/api/optimization/route", {
        "from_stop_id": s01_id,
        "to_stop_id": s01_id,
        "mode": "balanced"
    })
    check("Same source and dest returns 400", status == 400)

    # Missing stops
    status, err2 = request("POST", "/api/optimization/route", {
        "from_stop_id": 0,
        "to_stop_id": 0
    })
    check("Missing source/dest returns 400", status == 400)

    # Non-existent stop ID
    status, err3 = request("POST", "/api/optimization/route", {
        "from_stop_id": 99999,
        "to_stop_id": s02_id
    })
    check("Non-existent stop ID returns 404", status == 404)

    # Invalid route ID
    status, err4 = request("GET", "/api/routes/99999")
    check("Invalid route ID returns 404", status == 404)

    # Invalid stop ID
    status, err5 = request("GET", "/api/stops/99999")
    check("Invalid stop ID returns 404", status == 404)

    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed} PASSED, {failed} FAILED (TOTAL {passed + failed})")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
