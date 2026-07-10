"""
multiverse.py
=============
Generates N independent maps and connects them via bidirectional portals.
"""

from __future__ import annotations

import random
from   dataclasses import dataclass, field
from   typing      import Optional

from maze_generator import MazeResult, generate_open_grid



# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Portal:
    """Portal edge between two maps at the same position (r, c)."""
    map_a: int
    map_b: int
    row:   int      # coordinate in the EXPANDED grid (0..grid_rows-1)
    col:   int      # coordinate in the EXPANDED grid (0..grid_cols-1)
    cost:  float = 1.0


@dataclass
class MultiverseResult:
    """Holds all generated maps and the portals connecting them."""
    maps:      list[MazeResult]
    portals:   list[Portal]
    n_maps:    int
    start_map: int = 0
    goal_map:  int = 0   # filled in by generate_multiverse


# ─────────────────────────────────────────────────────────────────────────────
# Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_multiverse(
    n_maps:          int   = 6,
    rows:            int   = 8,
    cols:            int   = 8,
    portals_per_map: int   = 2,
    portal_cost:     float = 1.0,
    seed:            Optional[int] = None,
) -> MultiverseResult:
    """Generate n_maps maps and connect them with portals."""
    if seed is None:
        seed = random.randint(0, 2 ** 32 - 1)
    rng = random.Random(seed)

    # ── 1. Generate maps ─────────────────────────────────────────────────────
    maps: list[MazeResult] = [
        generate_open_grid(rows, cols, rng.randint(0, 2 ** 32 - 1))
        for _ in range(n_maps)
    ]

    # ── 2. Pre-compute free cells for each map ───────────────────────────────
    def free_cells(m: MazeResult) -> set[tuple[int, int]]:
        return {
            (r, c)
            for r in range(m.grid_rows)
            for c in range(m.grid_cols)
            if m.grid_map[r][c] == 0
        }

    free: list[set[tuple[int, int]]] = [free_cells(m) for m in maps]

    portals: list[Portal] = []

    def add_portal(a: int, b: int) -> bool:
        """Try to add a bidirectional portal between map a and map b."""
        shared = list(free[a] & free[b])
        if not shared:
            return False
        r, c = rng.choice(shared)
        portals.append(Portal(a, b, r, c, portal_cost))
        portals.append(Portal(b, a, r, c, portal_cost))
        return True

    # ── 3. Spanning tree over the maps (guarantees M0 → M_final connectivity) ─
    order = list(range(n_maps))
    rng.shuffle(order)
    connected = {order[0]}
    remaining = set(order[1:])
    attempts  = 0

    while remaining and attempts < n_maps * 10:
        attempts += 1
        a = rng.choice(list(connected))
        b = rng.choice(list(remaining))
        if add_portal(a, b):
            connected.add(b)
            remaining.discard(b)

    # ── 4. Extra portals ──────────────────────────────────────────────────────
    extra_count = portals_per_map * n_maps
    for _ in range(extra_count * 3):   # extra attempts to account for collisions
        if len(portals) // 2 >= extra_count + (n_maps - 1):
            break
        if n_maps < 2:
            break
        a, b = rng.sample(range(n_maps), 2)
        add_portal(a, b)

    return MultiverseResult(
        maps=maps,
        portals=portals,
        n_maps=n_maps,
        start_map=0,
        goal_map=n_maps - 1,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Query utilities
# ─────────────────────────────────────────────────────────────────────────────

def portals_of_map(mv: MultiverseResult, map_id: int) -> list[Portal]:
    """Return the portals that originate from map map_id."""
    return [p for p in mv.portals if p.map_a == map_id]


def portal_cells_of_map(mv: MultiverseResult, map_id: int) -> set[tuple[int, int]]:
    """Return the set of (row, col) positions that are portals in map map_id."""
    return {(p.row, p.col) for p in mv.portals if p.map_a == map_id}