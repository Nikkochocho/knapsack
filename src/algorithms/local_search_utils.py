"""
algorithms/local_search_utils.py
================================
Utility functions for evaluating and generating candidate paths.
"""

from    collections import deque
import  config
from    algorithms.converter import Converter


INITIAL_SPEED = 100.0


def evaluate_path(path: list, initial_speed: float = None, time_limit: float = None) -> float:
    """Compute the total time of path `path`, returning -inf if it exceeds time_limit."""
    speed = initial_speed if initial_speed is not None else INITIAL_SPEED

    total_time = 0.0

    for node in path[1:]:
        if config.MULTIVERSE_MODE:
            map_id, (r, c) = node
            weights     = config.MULTIVERSE.maps[map_id].grid_weights
            terrain_map = config.MULTIVERSE.maps[map_id].terrain_map
        else:
            r, c = node
            weights     = config.GRID_WEIGHTS
            terrain_map = config.TERRAIN_MAP

        weight  = weights[r][c] or 1.0
        terrain = terrain_map[r][c] if terrain_map else None
        factor  = config.FATORES.get(terrain.name, 1.0) if terrain else 1.0

        delay = round((weight / speed) * 1000)
        delay = max(50, min(delay, 2000))
        total_time += delay / 1000

        speed = speed * factor
        speed = max(config.VELOCIDADE_MIN, min(speed, config.VELOCIDADE_MAX))

    if time_limit is not None and total_time > time_limit:
        return float('-inf')

    return total_time


def _initial_path(start: str, goal: str, time_limit: float = None) -> list | None:
    """Simple BFS to generate a valid initial solution.
    If time_limit is given and the full path exceeds it, returns the
    prefix up to the last node within the limit (an incomplete path).
    """
    if config.MULTIVERSE_MODE:
        start_node = Converter.super_str_to_key(start)
        goal_node  = Converter.super_str_to_key(goal)
        def neighbors(state):
            return [v for v, _ in _multiverse_successors(state)]
    else:
        start_node = Converter.str_to_tuple(start)
        goal_node  = Converter.str_to_tuple(goal)
        def neighbors(state):
            r, c = state
            result = []
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if (0 <= nr < config.GRID_ROWS and 0 <= nc < config.GRID_COLS
                        and config.GRID_MAP[nr][nc] == 0):
                    result.append((nr, nc))
            return result

    queue, visited = deque([[start_node]]), {start_node}
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == goal_node:
            if time_limit is None:
                return path
            fitness = evaluate_path(path, time_limit=time_limit)
            if fitness != float('-inf'):
                return path
            return _truncate_to_limit(path, time_limit)

        for neighbor in neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return None


def _truncate_to_limit(path: list, time_limit: float) -> list:
    """Return the prefix of `path` that fits within time_limit."""
    speed        = INITIAL_SPEED
    time_elapsed = 0.0

    for idx, node in enumerate(path[1:], start=1):
        if config.MULTIVERSE_MODE:
            map_id, (r, c) = node
            weights     = config.MULTIVERSE.maps[map_id].grid_weights
            terrain_map = config.MULTIVERSE.maps[map_id].terrain_map
        else:
            r, c = node
            weights     = config.GRID_WEIGHTS
            terrain_map = config.TERRAIN_MAP

        weight  = weights[r][c] or 1.0
        terrain = terrain_map[r][c] if terrain_map else None
        factor  = config.FATORES.get(terrain.name, 1.0) if terrain else 1.0

        delay = max(50, min(round((weight / speed) * 1000), 2000))
        time_elapsed += delay / 1000

        if time_elapsed > time_limit:
            return path[:idx] if idx > 1 else path[:1]

        speed = max(config.VELOCIDADE_MIN, min(speed * factor, config.VELOCIDADE_MAX))

    return path


def _bfs_segment(origin, destination) -> list | None:
    """Random valid path between two nodes — gives local search some variation."""
    import random

    if origin == destination:
        return [origin]

    if config.MULTIVERSE_MODE:
        def neighbors(n): return [v for v, _ in _multiverse_successors(n)]
        def coords(n): return n[1]
    else:
        def neighbors(state):
            r, c = state
            result = []
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if (0 <= nr < config.GRID_ROWS and 0 <= nc < config.GRID_COLS
                        and config.GRID_MAP[nr][nc] == 0):
                    result.append((nr, nc))
            return result
        def coords(n): return n

    max_steps = config.GRID_ROWS * config.GRID_COLS
    for _ in range(20):
        current  = origin
        path     = [current]
        visited  = {current}

        for _ in range(max_steps):
            if current == destination:
                return path

            candidates = [v for v in neighbors(current) if v not in visited]
            if not candidates:
                break

            cur_r, cur_c = coords(current)
            delta_row = coords(destination)[0] - cur_r
            delta_col = coords(destination)[1] - cur_c
            directional = [
                v for v in candidates
                if (coords(v)[0] - cur_r) * (1 if delta_row >= 0 else -1) >= 0
                or (coords(v)[1] - cur_c) * (1 if delta_col >= 0 else -1) >= 0
            ]
            chosen_pool = directional if directional and random.random() < 0.7 else candidates

            next_node = random.choice(chosen_pool)
            path.append(next_node)
            visited.add(next_node)
            current = next_node

    # fallback: plain BFS
    queue, visited = deque([[origin]]), {origin}
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == destination:
            return path
        for neighbor in neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return None


def _multiverse_successors(state: tuple) -> list[tuple]:
    """Generate successors for the multiverse supergraph.
    state = (map_id, (r, c)) — returns [(new_state, cost), ...]
    """
    map_id, (r, c) = state
    mv  = config.MULTIVERSE
    maz = mv.maps[map_id]

    neighbors = []

    # ── local grid neighbors ─────────────────────────────────────────
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < maz.grid_rows and 0 <= nc < maz.grid_cols \
                and maz.grid_map[nr][nc] == 0:
            cost = maz.grid_weights[nr][nc] or 1.0
            neighbors.append(((map_id, (nr, nc)), cost))

    # ── portals leaving this map at position (r, c) ──────────────────
    for portal in mv.portals:
        if portal.map_a == map_id and portal.row == r and portal.col == c:
            neighbors.append(((portal.map_b, (portal.row, portal.col)), portal.cost))

    return neighbors