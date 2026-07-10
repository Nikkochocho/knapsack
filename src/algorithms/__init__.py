"""
algorithms/__init__.py
======================
Central registry of search algorithms.
"""


from search_result import SearchResult

# ── algorithm imports ──────────────────────────────────────────────────────

from algorithms.encosta             import search as encosta_search
from algorithms.encosta_tentativa   import search as encosta_tentativa_search
from algorithms.tempera             import search as tempera_search
from algorithms.ag                  import search as ag_search

# Canonical (English) method keys — must match config.SEARCH_METHODS exactly,
# since those are the values selected in ui/control_panel.py's dropdown.
REGISTRY: dict[str, callable] = {
    'Hill Climbing':                  encosta_search,
    'Hill Climbing (Random Restart)': encosta_tentativa_search,
    'Simulated Annealing':            tempera_search,
    'Genetic Algorithm':              ag_search,
}

LOCAL_SEARCH_METHODS = {
    'Hill Climbing',
    'Hill Climbing (Random Restart)',
    'Simulated Annealing',
    'Genetic Algorithm',
}

def run_search(method: str, start: str, goal: str,
               graph: dict,
               tmax: int = 20,
               t1: float = 100.0,
               tf: float = 0.1,
               fr: float = 0.95,
               tempo_limite: float = 10.0,
               tp: int = 10,
               ng: int = 20,
               tc: float = 0.8,
               tm: float = 0.1,
               ig: float = 0.2,
               ) -> SearchResult:

    fn = REGISTRY.get(method)
    if fn is None:
        print(f'[WARNING] Method "{method}" not found in the registry.')
        return SearchResult()

    kwargs = dict(start=start, goal=goal, graph=graph)

    if method in LOCAL_SEARCH_METHODS:
        kwargs['tmax']         = tmax
        kwargs['t1']           = t1
        kwargs['tf']           = tf
        kwargs['fr']           = fr
        kwargs['tempo_limite'] = tempo_limite

    if method == 'Genetic Algorithm':
        kwargs['tempo_limite'] = tempo_limite  # ← knapsack's C_MAX
        kwargs['tp'] = tp
        kwargs['ng'] = ng
        kwargs['tc'] = tc
        kwargs['tm'] = tm
        kwargs['ig'] = ig

    return fn(**kwargs)