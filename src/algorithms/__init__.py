"""
algorithms/__init__.py
======================
Registro central dos algoritmos de busca.
"""


from search_result import SearchResult

# ── imports dos algoritmos ────────────────────────────────────────────────────

from algorithms.encosta             import search as encosta_search
from algorithms.encosta_tentativa   import search as encosta_tentativa_search
from algorithms.tempera             import search as tempera_search
from algorithms.ag                  import search as ag_search

REGISTRY: dict[str, callable] = {
    'Subida de Encosta':              encosta_search,
    'Subida de Encosta (Tentativa)':  encosta_tentativa_search,
    'Têmpera Simulada':               tempera_search,
    'Algoritmo Genético':             ag_search,
}

LOCAL_SEARCH_METHODS = {
    'Subida de Encosta',
    'Subida de Encosta (Tentativa)',
    'Têmpera Simulada',
    'Algoritmo Genético',   # ← adiciona
}

def run_search(method: str, start: str, goal: str,
               graph: dict, heuristic: dict,
               depth_limit: int = None,
               heuristic_name: str = None,
               tmax: int = 20,
               t1: float = 100.0,
               tf: float = 0.1,
               fr: float = 0.95,
               tempo_limite: float = 10.0,
               tp: int = 10,        # ← adiciona
               ng: int = 20,        # ← adiciona
               tc: float = 0.8,     # ← adiciona
               tm: float = 0.1,     # ← adiciona
               ig: float = 0.2,     # ← adiciona
               ) -> SearchResult:

    fn = REGISTRY.get(method)
    if fn is None:
        print(f'[AVISO] Método "{method}" não encontrado no registro.')
        return SearchResult()

    kwargs = dict(start=start, goal=goal, graph=graph)

    if method in LOCAL_SEARCH_METHODS:
        kwargs['tmax']         = tmax
        kwargs['t1']           = t1
        kwargs['tf']           = tf
        kwargs['fr']           = fr
        kwargs['tempo_limite'] = tempo_limite

    if method == 'Algoritmo Genético':  # ← adiciona
        kwargs['tempo_limite'] = tempo_limite  # ← C_MAX da mochila
        kwargs['tp'] = tp
        kwargs['ng'] = ng
        kwargs['tc'] = tc
        kwargs['tm'] = tm
        kwargs['ig'] = ig

    return fn(**kwargs)