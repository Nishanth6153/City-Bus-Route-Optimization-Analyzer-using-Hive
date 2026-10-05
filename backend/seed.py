"""
Seed demo data for the City Bus Route Optimization Analyzer.
Represents a realistic mid-sized smart-city bus transit network (Coimbatore Smart City).
Populates:
  - bus_stops (22 strategic transit stops including Central Bus Stand & Railway Station)
  - bus_routes (6 high-frequency routes)
  - route_stops (sequential stop order per route)
  - route_edges (56 bidirectional & corridor edges with realistic distance, time, fare, congestion)
  - buses (16 active fleet vehicles with live status, drivers, load, maintenance)
  - demand_data (hourly passenger boarding/alighting distributions)
  - congestion_data (time-based traffic congestion indices & speeds)
  - optimization_runs & optimization_results (pre-computed optimization history)
"""

import json
from database import get_connection, init_db

# ─────────────────────────── bus stops ──────────────────────────────────────────
# (stop_code, name, lat, lon, zone, is_terminal, passenger_load)
STOPS = [
    ("S01", "Central Bus Stand",        11.0168,  76.9558, "A", 1, 95),
    ("S02", "Railway Station",          11.0016,  76.9666, "A", 1, 90),
    ("S03", "Gandhipuram Central",      11.0175,  76.9780, "A", 1, 85),
    ("S04", "Town Hall",                11.0186,  76.9659, "A", 0, 70),
    ("S05", "RS Puram West",            11.0050,  76.9554, "A", 0, 65),
    ("S06", "Peelamedu Tech Park",      11.0217,  77.0237, "B", 0, 80),
    ("S07", "Airport Road Junction",    11.0300,  77.0450, "B", 0, 55),
    ("S08", "Ukkadam Bus Terminal",     10.9962,  76.9641, "A", 1, 88),
    ("S09", "Saibaba Colony",           11.0069,  76.9806, "A", 0, 60),
    ("S10", "Singanallur Hub",          10.9997,  77.0261, "B", 1, 75),
    ("S11", "Ganapathy Junction",       11.0343,  76.9666, "A", 0, 58),
    ("S12", "Vadavalli Hills",          11.0285,  76.9225, "B", 0, 45),
    ("S13", "Race Course Promenade",    11.0095,  76.9692, "A", 0, 50),
    ("S14", "TNAU Gate",                11.0133,  77.0021, "B", 0, 62),
    ("S15", "Hopes College",            11.0250,  76.9912, "B", 0, 72),
    ("S16", "Kovaipudur South",         10.9798,  76.9450, "C", 1, 40),
    ("S17", "Sulur Aero Hub",           11.0318,  77.1257, "C", 1, 35),
    ("S18", "Podanur Junction",         10.9765,  76.9720, "C", 0, 48),
    ("S19", "Ramakrishna Hospital",     11.0130,  76.9490, "A", 0, 52),
    ("S20", "VOC Park",                 11.0020,  76.9700, "A", 0, 64),
    ("S21", "Maruthamalai Road",        11.0490,  76.9500, "B", 0, 42),
    ("S22", "Saravanampatti IT Corridor", 11.0780, 77.0010, "B", 0, 85),
]

# ─────────────────────────── bus routes ─────────────────────────────────────────
# (route_code, name, frequency, capacity, status)
ROUTES = [
    ("R01", "Central – Peelamedu Express",        12, 65, "ACTIVE"),
    ("R02", "Railway Station – Airport Link",      10, 60, "ACTIVE"),
    ("R03", "Ukkadam – Singanallur Direct",        8, 55, "ACTIVE"),
    ("R04", "Kovaipudur – Sulur Aero Express",     6, 60, "ACTIVE"),
    ("R05", "RS Puram – IT Corridor Shuttle",     15, 50, "ACTIVE"),
    ("R06", "Metro Circular Ring Line",            10, 70, "ACTIVE"),
]

