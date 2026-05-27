"""
multiverse.py
=============
Gera N mapas independentes e os conecta via portais bidirecionais.
"""

from __future__ import annotations

import random
from   dataclasses import dataclass, field
from   typing      import Optional

from maze_generator import MazeResult, generate_open_grid



# ─────────────────────────────────────────────────────────────────────────────
# Estruturas de dados
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Portal:
    """Aresta de portal entre dois mapas na mesma posição (r, c)."""
    map_a: int
    map_b: int
    row:   int      # coordenada no grid EXPANDIDO (0..grid_rows-1)
    col:   int      # coordenada no grid EXPANDIDO (0..grid_cols-1)
    cost:  float = 1.0


@dataclass
class MultiverseResult:
    """Contém todos os mapas gerados e os portais que os conectam."""
    maps:      list[MazeResult]
    portals:   list[Portal]
    n_maps:    int
    start_map: int = 0
    goal_map:  int = 0   # preenchido por generate_multiverse


# ─────────────────────────────────────────────────────────────────────────────
# Geração
# ─────────────────────────────────────────────────────────────────────────────

def generate_multiverse(
    n_maps:          int   = 6,
    rows:            int   = 8,
    cols:            int   = 8,
    portals_per_map: int   = 2,
    portal_cost:     float = 1.0,
    seed:            Optional[int] = None,
) -> MultiverseResult:
    """Gera n_maps mapas e os conecta com portais."""
    if seed is None:
        seed = random.randint(0, 2 ** 32 - 1)
    rng = random.Random(seed)

    # ── 1. Gerar mapas ───────────────────────────────────────────────────────
    maps: list[MazeResult] = [
        generate_open_grid(rows, cols, rng.randint(0, 2 ** 32 - 1))
        for _ in range(n_maps)
    ]

    # ── 2. Pré-calcular células livres de cada mapa ──────────────────────────
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
        """Tenta adicionar um portal bidirecional entre mapa a e mapa b."""
        shared = list(free[a] & free[b])
        if not shared:
            return False
        r, c = rng.choice(shared)
        portals.append(Portal(a, b, r, c, portal_cost))
        portals.append(Portal(b, a, r, c, portal_cost))
        return True

    # ── 3. Spanning-tree dos mapas (garante conectividade M0 → M_final) ──────
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

    # ── 4. Portais extras ────────────────────────────────────────────────────
    extra_count = portals_per_map * n_maps
    for _ in range(extra_count * 3):   # tenta mais vezes por causa de colisões
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
# Utilitários de consulta
# ─────────────────────────────────────────────────────────────────────────────

def portals_of_map(mv: MultiverseResult, map_id: int) -> list[Portal]:
    """Retorna os portais que saem do mapa map_id."""
    return [p for p in mv.portals if p.map_a == map_id]


def portal_cells_of_map(mv: MultiverseResult, map_id: int) -> set[tuple[int, int]]:
    """Retorna o conjunto de (row, col) que são portais no mapa map_id."""
    return {(p.row, p.col) for p in mv.portals if p.map_a == map_id}