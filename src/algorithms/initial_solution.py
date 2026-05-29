"""
algorithms/initial_solution.py
======================
Handler para geração e exibição da solução inicial via BFS.
"""

import config
from config import COLORS
from search_result import SearchResult
from algorithms.busca_local_utils import _caminho_inicial, avalia_caminho, VELOCIDADE_INICIAL
from algorithms.conversor import Conversor
from algorithms.BuscaLocal import BuscaLocal


def handle_initial_solution(app):
    """
    Gera a solução inicial via BFS e atualiza a interface.
    'app' é a instância de SearchApp.
    """
    start = app.control.start_var.get()
    goal  = app.control.goal_var.get()

    if start == goal:
        app.result.set_status('⚠ Estado inicial = objetivo.', COLORS['warning'])
        return

    app.result.set_status('Gerando solução inicial...', COLORS['accent'])
    app.update()

    tempo_limite = app.control.tempo_limite_var.get()
    caminho = _caminho_inicial(start, goal, tempo_limite=tempo_limite)

    if not caminho:
        app.result.set_status('✗ Sem caminho encontrado.', COLORS['danger'])
        return

    if config.MULTIVERSE_MODE:
        path_str = [Conversor.key_to_super_str(n) for n in caminho]
    else:
        path_str = [Conversor.tuple_to_str(n) for n in caminho]

    custo = BuscaLocal.tempo_caminho(caminho)

    result = SearchResult(
        path=path_str,
        cost=round(float(custo), 2),
        depth=len(path_str),
        profit=None,
    )

    app.graph_canvas.reset_visited()
    app.graph_canvas.render(path=path_str, start=start, goal=goal)
    app.result.update_result(result)
    app.result.set_status(
        f'⬡ Solução inicial: {len(path_str)} nós, custo {custo:.3f}s.',
        COLORS['text_dim'])