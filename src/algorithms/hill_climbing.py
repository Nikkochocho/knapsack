"""
algorithms/hill_climbing.py
===================
Hill Climbing.
"""

import  config
from    search_result                import SearchResult
from    algorithms.local_search        import LocalSearch
from    algorithms.converter         import Converter
from    algorithms.local_search_utils import _initial_path, evaluate_path, INITIAL_SPEED


def search(start: str, goal: str, graph: dict,
           tmax=None, t1=None, tf=None, fr=None,
           initial_speed=None, time_limit=None) -> SearchResult:

    initial_path = _initial_path(start, goal, time_limit=time_limit)
    if initial_path is None:
        return SearchResult()

    ls    = LocalSearch()
    speed = initial_speed if initial_speed is not None else INITIAL_SPEED
    initial_value = evaluate_path(initial_path, initial_speed=speed, time_limit=time_limit)

    if initial_value == float('-inf') or initial_value == 0.0:   # ← truncated path, no valid solution
        converter  = Converter.key_to_super_str if config.MULTIVERSE_MODE else Converter.tuple_to_str
        time_taken = LocalSearch.path_time(initial_path, speed)
        return SearchResult(
            path=  [converter(n) for n in initial_path],
            cost=  initial_value,
            depth= len(initial_path) - 1,
            profit= 0.0,
        )

    path, value, speed, time_taken = ls.hill_climbing(initial_path, initial_value, speed, time_limit=time_limit)

    converter = Converter.key_to_super_str if config.MULTIVERSE_MODE else Converter.tuple_to_str
    return SearchResult(
        path=  [converter(n) for n in path],
        cost=  round(float(time_taken), 2),
        depth= len(path) - 1,
        profit= round((time_taken - initial_value) / time_limit * 100, 2),
    )