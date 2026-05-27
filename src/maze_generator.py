"""
maze_generator.py
=================
Geração procedural de mapas de grid aberto.
"""

from    __future__  import annotations
import  random
from    dataclasses import dataclass, field
from    typing      import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Tipos de terreno
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TerrainType:
    name: str
    weight: float
    probability: float   # deve somar 1.0 no conjunto escolhido


TERRAINS: list[TerrainType] = [
    TerrainType("plains",   1.0, 0.25),  # fator 1.0  — sem perda
    TerrainType("forest",   2.0, 0.25),  # fator 0.5  — perde metade
    TerrainType("swamp",    3.0, 0.25),  # fator 0.33 — perde 2/3
    TerrainType("mountain", 5.0, 0.25),  # fator 0.2  — perde 4/5
]

TERRAIN_COUNTS: dict[str, int] = {
    "plains":   25,
    "forest":   20,
    "swamp":    12,
    "mountain":  7,
}

# Validação simples
assert abs(sum(t.probability for t in TERRAINS) - 1.0) < 1e-6, \
    "Probabilidades dos terrenos devem somar 1.0"

EXTRA_EDGE_PROBABILITY: float = 0.75  # 0.0 = perfeito, 1.0 = remove todas as paredes

# ─────────────────────────────────────────────────────────────────────────────
# Geração de terreno
# ─────────────────────────────────────────────────────────────────────────────

def _build_terrain_pool(
    rng: random.Random,
    total_cells: int,
    counts: Optional[dict[str, int]] = None,
) -> list[TerrainType]:
    """
    Monta um pool com quantidades exatas de cada terreno.
    
    Se counts for None, divide igualmente (resto vai para o primeiro terreno).
    Exemplo: counts={"plains": 20, "forest": 15, "swamp": 10, "mountain": 5}
    """
    terrain_map_by_name = {t.name: t for t in TERRAINS}
    
    if counts is None:
        base = total_cells // len(TERRAINS)
        remainder = total_cells % len(TERRAINS)
        counts = {t.name: base for t in TERRAINS}
        counts[TERRAINS[0].name] += remainder

    # Valida
    assigned = sum(counts.values())
    assert assigned == total_cells, (
        f"Soma dos counts ({assigned}) != total de células ({total_cells})"
    )
    assert all(name in terrain_map_by_name for name in counts), \
        f"Nome de terreno inválido em counts. Válidos: {[t.name for t in TERRAINS]}"

    pool: list[TerrainType] = []
    for name, qty in counts.items():
        pool.extend([terrain_map_by_name[name]] * qty)

    rng.shuffle(pool)
    return pool

def _pick_from_pool(
    rng: random.Random,
    pool: list[TerrainType],
    neighbors: list[Optional[TerrainType]],
    penalty: float = 0.15,
) -> TerrainType:
    """
    Escolhe um terreno do pool penalizando tipos já nos vizinhos.
    Remove e retorna o terreno escolhido do pool (in-place).
    """
    neighbor_counts: dict[str, int] = {}
    for n in neighbors:
        if n is not None:
            neighbor_counts[n.name] = neighbor_counts.get(n.name, 0) + 1

    # Peso de cada posição no pool
    weights = [
        max(0.0, 1.0 - penalty * neighbor_counts.get(t.name, 0))
        for t in pool
    ]
    total = sum(weights)

    if total <= 0:
        idx = rng.randrange(len(pool))
    else:
        r = rng.random() * total
        cumulative = 0.0
        idx = len(pool) - 1
        for i, w in enumerate(weights):
            cumulative += w
            if r < cumulative:
                idx = i
                break

    chosen = pool[idx]
    pool.pop(idx)
    return chosen

# ─────────────────────────────────────────────────────────────────────────────
# Union-Find (Disjoint Set Union — DSU)
# ─────────────────────────────────────────────────────────────────────────────