# ─────────────────────────── route stops sequence ────────────────────────────────
# (route_code, [stop_codes])
ROUTE_STOPS_MAP = {
    "R01": ["S01", "S04", "S03", "S14", "S06"],
    "R02": ["S02", "S20", "S04", "S03", "S15", "S06", "S07"],
    "R03": ["S08", "S20", "S13", "S04", "S09", "S10"],
    "R04": ["S16", "S18", "S05", "S01", "S02", "S03", "S06", "S17"],
    "R05": ["S05", "S01", "S19", "S03", "S11", "S22"],
    "R06": ["S01", "S02", "S08", "S10", "S06", "S15", "S03", "S01"],
}

# ─────────────────────────── route edges ─────────────────────────────────────────
# (route_code, from_code, to_code, dist_km, time_min, fare, congestion, seq)
EDGES = [
    # R01: Central -> Town Hall -> Gandhipuram -> TNAU -> Peelamedu
    ("R01", "S01", "S04", 1.2,  4.0,   8.0,  1.1, 1),
    ("R01", "S04", "S03", 1.5,  5.0,  10.0,  1.2, 2),
    ("R01", "S03", "S14", 2.8,  9.0,  15.0,  1.0, 3),
    ("R01", "S14", "S06", 2.4,  8.0,  12.0,  0.9, 4),
    # R01 Reverse
    ("R01", "S06", "S14", 2.4,  8.0,  12.0,  1.0, 5),
    ("R01", "S14", "S03", 2.8,  9.0,  15.0,  1.1, 6),
    ("R01", "S03", "S04", 1.5,  5.0,  10.0,  1.0, 7),
    ("R01", "S04", "S01", 1.2,  4.5,   8.0,  1.0, 8),

    # Direct connection between Central Bus Stand and Railway Station
    ("R02", "S01", "S02", 1.6,  5.5,   8.0,  1.1, 1),
    ("R02", "S02", "S01", 1.6,  5.5,   8.0,  1.1, 2),

    # R02: Railway Station -> VOC Park -> Town Hall -> Gandhipuram -> Hopes -> Peelamedu -> Airport
    ("R02", "S02", "S20", 0.9,  3.0,   6.0,  1.0, 3),
    ("R02", "S20", "S04", 1.4,  5.0,   8.0,  1.2, 4),
    ("R02", "S04", "S03", 1.5,  5.0,  10.0,  1.1, 5),
    ("R02", "S03", "S15", 2.2,  7.0,  12.0,  1.0, 6),
    ("R02", "S15", "S06", 2.0,  6.0,  10.0,  1.0, 7),
    ("R02", "S06", "S07", 3.0, 10.0,  15.0,  0.9, 8),
    # R02 Reverse
    ("R02", "S07", "S06", 3.0,  9.5,  15.0,  0.9, 9),
    ("R02", "S06", "S15", 2.0,  6.0,  10.0,  1.0, 10),
    ("R02", "S15", "S03", 2.2,  7.0,  12.0,  1.0, 11),
    ("R02", "S03", "S20", 2.0,  6.5,  11.0,  1.2, 12),
    ("R02", "S20", "S02", 0.9,  3.0,   6.0,  1.0, 13),

    # R03: Ukkadam -> VOC Park -> Race Course -> Town Hall -> Saibaba -> Singanallur
    ("R03", "S08", "S20", 1.0,  4.0,   7.0,  1.0, 1),
    ("R03", "S20", "S13", 1.5,  5.0,   8.0,  1.3, 2),
    ("R03", "S13", "S04", 0.8,  3.0,   5.0,  1.2, 3),
    ("R03", "S04", "S09", 2.0,  7.0,  10.0,  1.0, 4),
    ("R03", "S09", "S10", 3.5, 12.0,  18.0,  1.0, 5),
    ("R03", "S10", "S08", 5.0, 16.0,  22.0,  0.9, 6),
    # R03 Return
    ("R03", "S08", "S10", 5.0, 16.0,  22.0,  0.9, 7),
    ("R03", "S10", "S09", 3.5, 11.5,  18.0,  1.0, 8),
    ("R03", "S09", "S04", 2.0,  6.5,  10.0,  1.0, 9),

    # R04: Kovaipudur -> Podanur -> RS Puram -> Central -> Railway Station -> Gandhipuram -> Peelamedu -> Sulur
    ("R04", "S16", "S18", 2.5,  9.0,  12.0,  1.0, 1),
    ("R04", "S18", "S05", 2.0,  7.0,  10.0,  1.0, 2),
    ("R04", "S05", "S01", 1.8,  6.0,   9.0,  1.1, 3),
    ("R04", "S01", "S02", 1.6,  5.0,   8.0,  1.0, 4),
    ("R04", "S02", "S03", 2.2,  7.0,  11.0,  1.2, 5),
    ("R04", "S03", "S06", 4.2, 13.0,  20.0,  1.0, 6),
    ("R04", "S06", "S17", 8.0, 25.0,  35.0,  0.8, 7),
    # R04 Reverse
    ("R04", "S17", "S06", 8.0, 25.0,  35.0,  0.8, 8),
    ("R04", "S06", "S03", 4.2, 13.0,  20.0,  1.1, 9),
    ("R04", "S03", "S02", 2.2,  7.0,  11.0,  1.1, 10),
    ("R04", "S02", "S01", 1.6,  5.0,   8.0,  1.0, 11),
    ("R04", "S01", "S05", 1.8,  6.0,   9.0,  1.0, 12),
    ("R04", "S05", "S18", 2.0,  7.0,  10.0,  1.0, 13),
    ("R04", "S18", "S16", 2.5,  9.0,  12.0,  1.0, 14),

    # R05: RS Puram -> Central -> Hospital -> Gandhipuram -> Ganapathy -> Saravanampatti
    ("R05", "S05", "S01", 1.8,  6.0,   9.0,  1.0, 1),
    ("R05", "S01", "S19", 0.8,  3.0,   5.0,  1.0, 2),
    ("R05", "S19", "S03", 1.5,  5.0,   8.0,  1.1, 3),
    ("R05", "S03", "S11", 2.0,  7.0,  10.0,  1.2, 4),
    ("R05", "S11", "S22", 4.5, 14.0,  22.0,  1.0, 5),
    # R05 Return
    ("R05", "S22", "S11", 4.5, 14.0,  22.0,  1.0, 6),
    ("R05", "S11", "S03", 2.0,  7.0,  10.0,  1.1, 7),
    ("R05", "S03", "S19", 1.5,  5.0,   8.0,  1.0, 8),
    ("R05", "S19", "S01", 0.8,  3.0,   5.0,  1.0, 9),
    ("R05", "S01", "S05", 1.8,  6.0,   9.0,  1.0, 10),

    # Cross connections & Arterials
    ("R06", "S02", "S08", 1.8,  6.0,   9.0,  1.0, 1),
    ("R06", "S08", "S02", 1.8,  6.0,   9.0,  1.0, 2),
    ("R06", "S10", "S06", 3.2, 10.0,  15.0,  0.9, 3),
    ("R06", "S06", "S10", 3.2, 10.0,  15.0,  0.9, 4),
    ("R06", "S11", "S21", 2.5,  8.0,  12.0,  1.0, 5),
    ("R06", "S21", "S12", 3.5, 11.0,  16.0,  1.0, 6),
    ("R06", "S12", "S05", 2.8,  9.0,  14.0,  1.0, 7),
]

