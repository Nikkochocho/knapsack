"""
algorithms/initial_solution.py
======================
Handler for generating and displaying the initial solution via BFS.
"""

import config
import i18n
from config import COLORS
from search_result import SearchResult
from algorithms.local_search_utils import _initial_path, evaluate_path, INITIAL_SPEED
from algorithms.converter import Converter
from algorithms.local_search import LocalSearch


def handle_initial_solution(app):
    """
    Generate the initial solution via BFS and update the interface.
    'app' is the SearchApp instance.
    """
    start = app.control.start_var.get()
    goal  = app.control.goal_var.get()

    if start == goal:
        app.result.set_status(i18n.t('status_start_eq_goal'), COLORS['warning'])
        return

    app.result.set_status(i18n.t('status_generating_initial_solution'), COLORS['accent'])
    app.update()

    time_limit = app.control.time_limit_var.get()
    path = _initial_path(start, goal, time_limit=time_limit)

    if not path:
        app.result.set_status(i18n.t('status_no_path'), COLORS['danger'])
        return

    if config.MULTIVERSE_MODE:
        path_str = [Converter.key_to_super_str(n) for n in path]
    else:
        path_str = [Converter.tuple_to_str(n) for n in path]

    cost = LocalSearch.path_time(path)

    result = SearchResult(
        path=path_str,
        cost=round(float(cost), 2),
        depth=len(path_str),
        profit=None,
    )

    app.graph_canvas.reset_visited()
    app.graph_canvas.render(path=path_str, start=start, goal=goal)
    app.result.update_result(result)
    app.result.set_status(
        i18n.t('status_initial_solution_done', n=len(path_str), cost=cost),
        COLORS['text_dim'])