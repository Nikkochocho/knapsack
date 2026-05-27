"""
algorithms/AlgoritmoGenetico.py
================================
AG adaptado para maximização de tempo percorrido em grafos ponderados.
Cromossomo = lista de nós [(r,c), ...] representando um caminho válido.
Fitness    = tempo total do caminho (maior = melhor), -inf se ultrapassar tempo_limite.
"""

import random
from math import ceil
from algorithms.BuscaLocal import BuscaLocal
from algorithms.busca_local_utils import _caminho_inicial, _bfs_trecho, avalia_caminho
import config


# ── população ────────────────────────────────────────────────────────────────

def pop_ini(tp: int, start: str, goal: str, velocidade: float, tempo_limite: float) -> list:
    """
    Gera população inicial: tp variações do caminho BFS base via sucessores.
    Garante que todos os indivíduos são caminhos válidos start→goal.
    """
    base = _caminho_inicial(start, goal, tempo_limite)
    return [base] if base is not None else []


# ── avaliação ─────────────────────────────────────────────────────────────────

def aptidao(pop: list, velocidade: float, tempo_limite: float) -> list[float]:
    """
    Calcula fitness de cada indivíduo e normaliza para uso na roleta.
    Indivíduos inválidos (fitness=-inf) recebem peso 0.
    """
    raw = [avalia_caminho(ind, velocidade, tempo_limite) for ind in pop]

    # substitui -inf por 0 para não quebrar a normalização
    positivos = [f if f != float('-inf') else 0.0 for f in raw]

    soma = sum(positivos)
    if soma == 0:
        n = len(positivos)
        return [1.0 / n] * n  # distribuição uniforme se todos inválidos

    return [f / soma for f in positivos]


# ── seleção ───────────────────────────────────────────────────────────────────

def roleta(fit: list[float]) -> int:
    """Seleciona índice por roleta viciada proporcional ao fitness."""
    ale  = random.random()
    soma = 0.0
    for i, f in enumerate(fit):
        soma += f
        if soma >= ale:
            return i
    return len(fit) - 1


def torneio(fit: list[float]) -> int:
    """Seleciona índice por torneio binário."""
    p1 = random.randrange(len(fit))
    p2 = random.randrange(len(fit))
    return p1 if fit[p1] >= fit[p2] else p2


# ── cruzamento ────────────────────────────────────────────────────────────────

def cruzamento(pai1: list, pai2: list) -> tuple[list, list]:
    """
    Cruzamento por corte posicional.
    Sorteia um índice de corte, BFS reconecta as metades.
    Se BFS falhar, retorna cópias dos pais.
    """
    n    = min(len(pai1), len(pai2))
    if n < 4:
        return list(pai1), list(pai2)

    corte = random.randint(1, n - 2)

    def _reconecta(prefixo, sufixo):
        ponte = _bfs_trecho(prefixo[-1], sufixo[0])
        if ponte is None:
            return None
        return prefixo + ponte[1:] + sufixo[1:]   # evita duplicar nós da junção

    f1 = _reconecta(pai1[:corte], pai2[corte:])
    f2 = _reconecta(pai2[:corte], pai1[corte:])
    return (f1 if f1 else list(pai1)), (f2 if f2 else list(pai2))


# ── mutação ───────────────────────────────────────────────────────────────────

def mutacao(individuo: list, velocidade: float, tempo_limite: float) -> list:
    """
    Mutação por translocação: move um nó intermediário para outra posição
    e usa BFS para reconectar os vizinhos afetados.
    Se qualquer BFS falhar, retorna o indivíduo sem alteração.
    """
    n = len(individuo)
    if n < 5:
        return list(individuo)

    # sorteia o nó a mover (i) e o destino (j), ambos intermediários
    i = random.randint(1, n - 3)
    j = random.randint(1, n - 3)
    if i == j:
        return list(individuo)

    no_movido = individuo[i]

    # remove o nó i e reconecta seus vizinhos
    sem_i = list(individuo)
    sem_i.pop(i)
    ponte_gap = _bfs_trecho(sem_i[i - 1], sem_i[i])   # vizinhos do buraco
    if ponte_gap is None:
        return list(individuo)

    base = sem_i[:i - 1] + ponte_gap + sem_i[i + 1:]

    # insere no_movido na posição j da nova sequência (ajustada)
    j_adj = min(j, len(base) - 2)
    ponte_antes = _bfs_trecho(base[j_adj - 1], no_movido)
    ponte_depois = _bfs_trecho(no_movido, base[j_adj])
    if ponte_antes is None or ponte_depois is None:
        return list(individuo)

    return base[:j_adj - 1] + ponte_antes + ponte_depois[1:] + base[j_adj + 1:]


# ── restrição ─────────────────────────────────────────────────────────────────

