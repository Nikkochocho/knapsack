"""
config.py
=========
Centraliza toda a configuração do problema e da interface.

Modos de operação
-----------------
MULTIVERSE_MODE = False  →  comportamento original (mapa único)
MULTIVERSE_MODE = True   →  múltiplos mapas conectados por portais
"""

from __future__     import annotations
from typing         import Optional
from maze_generator import generate_open_grid, maze_to_config_format


import sys

# ─────────────────────────────────────────────────────────────────────────────
# Parâmetros de geração
# ─────────────────────────────────────────────────────────────────────────────

MAZE_LOGICAL_ROWS: int   = 8
MAZE_LOGICAL_COLS: int   = 8
MAZE_SEED: Optional[int] = None   # None = aleatório; ex.: 42 para fixo


# ─────────────────────────────────────────────────────────────────────────────
# Construção do grafo (mapa único)
# ─────────────────────────────────────────────────────────────────────────────

def _build_graph( grid:    list[list[int]],
                  weights: list[list[float]],
                ) -> dict[str, list[tuple[str, float]]]:
    """Monta um grafo plano para configuração comum."""
    rows, cols = len(grid), len(grid[0])
    graph: dict[str, list[tuple[str, float]]] = {}

    def node(r: int, c: int) -> str:
        return f"({r},{c})"

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                continue
            neighbors: list[tuple[str, float]] = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                    cost = weights[nr][nc] or 1.0
                    neighbors.append((node(nr, nc), cost))
            graph[node(r, c)] = neighbors
    return graph


# ─────────────────────────────────────────────────────────────────────────────
# Construção do supergrafo (multiverso)
# ─────────────────────────────────────────────────────────────────────────────

def _build_super_graph(mv) -> dict[str, list[tuple[str, float]]]:
    """Monta um único grafo plano com nós no formato "M{id}:(r,c)"."""
    super_graph: dict[str, list[tuple[str, float]]] = {}

    # ── arestas intra-mapa ───────────────────────────────────────────────────
    for i, maze in enumerate(mv.maps):
        prefix = f"M{i}:"
        local  = _build_graph(maze.grid_map, maze.grid_weights)
        for local_node, neighbors in local.items():
            super_node = prefix + local_node
            super_graph[super_node] = [
                (prefix + nb, cost) for nb, cost in neighbors
            ]

    # ── arestas de portal ────────────────────────────────────────────────────
    for portal in mv.portals:
        node_a = f"M{portal.map_a}:({portal.row},{portal.col})"
        node_b = f"M{portal.map_b}:({portal.row},{portal.col})"
        if node_a in super_graph and node_b in super_graph:
            super_graph[node_a].append((node_b, portal.cost))

    return super_graph


# ─────────────────────────────────────────────────────────────────────────────
# Aplicar resultado de geração — mapa único
# ─────────────────────────────────────────────────────────────────────────────

def _apply(result) -> None:
    """Aplica um MazeResult nos globais deste módulo (modo mapa único)."""
    m = sys.modules[__name__]
    gm, gw, gr, gc = maze_to_config_format(result)
    m.GRID_MAP       = gm
    m.GRID_WEIGHTS   = gw
    m.GRID_ROWS      = gr
    m.GRID_COLS      = gc
    m.ACTIVE_SEED    = result.seed
    m.TERRAIN_MAP    = result.terrain_map
    m.GRAPH          = _build_graph(gm, gw)
    m.STATES         = list(m.GRAPH.keys())
    m.START_NODE     = "(0,0)"
    m.GOAL_NODE      = f"({gr - 1},{gc - 1})"
    m.NODE_POSITIONS = {
        f"({r},{c})": (c, r)
        for r in range(gr)
        for c in range(gc)
        if gm[r][c] == 0
    }
    m.MULTIVERSE_MODE = False

def regenerate_maze(seed: Optional[int] = None) -> None:
    """Regera o mapa em modo mapa único."""
    _apply(generate_open_grid(
        rows=MAZE_LOGICAL_ROWS,
        cols=MAZE_LOGICAL_COLS,
        seed=seed,
    ))


# ─────────────────────────────────────────────────────────────────────────────
# Aplicar resultado de geração — multiverso
# ─────────────────────────────────────────────────────────────────────────────

def _apply_active_map(map_id: int) -> None:
    """Atualiza GRID_MAP / TERRAIN_MAP / GRAPH para o mapa visualizado."""
    m = sys.modules[__name__]
    if m.MULTIVERSE is None:
        return
    maz = m.MULTIVERSE.maps[map_id]
    gm, gw, gr, gc = maze_to_config_format(maz)
    m.GRID_MAP      = gm
    m.GRID_WEIGHTS  = gw
    m.GRID_ROWS     = gr
    m.GRID_COLS     = gc
    m.TERRAIN_MAP   = maz.terrain_map
    m.ACTIVE_MAP_ID = map_id
    # Grafo local usado pela heurística Manhattan (por mapa)
    m.GRAPH         = _build_graph(gm, gw)


