"""
algorithms/__init__.py
======================
Central registry of search algorithms.
"""


from search_result import SearchResult

# ── algorithm imports ──────────────────────────────────────────────────────

from algorithms.hill_climbing                import search as hill_climbing_search
from algorithms.hill_climbing_random_restart import search as hill_climbing_random_restart_search
from algorithms.simulated_annealing          import search as simulated_annealing_search
from algorithms.ga                           import search as ga_search

# Canonical (English) method keys — must match config.SEARCH_METHODS exactly,
# since those are the values selected in ui/control_panel.py's dropdown.
REGISTRY: dict[str, callable] = {
    'Hill Climbing':                  hill_climbing_search,
    'Hill Climbing (Random Restart)': hill_climbing_random_restart_search,
    'Simulated Annealing':            simulated_annealing_search,
    'Genetic Algorithm':              ga_search,
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