def ajusta_restricao(pop: list, velocidade: float, tempo_limite: float) -> list:
    """
    Garante que nenhum indivíduo ultrapassa tempo_limite.
    Estratégia: trunca no último nó antes de estourar e reconecta ao goal via BFS.
    """
    goal = pop[0][-1]  # todos os indivíduos compartilham o mesmo goal
    ajustados = []

    for ind in pop:
        tempo   = 0.0
        vel_sim = velocidade
        corte   = 0

        for idx, no in enumerate(ind[1:], start=1):
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

            delay   = max(50, min((peso / vel_sim) * 1000, 2000))
            tempo  += delay / 1000

            if tempo > tempo_limite:
                corte = idx - 1  # último nó ainda dentro do limite
                break

            vel_sim = max(config.VELOCIDADE_MIN,
                          min(vel_sim * fator, config.VELOCIDADE_MAX))
        else:
            ajustados.append(ind)  # já válido, sem corte necessário
            continue

        # reconecta ind[:corte+1] → goal via BFS
        if corte > 0:
            trecho = _bfs_trecho(ind[corte], goal)
            if trecho:
                ajustados.append(ind[:corte] + trecho)
                continue

        # fallback: caminho BFS direto start→goal
        fallback = _caminho_inicial(ind[0], goal)
        ajustados.append(fallback if fallback else ind)

    return ajustados


# ── ordenação ─────────────────────────────────────────────────────────────────

def ordena(pop: list, fit: list[float]) -> tuple[list, list[float]]:
    """Ordena população por fitness decrescente (maior fitness primeiro)."""
    pares = sorted(zip(pop, fit), key=lambda x: x[1], reverse=True)
    pop_ord, fit_ord = zip(*pares)
    return list(pop_ord), list(fit_ord)


# ── nova população ────────────────────────────────────────────────────────────

def nova_pop(pop: list, desc: list, tp: int, ig: float) -> list:
    """
    Elitismo: mantém os melhores ceil(ig*tp) da população atual,
    completa com os melhores descendentes.
    """
    elite = ceil(ig * tp)
    return pop[:elite] + desc[:tp - elite]


# ── descendentes ─────────────────────────────────────────────────────────────

def descendentes(pop: list, fit: list[float], tp: int,
                 tc: float, tm: float,
                 velocidade: float, tempo_limite: float) -> list:
    """
    Gera 2*tp descendentes via cruzamento e mutação.
    Usa roleta para seleção dos pais.
    """
    desc = []
    while len(desc) < 2 * tp:
        pai1 = pop[roleta(fit)]
        pai2 = pop[roleta(fit)]

        if random.random() <= tc:
            f1, f2 = cruzamento(pai1, pai2)
        else:
            f1, f2 = list(pai1), list(pai2)

        if random.random() <= tm:
            f1 = mutacao(f1, velocidade, tempo_limite)
        if random.random() <= tm:
            f2 = mutacao(f2, velocidade, tempo_limite)

        desc.extend([f1, f2])

    return desc[:2 * tp]


# ── algoritmo principal ───────────────────────────────────────────────────────

def AG(start: str, goal: str,
       velocidade: float, tempo_limite: float,
       tp: int = 10, ng: int = 20,
       tc: float = 0.8, tm: float = 0.1, ig: float = 0.2):
    """
    Algoritmo Genético para maximização de tempo percorrido (≤ tempo_limite).

    Parâmetros
    ----------
    start, goal     : nós de início e fim (string)
    velocidade      : velocidade inicial do personagem
    tempo_limite    : capacidade máxima — equivalente ao C_MAX da mochila
    tp              : tamanho da população
    ng              : número de gerações
    tc              : taxa de cruzamento
    tm              : taxa de mutação
    ig              : fração de elite preservada por geração

    Retorno
    -------
    (caminho_inicial, caminho_final, fitness_inicial, fitness_final)
    """
    pop = pop_ini(tp, start, goal, velocidade, tempo_limite)
    if not pop:
        return None, None, 0.0, 0.0

    fit = aptidao(pop, velocidade, tempo_limite)
    pop, fit = ordena(pop, fit)
    si, vi = pop[0], avalia_caminho(pop[0], velocidade, tempo_limite)

    for _ in range(ng):
        desc = descendentes(pop, fit, tp, tc, tm, velocidade, tempo_limite)
        desc = ajusta_restricao(desc, velocidade, tempo_limite)

        fit_d       = aptidao(desc, velocidade, tempo_limite)
        desc, fit_d = ordena(desc, fit_d)

        pop  = nova_pop(pop, desc, tp, ig)
        fit  = aptidao(pop, velocidade, tempo_limite)
        pop, fit = ordena(pop, fit)

    sf = pop[0]
    vf = avalia_caminho(sf, velocidade, tempo_limite)
    return si, sf, vi, vf