class UnionFind:
    """Estrutura Union-Find com compressão de caminho e união por rank."""

    def __init__(self, n: int):
        """Método Construtor."""
        self._parent = list(range(n))
        self._rank   = [0] * n

    def find(self, x: int) -> int:
        """Retorna o representante do componente de x (com compressão de caminho)."""
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]  # path halving
            x = self._parent[x]
        return x

    def union(self, x: int, y: int) -> bool:
        """
        Une os componentes de x e y.
        Retorna True se eram componentes distintos (a parede foi removida),
        False se já pertenciam ao mesmo componente.
        """
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        # União por rank
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._parent[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Resultado da geração
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MazeResult:
    """Contém todos os dados gerados pelo algoritmo de geração de mapa."""
    rows:         int
    cols:         int
    grid_map:     list[list[int]]
    grid_weights: list[list[float]]
    terrain_map:  list[list[Optional[TerrainType]]]
    seed:         int

    # dimensões reais do grid expandido
    @property
    def grid_rows(self) -> int:
        return 2 * self.rows - 1

    @property
    def grid_cols(self) -> int:
        return 2 * self.cols - 1


# ─────────────────────────────────────────────────────────────────────────────
# Algoritmo principal
# ─────────────────────────────────────────────────────────────────────────────

def generate_open_grid(rows: int = 8,
                       cols: int = 8,
                       seed: Optional[int] = None,
                      ) -> MazeResult:
    """Gera um grid aberto sem paredes — só pesos de terreno."""
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    rng = random.Random(seed)

    G_ROWS = 2 * rows - 1
    G_COLS = 2 * cols - 1

    grid_map:    list[list[int]]                   = [[0] * G_COLS for _ in range(G_ROWS)]
    terrain_map: list[list[Optional[TerrainType]]] = [[None] * G_COLS for _ in range(G_ROWS)]
    pool = _build_terrain_pool(rng, G_ROWS * G_COLS, _counts_for_size(G_ROWS * G_COLS))

    for r in range(G_ROWS):
        for c in range(G_COLS):
            neighbors = [
                terrain_map[r - 1][c] if r > 0 else None,      # cima
                terrain_map[r][c - 1] if c > 0 else None,      # esquerda
                terrain_map[r - 1][c - 1] if r > 0 and c > 0 else None,  # diagonal
                terrain_map[r - 1][c + 1] if r > 0 and c + 1 < G_COLS else None,  # diagonal
            ]
            terrain_map[r][c] = _pick_from_pool(rng, pool, neighbors, penalty=0.5)

    grid_weights: list[list[float]] = [
        [terrain_map[r][c].weight for c in range(G_COLS)]
        for r in range(G_ROWS)
    ]

    return MazeResult(
        rows=rows,
        cols=cols,
        grid_map=grid_map,
        grid_weights=grid_weights,
        terrain_map=terrain_map,
        seed=seed,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Conversão para o formato esperado por config.py / _build_graph
# ─────────────────────────────────────────────────────────────────────────────

def maze_to_config_format(result: MazeResult,
                         ) -> tuple[list[list[int]], list[list[float]], int, int]:
    """Converte um MazeResult para as estruturas usadas em config.py."""
    return (
        result.grid_map,
        result.grid_weights,
        result.grid_rows,
        result.grid_cols,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de debug / inspeção
# ─────────────────────────────────────────────────────────────────────────────

_TERRAIN_CHAR: dict[str, str] = {
    "plains":   ".",
    "forest":   "F",
    "swamp":    "S",
    "mountain": "M",
}

def print_maze(result: MazeResult) -> None:
    """Imprime o grid no terminal para inspeção rápida."""
    G_ROWS = result.grid_rows
    G_COLS = result.grid_cols
    print(f"Seed: {result.seed}  |  Grid lógico: {result.rows}×{result.cols}"
          f"  |  Grid expandido: {G_ROWS}×{G_COLS}")
    print("+" + "─" * (G_COLS * 2 - 1) + "+")
    for r in range(G_ROWS):
        row_str = ""
        for c in range(G_COLS):
            if result.grid_map[r][c] == 1:
                row_str += "██"
            else:
                t = result.terrain_map[r][c]
                ch = _TERRAIN_CHAR.get(t.name, "?") if t else "?"
                row_str += f"{ch} "
        print(f"|{row_str.rstrip()}|")
    print("+" + "─" * (G_COLS * 2 - 1) + "+")


def terrain_stats(result: MazeResult) -> dict[str, int]:
    """Conta quantas células de cada terreno foram geradas."""
    counts: dict[str, int] = {t.name: 0 for t in TERRAINS}
    for r in range(result.grid_rows):
        for c in range(result.grid_cols):
            if result.grid_map[r][c] == 0:
                t = result.terrain_map[r][c]
                if t:
                    counts[t.name] = counts.get(t.name, 0) + 1
    return counts

def _counts_for_size(total: int) -> dict[str, int]:
    """Escala TERRAIN_COUNTS proporcionalmente para qualquer tamanho de mapa."""
    base_total = sum(TERRAIN_COUNTS.values())
    scaled = {}
    remainder = total
    names = list(TERRAIN_COUNTS)
    for name in names[:-1]:
        qty = round(TERRAIN_COUNTS[name] / base_total * total)
        scaled[name] = qty
        remainder -= qty
    scaled[names[-1]] = remainder  # último absorve o arredondamento
    return scaled

# ─────────────────────────────────────────────────────────────────────────────
# Execução standalone — teste rápido
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    maze = generate_open_grid(rows=8, cols=8, seed=42)
    print_maze(maze)
    print("\nEstatísticas de terreno:")
    for name, count in terrain_stats(maze).items():
        print(f"  {name:10s}: {count:3d} células")

    grid_map, grid_weights, g_rows, g_cols = maze_to_config_format(maze)
    print(f"\ngrid_map[0]     = {grid_map[0]}")
    print(f"grid_weights[0] = {grid_weights[0]}")