# ─────────────────────────── buses ──────────────────────────────────────────────
# (bus_number, route_code, model, capacity, status, current_load, driver_name, last_maintenance)
BUSES = [
    ("TN-38-N-2401", "R01", "Tata Starbus Ultra",     65, "ON_ROUTE",    48, "K. Murugan",       "2026-09-20"),
    ("TN-38-N-2402", "R01", "Ashok Leyland Viking",    60, "ON_ROUTE",    52, "P. Selvaraj",      "2026-09-22"),
    ("TN-38-N-2403", "R01", "Tata Starbus EV",        55, "ON_ROUTE",    38, "S. Ravindran",     "2026-10-01"),
    ("TN-38-N-2404", "R02", "Volvo 8400 Low Floor",   70, "ON_ROUTE",    64, "M. Senthilkumar",  "2026-09-18"),
    ("TN-38-N-2405", "R02", "Ashok Leyland JanBus",   60, "ON_ROUTE",    42, "R. Karthikeyan",   "2026-09-25"),
    ("TN-38-N-2406", "R02", "Tata Ultra EV Electric",  55, "IDLE",         0, "V. Anand",         "2026-10-02"),
    ("TN-38-N-2407", "R03", "Ashok Leyland Viking",    60, "ON_ROUTE",    50, "T. Palaniswamy",   "2026-09-15"),
    ("TN-38-N-2408", "R03", "Tata Marcopolo BS-VI",   65, "ON_ROUTE",    56, "N. Balakrishnan",  "2026-09-28"),
    ("TN-38-N-2409", "R04", "Eicher Skyline Pro",     55, "ON_ROUTE",    44, "C. Ramasamy",      "2026-09-10"),
    ("TN-38-N-2410", "R04", "Volvo B7RLE Premium",    65, "ON_ROUTE",    61, "A. Jeyachandran",  "2026-09-29"),
    ("TN-38-N-2411", "R05", "Tata Starbus Electric",  50, "ON_ROUTE",    35, "K. Vijayakumar",   "2026-10-03"),
    ("TN-38-N-2412", "R05", "Ashok Leyland Oyster",   45, "ON_ROUTE",    40, "D. Muthukumar",    "2026-09-14"),
    ("TN-38-N-2413", "R06", "Tata Ultra AC Low Floor", 60, "ON_ROUTE",    53, "G. Chandran",      "2026-09-27"),
    ("TN-38-N-2414", "R06", "Volvo 8400 Low Floor",   70, "ON_ROUTE",    58, "S. Manickam",      "2026-09-19"),
    ("TN-38-N-2415", "R03", "Ashok Leyland Viking",    60, "MAINTENANCE",  0, "Depot Standby",    "2026-10-04"),
    ("TN-38-N-2416", "R05", "Tata Starbus EV",        50, "IDLE",         0, "B. Prakash",        "2026-10-02"),
]


