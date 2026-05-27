"""
algorithms/encosta.py
===================
Subida de Encosta (Hill-Climbing).
"""

import  config
from    search_result                import SearchResult
from    algorithms.BuscaLocal        import BuscaLocal
from    algorithms.conversor         import Conversor
from    algorithms.busca_local_utils import _caminho_inicial, avalia_caminho, VELOCIDADE_INICIAL


def search(start: str, goal: str, graph: dict,
           tmax=None, t1=None, tf=None, fr=None,
           velocidade_entrada=None, tempo_limite=None) -> SearchResult:

    s1 = _caminho_inicial(start, goal, tempo_limite=tempo_limite)
    if s1 is None:
        return SearchResult()

    bl  = BuscaLocal()
    vel = velocidade_entrada if velocidade_entrada is not None else VELOCIDADE_INICIAL
    v1  = avalia_caminho(s1, velocidade_entrada=vel, tempo_limite=tempo_limite)

    if v1 == float('-inf') or v1 == 0.0:          # ← caminho truncado, não há solução válida
        conv = Conversor.key_to_super_str if config.MULTIVERSE_MODE else Conversor.tuple_to_str
        tempo = BuscaLocal.tempo_caminho(s1, vel)
        return SearchResult(
            path=  [conv(n) for n in s1],
            cost=  v1,
            depth= len(s1) - 1,
            profit= 0.0,
        )

    caminho, fitness, vel, tempo = bl.encosta(s1, v1, vel, tempo_limite=tempo_limite)

    conv = Conversor.key_to_super_str if config.MULTIVERSE_MODE else Conversor.tuple_to_str
    return SearchResult(
        path=  [conv(n) for n in caminho],
        cost=  round(float(tempo), 2),
        depth= len(caminho) - 1,
        profit= round((tempo - v1) / tempo_limite * 100, 2),
    )