"""
algorithms/ag.py
===================
Algoritmo Genético (AG).
"""

import  config
from    search_result                 import SearchResult
from    algorithms.conversor          import Conversor
from    algorithms.BuscaLocal         import BuscaLocal
from    algorithms.AlgoritmoGenetico  import AG
from    algorithms.busca_local_utils  import VELOCIDADE_INICIAL


def search(start: str, goal: str, graph: dict,
           velocidade_entrada=None, tempo_limite=None,
           tp=10, ng=20, tc=0.8, tm=0.1, ig=0.2,
           **_) -> SearchResult:                        

    vel = velocidade_entrada if velocidade_entrada is not None else VELOCIDADE_INICIAL

    si, sf, vi, vf = AG(
        start=start, goal=goal,
        velocidade=vel, tempo_limite=tempo_limite or 0.0,
        tp=tp, ng=ng, tc=tc, tm=tm, ig=ig,
    )

    if sf is None:
        return SearchResult()

    conv = Conversor.key_to_super_str if config.MULTIVERSE_MODE else Conversor.tuple_to_str
    tempo = BuscaLocal.tempo_caminho(sf, vel)
    return SearchResult(
        path=        [conv(n) for n in sf],
        cost=        round(float(tempo), 2),
        depth=       len(sf) - 1,
        profit=      round((vf - vi) / tempo_limite * 100, 2) if tempo_limite and tempo_limite > 0 else round(vf - vi, 2),
    )