def seed():
    init_db(reset=True)
    with get_connection() as conn:

        # 1. Insert stops
        conn.executemany(
            "INSERT INTO bus_stops (stop_code, name, latitude, longitude, zone, is_terminal, passenger_load) "
            "VALUES (?,?,?,?,?,?,?)",
            STOPS,
        )

        # Build stop code -> id map
        rows = conn.execute("SELECT id, stop_code FROM bus_stops").fetchall()
        stop_id_map = {r["stop_code"]: r["id"] for r in rows}

        # 2. Insert routes
        route_id_map = {}
        for rc, name, freq, cap, status in ROUTES:
            cur = conn.execute(
                "INSERT INTO bus_routes (route_code, name, frequency, capacity, status) "
                "VALUES (?,?,?,?,?)",
                (rc, name, freq, cap, status),
            )
            route_id_map[rc] = cur.lastrowid

        # 3. Insert route stops
        for rc, stop_codes in ROUTE_STOPS_MAP.items():
            r_id = route_id_map[rc]
            for order, sc in enumerate(stop_codes, start=1):
                conn.execute(
                    "INSERT INTO route_stops (route_id, stop_id, stop_order) VALUES (?,?,?)",
                    (r_id, stop_id_map[sc], order),
                )

        # 4. Insert route edges
        edge_id_list = []
        for rc, from_c, to_c, dist, ttime, fare, cong, seq in EDGES:
            cur = conn.execute(
                "INSERT INTO route_edges "
                "(route_id, from_stop_id, to_stop_id, distance_km, travel_time_min, fare, congestion, sequence_order) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (route_id_map[rc], stop_id_map[from_c], stop_id_map[to_c],
                 dist, ttime, fare, cong, seq),
            )
            edge_id_list.append(cur.lastrowid)

        # 5. Insert buses
        for bnum, rcode, model, cap, status, load, driver, maint in BUSES:
            conn.execute(
                "INSERT INTO buses (bus_number, route_id, model, capacity, status, current_load, driver_name, last_maintenance) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (bnum, route_id_map.get(rcode), model, cap, status, load, driver, maint),
            )

        # 6. Insert demand data across 24 hours for all stops
        demand_rows = []
        peak_hours = {8, 9, 10, 17, 18, 19}
        for stop_code, s_id in stop_id_map.items():
            for hour in range(24):
                if hour in peak_hours:
                    passengers = 120 + (s_id * 7) % 65
                    boardings = int(passengers * 0.55)
                    alightings = int(passengers * 0.45)
                elif 6 <= hour <= 22:
                    passengers = 45 + (s_id * 5) % 35
                    boardings = int(passengers * 0.50)
                    alightings = int(passengers * 0.50)
                else:
                    passengers = 8 + (s_id * 2) % 10
                    boardings = int(passengers * 0.40)
                    alightings = int(passengers * 0.60)
                demand_rows.append((s_id, hour, passengers, boardings, alightings, "WEEKDAY"))

        conn.executemany(
            "INSERT INTO demand_data (stop_id, hour_of_day, passenger_count, boardings, alightings, day_of_week) "
            "VALUES (?,?,?,?,?,?)",
            demand_rows,
        )

        # 7. Insert congestion data across sample hours for all edges
        congestion_rows = []
        for e_id in edge_id_list:
            for hour in [8, 12, 18, 22]:
                if hour in (8, 18):
                    factor = 1.35 + (e_id % 4) * 0.1
                    speed = 18.0 - (e_id % 3) * 2.0
                else:
                    factor = 1.05 + (e_id % 3) * 0.05
                    speed = 32.0 - (e_id % 3) * 2.0
                congestion_rows.append((e_id, hour, round(factor, 2), round(speed, 1)))

        conn.executemany(
            "INSERT INTO congestion_data (edge_id, hour_of_day, congestion_factor, avg_speed_kmh) "
            "VALUES (?,?,?,?)",
            congestion_rows,
        )

        # 8. Seed sample optimization history
        s01_id = stop_id_map["S01"]
        s02_id = stop_id_map["S02"]
        cur = conn.execute(
            "INSERT INTO optimization_runs (from_stop_id, to_stop_id, mode, algorithm, optimization_time_ms, score) "
            "VALUES (?,?,?,?,?,?)",
            (s01_id, s02_id, "balanced", "astar", 3.42, 94.5),
        )
        sample_run_id = cur.lastrowid
        conn.execute(
            "INSERT INTO optimization_results "
            "(run_id, rank, cost, distance_km, time_min, fare, transfers, num_stops, route_path, score) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (sample_run_id, 1, 6.2, 1.6, 5.5, 8.0, 0, 2,
             json.dumps(["Central Bus Stand", "Railway Station"]), 94.5),
        )

        conn.commit()

    print(f"[SEED] Successfully seeded:")
    print(f"       - {len(STOPS)} bus stops")
    print(f"       - {len(ROUTES)} bus routes")
    print(f"       - {len(EDGES)} route edges")
    print(f"       - {len(BUSES)} buses in fleet")
    print(f"       - {len(demand_rows)} demand data records")
    print(f"       - {len(congestion_rows)} congestion time slots")
    print(f"       - 1 demo optimization run & result")


if __name__ == "__main__":
    seed()
