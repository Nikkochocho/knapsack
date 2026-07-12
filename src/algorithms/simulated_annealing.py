"""
algorithms/tempera.py
===================
Têmpera Simulada (Simulated Annealing).
"""

import  config
from    search_result                import SearchResult
from    algorithms.local_search        import LocalSearch
from    algorithms.converter         import Converter
from    algorithms.local_search_utils import _initial_path, evaluate_path, INITIAL_SPEED

T1_DEFAULT = 100.0
TF_DEFAULT = 0.1
FR_DEFAULT = 0.95


def search(start: str, goal: str, graph: dict,
           tmax=None, t1=T1_DEFAULT, tf=TF_DEFAULT, fr=FR_DEFAULT,
           initial_speed=None, tempo_limite=None) -> SearchResult:

    s1 = _initial_path(start, goal, tempo_limite=tempo_limite)
    if s1 is None:
        return SearchResult()

    bl = LocalSearch()

    vel = initial_speed if initial_speed is not None else INITIAL_SPEED
    v1 = evaluate_path(s1, initial_speed=vel)  # tempo inicial do caminho

    if v1 == float('-inf') or v1 == 0.0:          # ← caminho truncado, não há solução válida
        conv = Converter.key_to_super_str if config.MULTIVERSE_MODE else Converter.tuple_to_str
        tempo = LocalSearch.path_time(s1, vel)
        return SearchResult(
            path=  [conv(n) for n in s1],
            cost=  round(float(tempo), 2),
            depth= len(s1) - 1,
            profit= 0.0
        )

    caminho, fitness, vel, tempo = bl.simulated_annealing(
        s1, v1, t1, tf, fr,
        vel, tempo_limite=tempo_limite
    )

    conv = Converter.key_to_super_str if config.MULTIVERSE_MODE else Converter.tuple_to_str
    return SearchResult(
        path=[conv(n) for n in caminho],
        cost=round(float(tempo), 2),
        depth=len(caminho) - 1,
        profit= round((tempo - v1) / tempo_limite * 100, 2),
    )