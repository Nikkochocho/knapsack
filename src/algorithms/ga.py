"""
algorithms/ga.py
===================
Genetic Algorithm (GA).
"""

import  config
from    search_result                 import SearchResult
from    algorithms.converter          import Converter
from    algorithms.local_search       import LocalSearch
from    algorithms.genetic_algorithm  import AG
from    algorithms.local_search_utils  import INITIAL_SPEED


def search(start: str, goal: str, graph: dict,
           initial_speed=None, tempo_limite=None,
           tp=10, ng=20, tc=0.8, tm=0.1, ig=0.2,
           **_) -> SearchResult:

    speed = initial_speed if initial_speed is not None else INITIAL_SPEED

    initial_path, final_path, initial_value, final_value = AG(
        start=start, goal=goal,
        velocidade=speed, tempo_limite=tempo_limite or 0.0,
        tp=tp, ng=ng, tc=tc, tm=tm, ig=ig,
    )

    if final_path is None:
        return SearchResult()

    converter  = Converter.key_to_super_str if config.MULTIVERSE_MODE else Converter.tuple_to_str
    time_taken = LocalSearch.path_time(final_path, speed)
    return SearchResult(
        path=        [converter(n) for n in final_path],
        cost=        round(float(time_taken), 2),
        depth=       len(final_path) - 1,
        profit=      round((final_value - initial_value) / tempo_limite * 100, 2) if tempo_limite and tempo_limite > 0 else round(final_value - initial_value, 2),
    )