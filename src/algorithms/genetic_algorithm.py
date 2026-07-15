"""
algorithms/genetic_algorithm.py
================================
GA adapted for maximizing travel time on weighted graphs.
Chromosome = list of nodes [(r,c), ...] representing a valid path.
Fitness    = total path time (higher = better), -inf if it exceeds time_limit.
"""

import random
from math import ceil
from algorithms.local_search import LocalSearch
from algorithms.local_search_utils import _initial_path, _bfs_segment, evaluate_path
import config


# ── population ───────────────────────────────────────────────────────────────

def initial_population(tp: int, start: str, goal: str, speed: float, time_limit: float) -> list:
    """
    Generate the initial population: tp variations of the base BFS path via
    successors. Guarantees every individual is a valid start→goal path.
    """
    base = _initial_path(start, goal, time_limit)
    return [base] if base is not None else []


# ── evaluation ────────────────────────────────────────────────────────────────

def compute_fitness(population: list, speed: float, time_limit: float) -> list[float]:
    """
    Compute each individual's fitness and normalize it for roulette-wheel use.
    Invalid individuals (fitness = -inf) get weight 0.
    """
    raw = [evaluate_path(ind, speed, time_limit) for ind in population]

    # replace -inf with 0 so it doesn't break normalization
    positive = [f if f != float('-inf') else 0.0 for f in raw]

    total = sum(positive)
    if total == 0:
        n = len(positive)
        return [1.0 / n] * n  # uniform distribution if all are invalid

    return [f / total for f in positive]


# ── selection ─────────────────────────────────────────────────────────────────

def roulette_wheel_selection(fitness: list[float]) -> int:
    """Select an index via fitness-proportionate roulette-wheel selection."""
    rnd   = random.random()
    total = 0.0
    for i, f in enumerate(fitness):
        total += f
        if total >= rnd:
            return i
    return len(fitness) - 1


def tournament_selection(fitness: list[float]) -> int:
    """Select an index via binary tournament."""
    p1 = random.randrange(len(fitness))
    p2 = random.randrange(len(fitness))
    return p1 if fitness[p1] >= fitness[p2] else p2


# ── crossover ─────────────────────────────────────────────────────────────────

def crossover(parent1: list, parent2: list) -> tuple[list, list]:
    """
    Positional-cut crossover.
    Picks a random cut point; BFS reconnects the two halves.
    If BFS fails, returns copies of the parents.
    """
    n = min(len(parent1), len(parent2))
    if n < 4:
        return list(parent1), list(parent2)

    cut = random.randint(1, n - 2)

    def _reconnect(prefix, suffix):
        bridge = _bfs_segment(prefix[-1], suffix[0])
        if bridge is None:
            return None
        return prefix + bridge[1:] + suffix[1:]   # avoids duplicating the junction nodes

    child1 = _reconnect(parent1[:cut], parent2[cut:])
    child2 = _reconnect(parent2[:cut], parent1[cut:])
    return (child1 if child1 else list(parent1)), (child2 if child2 else list(parent2))


# ── mutation ──────────────────────────────────────────────────────────────────

def mutation(individual: list, speed: float, time_limit: float) -> list:
    """
    Translocation mutation: moves an intermediate node to another position
    and uses BFS to reconnect the affected neighbors.
    If any BFS call fails, returns the individual unchanged.
    """
    n = len(individual)
    if n < 5:
        return list(individual)

    # pick the node to move (i) and its destination (j), both intermediate
    i = random.randint(1, n - 3)
    j = random.randint(1, n - 3)
    if i == j:
        return list(individual)

    moved_node = individual[i]

    # remove node i and reconnect its neighbors
    without_i = list(individual)
    without_i.pop(i)
    gap_bridge = _bfs_segment(without_i[i - 1], without_i[i])   # neighbors of the gap
    if gap_bridge is None:
        return list(individual)

    base_path = without_i[:i - 1] + gap_bridge + without_i[i + 1:]

    # insert moved_node at position j of the new sequence (adjusted)
    adjusted_j     = min(j, len(base_path) - 2)
    bridge_before  = _bfs_segment(base_path[adjusted_j - 1], moved_node)
    bridge_after   = _bfs_segment(moved_node, base_path[adjusted_j])
    if bridge_before is None or bridge_after is None:
        return list(individual)

    return base_path[:adjusted_j - 1] + bridge_before + bridge_after[1:] + base_path[adjusted_j + 1:]


# ── constraint enforcement ─────────────────────────────────────────────────────

