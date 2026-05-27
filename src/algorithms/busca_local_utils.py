"""
algorithms/busca_local_utils.py
================================
Utilitário contendo métodos para avaliação dos caminhos.
"""

from    collections import deque
import  config
from    algorithms.conversor import Conversor


VELOCIDADE_INICIAL = 100.0


def avalia_caminho(s: list, velocidade_entrada: float = None, tempo_limite: float = None) -> float:
    """Calcula o tempo total do caminho s, retornando -inf se ultrapassar tempo_limite."""
    velocidade = velocidade_entrada if velocidade_entrada is not None else VELOCIDADE_INICIAL

    tempo_total = 0.0

    for no in s[1:]:
        if config.MULTIVERSE_MODE:
            map_id, (r, c) = no
            w  = config.MULTIVERSE.maps[map_id].grid_weights
            tm = config.MULTIVERSE.maps[map_id].terrain_map
        else:
            r, c = no
            w  = config.GRID_WEIGHTS
            tm = config.TERRAIN_MAP

        peso    = w[r][c] or 1.0
        terreno = tm[r][c] if tm else None
        fator   = config.FATORES.get(terreno.name, 1.0) if terreno else 1.0

        delay = round((peso / velocidade) * 1000)
        delay = max(50, min(delay, 2000))
        tempo_total += delay / 1000

        velocidade = velocidade * fator
        velocidade = max(config.VELOCIDADE_MIN, min(velocidade, config.VELOCIDADE_MAX))

    if tempo_limite is not None and tempo_total > tempo_limite:
        return float('-inf')

    return tempo_total


def _caminho_inicial(start: str, goal: str, tempo_limite: float = None) -> list | None:
    """BFS simples para gerar solução inicial válida.
    Se tempo_limite for fornecido e o caminho completo ultrapassar, retorna
    o prefixo até o último nó dentro do limite (caminho incompleto).
    """
    if config.MULTIVERSE_MODE:
        t_start = Conversor.super_str_to_key(start)
        t_goal  = Conversor.super_str_to_key(goal)
        def vizinhos(estado):
            return [v for v, _ in _fn_sucessores_multiverse(estado)]
    else:
        t_start = Conversor.str_to_tuple(start)
        t_goal  = Conversor.str_to_tuple(goal)
        def vizinhos(estado):
            r, c = estado
            result = []
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if (0 <= nr < config.GRID_ROWS and 0 <= nc < config.GRID_COLS
                        and config.GRID_MAP[nr][nc] == 0):
                    result.append((nr, nc))
            return result

    fila, visitado = deque([[t_start]]), {t_start}
    while fila:
        caminho = fila.popleft()
        no = caminho[-1]
        if no == t_goal:
            if tempo_limite is None:
                return caminho
            fitness = avalia_caminho(caminho, tempo_limite=tempo_limite)
            if fitness != float('-inf'):
                return caminho
            return _trunca_no_limite(caminho, tempo_limite)

        for viz in vizinhos(no):
            if viz not in visitado:
                visitado.add(viz)
                fila.append(caminho + [viz])

    return None


def _trunca_no_limite(caminho: list, tempo_limite: float) -> list:
    """Retorna o prefixo do caminho que cabe dentro do tempo_limite."""
    vel   = VELOCIDADE_INICIAL
    tempo = 0.0

    for idx, no in enumerate(caminho[1:], start=1):
        if config.MULTIVERSE_MODE:
            map_id, (r, c) = no
            w  = config.MULTIVERSE.maps[map_id].grid_weights
            tm = config.MULTIVERSE.maps[map_id].terrain_map
        else:
            r, c = no
            w  = config.GRID_WEIGHTS
            tm = config.TERRAIN_MAP

        peso    = w[r][c] or 1.0
        terreno = tm[r][c] if tm else None
        fator   = config.FATORES.get(terreno.name, 1.0) if terreno else 1.0

        delay = max(50, min(round((peso / vel) * 1000), 2000))
        tempo += delay / 1000

        if tempo > tempo_limite:
            return caminho[:idx] if idx > 1 else caminho[:1]

        vel = max(config.VELOCIDADE_MIN, min(vel * fator, config.VELOCIDADE_MAX))

    return caminho


def _bfs_trecho(origem, destino) -> list | None:
    """Caminho aleatório válido entre dois nós — para busca local ter variação."""
    import random

    if origem == destino:
        return [origem]

    if config.MULTIVERSE_MODE:
        def vizinhos(n): return [v for v, _ in _fn_sucessores_multiverse(n)]
        def coords(n): return n[1]
    else:
        def vizinhos(estado):
            r, c = estado
            result = []
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if (0 <= nr < config.GRID_ROWS and 0 <= nc < config.GRID_COLS
                        and config.GRID_MAP[nr][nc] == 0):
                    result.append((nr, nc))
            return result
        def coords(n): return n

    max_passos = config.GRID_ROWS * config.GRID_COLS
    for _ in range(20):
        atual    = origem
        caminho  = [atual]
        visitado = {atual}

        for _ in range(max_passos):
            if atual == destino:
                return caminho

            viz = [v for v in vizinhos(atual) if v not in visitado]
            if not viz:
                break

            ar, ac = coords(atual)
            dr_val = coords(destino)[0] - ar
            dc_val = coords(destino)[1] - ac
            direcionados = [
                v for v in viz
                if (coords(v)[0] - ar) * (1 if dr_val >= 0 else -1) >= 0
                or (coords(v)[1] - ac) * (1 if dc_val >= 0 else -1) >= 0
            ]
            candidatos = direcionados if direcionados and random.random() < 0.7 else viz

            proximo = random.choice(candidatos)
            caminho.append(proximo)
            visitado.add(proximo)
            atual = proximo

    # fallback: BFS normal
    fila, visitado = deque([[origem]]), {origem}
    while fila:
        cam = fila.popleft()
        no  = cam[-1]
        if no == destino:
            return cam
        for viz in vizinhos(no):
            if viz not in visitado:
                visitado.add(viz)
                fila.append(cam + [viz])
    return None


def _fn_sucessores_multiverse(estado: tuple) -> list[tuple]:
    """Gera sucessores para o supergrafo do multiverso.
    estado = (map_id, (r, c)) — retorna [(novo_estado, custo), ...]
    """
    map_id, (r, c) = estado
    mv  = config.MULTIVERSE
    maz = mv.maps[map_id]

    vizinhos = []

    # ── vizinhos locais do grid ──────────────────────────────────────
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < maz.grid_rows and 0 <= nc < maz.grid_cols \
                and maz.grid_map[nr][nc] == 0:
            custo = maz.grid_weights[nr][nc] or 1.0
            vizinhos.append(((map_id, (nr, nc)), custo))

    # ── portais saindo deste mapa na posição (r, c) ──────────────────
    for portal in mv.portals:
        if portal.map_a == map_id and portal.row == r and portal.col == c:
            vizinhos.append(((portal.map_b, (portal.row, portal.col)), portal.cost))

    return vizinhos