def apply_multiverse(mv) -> None:
    """Ativa o modo multiverso e atualiza todos os globais."""
    m = sys.modules[__name__]
    m.MULTIVERSE      = mv
    m.SUPER_GRAPH     = _build_super_graph(mv)
    m.ACTIVE_MAP_ID   = 0
    m.MULTIVERSE_MODE = True

    # Globais de grade: começa no mapa 0
    _apply_active_map(0)

    # Estados e nós início/fim no espaço do supergrafo
    m.STATES     = list(m.SUPER_GRAPH.keys())
    gr = mv.maps[0].grid_rows
    gc = mv.maps[0].grid_cols
    m.START_NODE = "M0:(0,0)"
    m.GOAL_NODE  = f"M{mv.goal_map}:({mv.maps[mv.goal_map].grid_rows-1},{mv.maps[mv.goal_map].grid_cols-1})"


# ─────────────────────────────────────────────────────────────────────────────
# Placeholders — preenchidos imediatamente por _apply()
# ─────────────────────────────────────────────────────────────────────────────

GRID_MAP:       list[list[int]]   = []
GRID_WEIGHTS:   list[list[float]] = []
GRID_ROWS:      int               = 0
GRID_COLS:      int               = 0
ACTIVE_SEED:    Optional[int]     = None
TERRAIN_MAP                       = None
GRAPH:          dict              = {}
STATES:         list[str]         = []
START_NODE:     str               = "(0,0)"
GOAL_NODE:      str               = "(14,14)"
NODE_POSITIONS: dict              = {}
ACTIVE_METHOD:  str               = ''
LAST_VELOCITY:  float             = 1.0  
TEMPO_LIMITE:   float             = 10.0
GOAL_REACHED:   bool              = True

FATORES: dict[str, float] = {
    'plains':   1.2,
    'forest':   1.0,
    'swamp':    0.7,
    'mountain': 0.5,
}
VELOCIDADE_MIN: float = 10.0   # ← adicione
VELOCIDADE_MAX: float = 200.0  # ← adicione

# Multiverso (inicialmente None / desativado)
MULTIVERSE_MODE: bool  = False
MULTIVERSE             = None
PORTAL_COST:     float = 1.0
SUPER_GRAPH:     dict  = {}
ACTIVE_MAP_ID:   int   = 0

_apply(generate_open_grid(
    rows=MAZE_LOGICAL_ROWS,
    cols=MAZE_LOGICAL_COLS,
    seed=MAZE_SEED,
))


# ─────────────────────────────────────────────────────────────────────────────
# Configurações de UI
# ─────────────────────────────────────────────────────────────────────────────

SEARCH_METHODS: list[str] = [
    'Subida de Encosta',
    'Subida de Encosta (Tentativa)',
    'Têmpera Simulada',
    'Algoritmo Genético'
]

COLORS: dict[str, str] = {
    'bg':              '#1A2018',   
    'panel':           '#1A2018',
    'panel_border':    '#2A3828',   

    'accent':          '#4F8EF7',   # azul royal — mantido
    'accent2':         "#C98C47",  
    'index':           "#C46FFF",
    'success':         '#5AB87A',   
    'warning':         '#D4A840',   
    'danger':          '#C04848',   

    'text':            '#D8E0C8',   
    'text_dim':        '#788870',   

    # tiles por terreno
    'tile_free':       '#243020',   
    'tile_w2':         '#1C2C18',  
    'tile_w3':         '#202818',   
    'tile_w5':         '#222430',   
    'tile_wall':       '#141814',   
    'tile_border':     '#2A3828',   

    # tile portal
    'tile_portal':     '#1A2430',
    'tile_portal_glow':'#4F8EF7',   # mesmo azul do accent

    # texto de peso
    'weight_normal':   '#384830',
    'weight_medium':   '#786020',
    'weight_heavy':    '#584018',
    'weight_critical': '#782020',

    # nós especiais
    'node_start':      '#1A2C40',   
    'node_goal':       '#1E3428',   
    'node_path':       '#2A3430',   
    'node_default':    '#243020',

    'node_glow_start': '#4F8EF7',   
    'node_glow_goal':  '#5AB87A',   
    'node_glow_path':  '#A87840',   

    # arestas
    'edge_default':    '#2A3828',
    'edge_path':       '#4F8EF7',
    'edge_glow':       '#2A5898',

    'grid':            '#141814',
}

WINDOW = {
    'title':      'Visualizador interativo de algoritmos de busca — Mochila',
    'width':      1420,
    'height':     980,
    'min_width':  900,
    'min_height': 620,
}