def enforce_constraint(population: list, speed: float, time_limit: float) -> list:
    """
    Ensures no individual exceeds time_limit.
    Strategy: truncate at the last node before going over, then reconnect
    to the goal via BFS.
    """
    goal = population[0][-1]  # all individuals share the same goal
    adjusted = []

    for ind in population:
        elapsed_time = 0.0
        sim_speed    = speed
        cut_idx      = 0

        for idx, node in enumerate(ind[1:], start=1):
            if config.MULTIVERSE_MODE:
                map_id, (r, c) = node
                weights     = config.MULTIVERSE.maps[map_id].grid_weights
                terrain_map = config.MULTIVERSE.maps[map_id].terrain_map
            else:
                r, c = node
                weights     = config.GRID_WEIGHTS
                terrain_map = config.TERRAIN_MAP

            weight  = weights[r][c] or 1.0
            terrain = terrain_map[r][c] if terrain_map else None
            factor  = config.FATORES.get(terrain.name, 1.0) if terrain else 1.0

            delay          = max(50, min((weight / sim_speed) * 1000, 2000))
            elapsed_time  += delay / 1000

            if elapsed_time > time_limit:
                cut_idx = idx - 1  # last node still within the limit
                break

            sim_speed = max(config.VELOCIDADE_MIN,
                            min(sim_speed * factor, config.VELOCIDADE_MAX))
        else:
            adjusted.append(ind)  # already valid, no truncation needed
            continue

        # reconnect ind[:cut_idx+1] → goal via BFS
        if cut_idx > 0:
            segment = _bfs_segment(ind[cut_idx], goal)
            if segment:
                adjusted.append(ind[:cut_idx] + segment)
                continue

        # fallback: direct BFS path start→goal
        fallback = _initial_path(ind[0], goal)
        adjusted.append(fallback if fallback else ind)

    return adjusted


# ── sorting ───────────────────────────────────────────────────────────────────

def sort_population(population: list, fitness: list[float]) -> tuple[list, list[float]]:
    """Sort the population by descending fitness (highest fitness first)."""
    pairs = sorted(zip(population, fitness), key=lambda x: x[1], reverse=True)
    sorted_population, sorted_fitness = zip(*pairs)
    return list(sorted_population), list(sorted_fitness)


# ── next generation ─────────────────────────────────────────────────────────────

def next_generation(population: list, offspring: list, tp: int, ig: float) -> list:
    """
    Elitism: keeps the best ceil(ig*tp) individuals from the current
    population, fills the rest with the best offspring.
    """
    elite_count = ceil(ig * tp)
    return population[:elite_count] + offspring[:tp - elite_count]


# ── offspring ─────────────────────────────────────────────────────────────────

def generate_offspring(population: list, fitness: list[float], tp: int,
                       tc: float, tm: float,
                       speed: float, time_limit: float) -> list:
    """
    Generates 2*tp offspring via crossover and mutation.
    Uses roulette-wheel selection to pick the parents.
    """
    offspring = []
    while len(offspring) < 2 * tp:
        parent1 = population[roulette_wheel_selection(fitness)]
        parent2 = population[roulette_wheel_selection(fitness)]

        if random.random() <= tc:
            child1, child2 = crossover(parent1, parent2)
        else:
            child1, child2 = list(parent1), list(parent2)

        if random.random() <= tm:
            child1 = mutation(child1, speed, time_limit)
        if random.random() <= tm:
            child2 = mutation(child2, speed, time_limit)

        offspring.extend([child1, child2])

    return offspring[:2 * tp]


# ── main algorithm ────────────────────────────────────────────────────────────

def GA(start: str, goal: str,
       speed: float, time_limit: float,
       tp: int = 10, ng: int = 20,
       tc: float = 0.8, tm: float = 0.1, ig: float = 0.2):
    """
    Genetic Algorithm for maximizing travel time (≤ time_limit).

    Parameters
    ----------
    start, goal   : start and goal nodes (string)
    speed         : the agent's initial speed
    time_limit  : maximum capacity — equivalent to the knapsack's C_MAX
    tp            : population size
    ng            : number of generations
    tc            : crossover rate
    tm            : mutation rate
    ig            : fraction of elite individuals preserved per generation

    Returns
    -------
    (initial_path, final_path, initial_fitness, final_fitness)
    """
    population = initial_population(tp, start, goal, speed, time_limit)
    if not population:
        return None, None, 0.0, 0.0

    fitness = compute_fitness(population, speed, time_limit)
    population, fitness = sort_population(population, fitness)
    initial_path, initial_value = population[0], evaluate_path(population[0], speed, time_limit)

    for _ in range(ng):
        offspring = generate_offspring(population, fitness, tp, tc, tm, speed, time_limit)
        offspring = enforce_constraint(offspring, speed, time_limit)

        offspring_fitness           = compute_fitness(offspring, speed, time_limit)
        offspring, offspring_fitness = sort_population(offspring, offspring_fitness)

        population = next_generation(population, offspring, tp, ig)
        fitness    = compute_fitness(population, speed, time_limit)
        population, fitness = sort_population(population, fitness)

    final_path  = population[0]
    final_value = evaluate_path(final_path, speed, time_limit)
    return initial_path, final_path, initial_value, final_value