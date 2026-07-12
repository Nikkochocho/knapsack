"""
algorithms/local_search.py
================================
Implementation of the Local Search algorithms.
"""

from    math import exp
import  random
import  config
from    algorithms.local_search_utils import _bfs_segment, evaluate_path, INITIAL_SPEED

class LocalSearch(object):

    @staticmethod
    def path_time(path: list, initial_speed: float = None, tempo_limite: float = None) -> float:
        """Compute the total travel time of path `path`, mirroring the animation."""
        speed = initial_speed if initial_speed is not None else INITIAL_SPEED

        total_time = 0.0

        for node in path[1:]:
            if config.MULTIVERSE_MODE:
                map_id, (r, c) = node
                weights      = config.MULTIVERSE.maps[map_id].grid_weights
                terrain_map  = config.MULTIVERSE.maps[map_id].terrain_map
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

        if tempo_limite is not None and total_time > tempo_limite:
            return float('-inf')

        return total_time

    @staticmethod
    def successors(path: list, initial_speed: float = None, tempo_limite: float = None) -> tuple[list, float]:
        """Generate a neighbor by replacing a random segment with an alternative BFS path."""
        n = len(path)
        if n <= 3:
            return path, evaluate_path(path, initial_speed, tempo_limite)

        i = random.randint(1, n - 3)
        j = random.randint(i + 2, n - 1)

        alternative = _bfs_segment(path[i], path[j])
        if alternative is None:
            return path, evaluate_path(path, initial_speed, tempo_limite)

        new_path  = path[:i] + alternative + path[j+1:]
        new_value = evaluate_path(new_path, initial_speed, tempo_limite)

        return new_path, new_value

    def hill_climbing(self, initial_path: list, initial_value: float, speed: float = None, tempo_limite: float = None) -> tuple[list, float, float, float]:
        """Simple hill climbing: maximizes travel time, stops when there's no improvement."""
        current_path  = initial_path
        current_value = initial_value

        while True:
            candidates = [LocalSearch.successors(current_path, speed, tempo_limite) for _ in range(5)]
            better = [(p, v) for p, v in candidates if v > current_value]

            if not better:
                resolved_speed = speed or INITIAL_SPEED
                config.LAST_VELOCITY = resolved_speed
                return current_path, current_value, resolved_speed, LocalSearch.path_time(current_path, resolved_speed, tempo_limite)

            current_path, current_value = random.choice(better)

    def hill_climbing_with_retry(self, initial_path: list, initial_value: float, tmax: int, speed: float = None, tempo_limite: float = None) -> tuple[list, float, float, float]:
        """Hill climbing with retries: tolerates up to tmax iterations without improvement before stopping."""
        current_path  = initial_path
        current_value = initial_value
        stagnation    = 0

        while True:
            candidates = [LocalSearch.successors(current_path, speed, tempo_limite) for _ in range(5)]
            better = [(p, v) for p, v in candidates if v > current_value]

            if better:
                current_path, current_value = random.choice(better)
                stagnation = 0
            elif stagnation < tmax:
                stagnation += 1
            else:
                resolved_speed = speed or INITIAL_SPEED
                config.LAST_VELOCITY = resolved_speed
                return current_path, current_value, resolved_speed, LocalSearch.path_time(current_path, resolved_speed, tempo_limite)

    def simulated_annealing(self, initial_path: list, initial_value: float, t1: float, tf: float, fr: float, speed: float = None, tempo_limite: float = None) -> tuple[list, float, float, float]:
        """Simulated Annealing: accepts worse moves with probability exp(-diff/temperature) to escape local optima."""
        current_path  = initial_path
        current_value = initial_value
        temperature   = t1

        while temperature > tf:
            new_path, new_value = LocalSearch.successors(current_path, speed, tempo_limite)

            if new_value > current_value:
                current_path  = new_path
                current_value = new_value
            else:
                diff = current_value - new_value
                rnd  = random.random()
                if rnd < exp(-diff / temperature):
                    current_path  = new_path
                    current_value = new_value

            temperature *= fr

        resolved_speed = speed or INITIAL_SPEED
        config.LAST_VELOCITY = resolved_speed
        return current_path, current_value, resolved_speed, LocalSearch.path_time(current_path, resolved_speed, tempo_limite)