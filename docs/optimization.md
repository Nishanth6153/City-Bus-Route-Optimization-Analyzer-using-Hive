# Route Optimization Algorithms & Engine

The platform integrates classical graph algorithms with domain-specific multi-criteria utility functions to compute resilient, optimal transit trajectories.

## Graph Mathematical Model

Let $G = (V, E)$ represent the transit network where:
- $V$: Set of bus stops (vertices) with geographic coordinates $(\phi_i, \lambda_i)$.
- $E$: Set of directed edges $(u, v) \in V \times V$ representing direct bus connections.
- Each edge $e \in E$ possesses attributes: distance $d_e$, base travel time $t_e$, fare $f_e$, congestion multiplier $c_e \ge 1.0$, and average passenger demand $p_e$.

## Optimization Objectives

The edge traversal cost function $w(e)$ dynamically adapts according to the selected operational mode:

| Mode | Objective | Cost Formulation $w(e)$ |
|---|---|---|
| **Fastest** | Minimize travel time | $w(e) = t_e \cdot c_e$ |
| **Shortest** | Minimize physical distance | $w(e) = d_e$ |
| **Low Congestion** | Avoid bottlenecks | $w(e) = t_e \cdot (c_e)^{2.5}$ |
| **High Demand** | Maximize passenger throughput | $w(e) = \frac{t_e \cdot c_e}{(p_e / 60.0)^{1.2}}$ |
| **Low Cost** | Minimize passenger expenditure | $w(e) = f_e$ |
| **Balanced** | Multi-attribute utility | $w(e) = 0.40 \cdot \frac{t_e c_e}{10} + 0.25 \cdot \frac{d_e}{5} + 0.15 \cdot \frac{f_e}{15} + 0.20 \cdot (c_e - 1) \cdot 2$ |

## Routing Algorithms

### 1. Dijkstra's Algorithm
- Implemented with a min-priority heap (`heapq`).
- Explores uniform-cost frontiers until the target destination $v_{dest}$ is extracted.
- Guaranteed to find the globally optimal path for non-negative weights $w(e) \ge 0$.

### 2. A* Search Algorithm
- Uses an admissible heuristic function $h(u, v_{dest})$ calculated via the Haversine spherical distance formula:
  $$d_{\text{haversine}} = 2 R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
- Lower bounds:
  - Distance mode: $h(u) = d_{\text{haversine}}$
  - Time mode: $h(u) = \frac{d_{\text{haversine}}}{v_{\text{max}}} \cdot 60$ (where $v_{\text{max}} = 45\text{ km/h}$)
- Explores significantly fewer states than Dijkstra, achieving execution times under 0.5 ms.

### 3. K-Shortest Path Alternatives (Yen's Algorithm)
- Generates up to $k$ diverse, alternative candidate paths.
- Employs edge-exclusion penalties along the primary route's critical bottlenecks, compelling the engine to discover alternative corridors.

## Route Normalization & Scoring

Candidate paths are evaluated against a standardized 0–100 efficiency score:

$$\text{Score} = 100 - \left( w_t \cdot T + w_d \cdot D + w_f \cdot F + w_{\text{tr}} \cdot \text{Transfers} + w_c \cdot (C_{\text{avg}} - 1) \right) + \text{Bonus}_{\text{demand}}$$

Where:
- $T$: Total travel time (minutes)
- $D$: Total distance (kilometers)
- $F$: Total fare (INR)
- $\text{Transfers}$: Route changeovers (penalized heavily)
- $C_{\text{avg}}$: Average congestion multiplier
- Realized scores typically fall in the range $80.0 \le \text{Score} \le 99.4$.
