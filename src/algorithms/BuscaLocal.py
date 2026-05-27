"""
algorithms/BuscaLocal.py
================================
Implementação dos algoritmos de Busca Local.
"""

from    math import exp
import  random
import  config
from    algorithms.busca_local_utils import _bfs_trecho, avalia_caminho, VELOCIDADE_INICIAL

class BuscaLocal(object):

    @staticmethod
    def tempo_caminho(s: list, velocidade_entrada: float = None, tempo_limite: float = None) -> float:
        """Calcula o tempo total do caminho s, espelhando a animação."""
        velocidade = velocidade_entrada if velocidade_entrada is not None else VELOCIDADE_INICIAL

        tempo_total = 0.0

        for no in s[1:]:
            if config.MULTIVERSE_MODE:
                map_id, (r, c) = no
                w  = config.MULTIVERSE.maps[map_id].grid_weights
                tm = config.MULTIVERSE.maps[map_id].terrain_map
            else:
                r, c = no
                w  = config.GRID_WEIGHTS
                tm = config.TERRAIN_MAP

            peso    = w[r][c] or 1.0
            terreno = tm[r][c] if tm else None
            fator   = config.FATORES.get(terreno.name, 1.0) if terreno else 1.0

            delay = round((peso / velocidade) * 1000)
            delay = max(50, min(delay, 2000))
            tempo_total += delay / 1000

            velocidade = velocidade * fator
            velocidade = max(config.VELOCIDADE_MIN, min(velocidade, config.VELOCIDADE_MAX))

        if tempo_limite is not None and tempo_total > tempo_limite:
            return float('-inf')

        return tempo_total

    @staticmethod
    def sucessores(s: list, velocidade_entrada: float = None, tempo_limite: float = None) -> tuple[list, float]:
        """Gera um vizinho substituindo um trecho aleatório por um caminho BFS alternativo."""
        n = len(s)
        if n <= 3:
            return s, avalia_caminho(s, velocidade_entrada, tempo_limite)

        i = random.randint(1, n - 3)
        j = random.randint(i + 2, n - 1)

        alternativo = _bfs_trecho(s[i], s[j])
        if alternativo is None:
            return s, avalia_caminho(s, velocidade_entrada, tempo_limite)

        novo    = s[:i] + alternativo + s[j+1:]
        vs      = avalia_caminho(novo, velocidade_entrada, tempo_limite)

        return novo, vs

    def encosta(self, s1: list, v1: float, velocidade: float = None, tempo_limite: float = None) -> tuple[list, float, float, float]:
        """Busca em encosta simples: maximiza tempo percorrido, para quando não há melhora."""
        atual = s1
        va    = v1

        while True:
            candidatos = [BuscaLocal.sucessores(atual, velocidade, tempo_limite) for _ in range(5)]
            melhores   = [(s, v) for s, v in candidatos if v > va]

            if not melhores:
                vel = velocidade or VELOCIDADE_INICIAL
                config.LAST_VELOCITY = vel
                return atual, va, vel, BuscaLocal.tempo_caminho(atual, vel, tempo_limite)

            atual, va = random.choice(melhores)

    def encosta_com_tentativa(self, s1: list, v1: float, tmax: int, velocidade: float = None, tempo_limite: float = None) -> tuple[list, float, float, float]:
        """Busca em encosta com tentativas: tolera até tmax iterações sem melhora antes de parar."""
        atual = s1
        va    = v1
        t     = 0

        while True:
            candidatos = [BuscaLocal.sucessores(atual, velocidade, tempo_limite) for _ in range(5)]
            melhores   = [(s, v) for s, v in candidatos if v > va]

            if melhores:
                atual, va = random.choice(melhores)
                t = 0
            elif t < tmax:
                t += 1
            else:
                vel = velocidade or VELOCIDADE_INICIAL
                config.LAST_VELOCITY = vel
                return atual, va, vel, BuscaLocal.tempo_caminho(atual, vel, tempo_limite)

    def tempera(self, s1: list, v1: float, t1: float, tf: float, fr: float, velocidade: float = None, tempo_limite: float = None) -> tuple[list, float, float, float]:
        """Simulated Annealing: aceita pioras com probabilidade exp(-d/temp) para escapar de ótimos locais."""
        atual = s1
        va    = v1
        temp  = t1

        while temp > tf:
            novo, vn = BuscaLocal.sucessores(atual, velocidade, tempo_limite)

            if vn > va:
                atual = novo
                va    = vn
            else:
                d   = va - vn
                ale = random.random()
                if ale < exp(-d / temp):
                    atual = novo
                    va    = vn

            temp *= fr

        vel = velocidade or VELOCIDADE_INICIAL
        config.LAST_VELOCITY = vel
        return atual, va, vel, BuscaLocal.tempo_caminho(atual, vel, tempo_limite)