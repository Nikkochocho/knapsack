"""
algorithms/hill_climbing_random_restart.py
===================
Hill Climbing with Random Restarts (Hill Climbing with tolerance).
"""

import  config
from    search_result                import SearchResult
from    algorithms.local_search        import LocalSearch
from    algorithms.converter         import Converter
from    algorithms.local_search_utils import _initial_path, evaluate_path, INITIAL_SPEED


TMAX_DEFAULT = 20


def search(start: str, goal: str, graph: dict,
           tmax=TMAX_DEFAULT, t1=None, tf=None, fr=None,
           initial_speed=None, tempo_limite=None) -> SearchResult:

    initial_path = _initial_path(start, goal, tempo_limite=tempo_limite)
    if initial_path is None:
        return SearchResult()

    ls    = LocalSearch()
    speed = initial_speed if initial_speed is not None else INITIAL_SPEED
    initial_value = evaluate_path(initial_path, initial_speed=speed)

    if initial_value == float('-inf') or initial_value == 0.0:   # ← truncated path, no valid solution
        converter  = Converter.key_to_super_str if config.MULTIVERSE_MODE else Converter.tuple_to_str
        time_taken = LocalSearch.path_time(initial_path, speed)
        return SearchResult(
            path=  [converter(n) for n in initial_path],
            cost=  round(float(time_taken), 2),
            depth= len(initial_path) - 1,
            profit= 0.0
        )

    path, value, speed, time_taken = ls.hill_climbing_with_retry(
        initial_path, initial_value, tmax, speed, tempo_limite=tempo_limite
    )

    converter = Converter.key_to_super_str if config.MULTIVERSE_MODE else Converter.tuple_to_str
    return SearchResult(
        path=[converter(n) for n in path],
        cost=round(float(time_taken), 2),
        depth=len(path) - 1,
        profit= round((time_taken - initial_value) / tempo_limite * 100, 2),
    )