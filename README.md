# Knapsack

<div align = "center">

<img src = "/resources/logo.png" alt = "knapsack logo" title = "racoon">

An interactive desktop application, built with Python and Tkinter, that visualizes and compares **local search** and **genetic algorithms** applied to a pathfinding problem framed as a knapsack-style optimization: traveling across a procedurally generated grid while maximizing gain (velocity/profit) within a limited time budget.

The grid is generated procedurally each run, with different terrain types affecting movement speed, and the chosen algorithm animates its search for a path from a start node to a goal node.

</div>

---

## 📋 Table of Contents

* [Overview](#overview-bulb)
* [Features](#features-pushpin)
* [Tech Stack](#tech-stack-space_invader)
* [Getting Started](#getting-started-rocket)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
* [Usage](#usage-turtle)
* [Algorithm Parameters](#algorithm-parameters-gear)
  - [Hill Climbing](#hill-climbing)
  - [Hill Climbing with Random Restarts](#hill-climbing-with-random-restarts)
  - [Simulated Annealing](#simulated-annealing)
  - [Genetic Algorithm](#genetic-algorithm)
  - [Shared parameter: Time Limit](#shared-parameter-time-limit)
* [Comparative Analysis & PDF Reports](#comparative-analysis--pdf-reports-bar_chart)

## Overview :bulb:

Although named after the classic knapsack problem, this project reframes it as a **path optimization under a time constraint**: the "capacity" is a time limit, and the "value" collected is the velocity/profit gained by traversing terrain efficiently. Algorithms search for the path that best balances distance and terrain cost against that time budget.

## Features :pushpin:

- **Procedurally generated maze/grid** with configurable size and terrain (plains, forest, swamp, mountain), each with a different movement-speed factor.
- **Four search algorithms**, selectable at runtime:
  - Hill Climbing
  - Hill Climbing with Random Restarts
  - Simulated Annealing
  - Genetic Algorithm
- **Real-time animated visualization** of the path being explored on the grid.
- **Manual start/goal node picking** directly on the canvas.
- **Multiverse mode**: generates multiple connected maps linked by bidirectional portals, forming a larger super-graph to search across.
- **Comparative analysis window**: run all algorithms — with multiple parameter configurations and multiple runs each — on the same problem, and compare cost, depth, and profit side by side in a table and bar chart.
- **PDF report export**: turn a comparative analysis run into a formatted, multi-section PDF report with an automatically generated conclusion.
- **Configurable algorithm parameters** (e.g., simulated annealing schedule, genetic algorithm population/generations/crossover/mutation rates, time limit).
- **Multi-language interface** (English, Português, Español), switchable at runtime from the settings menu — including the exported PDF report.
- Custom pixel-art tileset and sprite assets for the grid and characters.

## Tech Stack :space_invader:

- **Python 3.11**
- **Tkinter** — GUI framework
- **Pillow (PIL)** — image handling for sprites/tilesets
- **ReportLab** — PDF generation for the comparative analysis report

No other third-party dependencies are required; the rest of the codebase relies on the Python standard library (`dataclasses`, `collections`, `math`, `random`, `pathlib`, `webbrowser`, etc).

## Getting Started :rocket:

### Prerequisites

- Python 3.11+
- [Pillow](https://pypi.org/project/Pillow/)
- [ReportLab](https://pypi.org/project/reportlab/) (only needed to export PDF reports from the Comparative Analysis window)

### Installation

```bash
git clone https://github.com/Nikkochocho/knapsack.git
cd knapsack
pip install Pillow reportlab
```

### Running the application

```bash
cd src
python main.py
```

## Usage :turtle:

1. Launch the app; a grid is generated automatically.
2. Pick a **search method** from the control panel.
3. Optionally set custom **start/goal nodes** by clicking "pick" and then a cell on the grid.
4. Adjust algorithm-specific parameters (time limit, annealing schedule, GA population settings, etc.) — see [Algorithm Parameters](#algorithm-parameters-gear) below for what each one does.
5. Click **Search** to run the algorithm and watch the animated path.
6. Use **Regenerate** to create a new grid, or enable **Multiverse mode** to search across multiple connected maps.
7. Open the **Comparative Analysis** window to run all algorithms on the same setup, compare results in a table/chart, and optionally export a PDF report — see [Comparative Analysis & PDF Reports](#comparative-analysis--pdf-reports-bar_chart) below.
8. Use the **settings (⚙)** button to switch the interface language (English / Português / Español) at any time.

## Algorithm Parameters :gear:

Every algorithm searches for a path from the start node to the goal node, trying to maximize the total distance/profit covered without exceeding the **time limit**. The parameters below control *how* each algorithm explores the space of possible paths.

### Hill Climbing

A greedy local search: at each step it evaluates several neighboring paths (generated by swapping a random segment of the current path for an alternative route) and moves to the best one found, as long as it's an improvement. It stops as soon as none of the neighbors it samples are better than the current path.

- No additional parameters — it always runs until it can no longer improve.
- **Trade-off:** fast and simple, but easily gets stuck in local optima — it will stop at the first "good enough" path it can't immediately improve on.

### Hill Climbing with Random Restarts

The same neighbor-based climb as above, but more patient: instead of stopping the moment it fails to improve, it keeps trying for a while longer before giving up.

- **`tmax` (Attempts)** — the number of consecutive non-improving iterations it will tolerate before finally stopping. Higher values let it climb out of small plateaus and shallow local optima at the cost of more computation; lower values make it behave closer to plain Hill Climbing.

### Simulated Annealing

Inspired by the metallurgical process of annealing. It behaves like Hill Climbing early on, but will also *sometimes* accept a worse path — with a probability that shrinks as the "temperature" cools down. This lets it escape local optima that plain Hill Climbing would get stuck in.

- **`t1` (Initial temperature)** — how "hot" the search starts. Higher values mean the algorithm is more willing to accept worse moves early on (more exploration).
- **`tf` (Final temperature)** — the temperature at which the search stops. Once the temperature cools below this value, the algorithm halts.
- **`fr` (Cooling factor)** — how quickly the temperature decays after each step (a multiplier applied every iteration, e.g. `0.95`). Values closer to `1.0` cool more slowly (longer, more thorough search); values further from `1.0` cool faster (quicker, greedier search).

### Genetic Algorithm

Evolves a *population* of candidate paths over several generations using selection, crossover, and mutation, keeping the fittest individuals (by total travel time/profit) between generations.

- **`tp` (Population)** — how many candidate paths exist in each generation. Larger populations explore more of the search space per generation, at a higher computational cost.
- **`ng` (Generations)** — how many rounds of selection/crossover/mutation are run before returning the best path found.
- **`tc` (Crossover rate)** — the probability that two selected parent paths are combined (rather than copied as-is) to produce offspring. Higher values increase genetic mixing between paths.
- **`tm` (Mutation rate)** — the probability that a given offspring path is randomly altered (a segment rerouted) after crossover. Higher values increase exploration/diversity but can disrupt good solutions.
- **`ig` (Elitism)** — the fraction of the current generation's best individuals that are carried over unchanged into the next generation, guaranteeing the population never gets worse over time.

### Shared parameter: Time Limit

All four algorithms respect a **time limit** — the "capacity" of the knapsack framing. It represents the maximum travel time (in seconds) a path is allowed to take; any candidate path that would exceed it is treated as invalid (or is truncated to the last valid node) rather than as a valid solution. Profit/gain is reported as the percentage of that time budget actually put to good use compared to the naive baseline path.

## Comparative Analysis & PDF Reports :bar_chart:

The **Comparative Analysis** window (opened from the control panel) lets you benchmark all four algorithms against each other on the *same* grid, start/goal pair, and time limit — rather than running them one at a time.

**Setting it up:**
- Each algorithm gets its own configuration block with the parameters described above.
- Methods with tunable parameters (Hill Climbing with Random Restarts, Simulated Annealing, Genetic Algorithm) can have **multiple configuration blocks** added via "+ add configuration" — for example, to compare Simulated Annealing with a fast cooling schedule against a slow one in the same run.
- Any block can be individually enabled/disabled with its checkbox, letting you exclude configurations from a run without deleting them.
- **Runs per method** lets you repeat each configuration multiple times and average the results — useful since these are stochastic algorithms and a single run can be lucky or unlucky.

**Results:**
- A **comparison table** lists every executed configuration with its average cost (time), average gain (%), and average path length (nodes).
- A **bar chart** visualizes the percentage gain achieved by each configuration, making it easy to spot the best performer at a glance.

**Exporting a PDF report:**
Clicking **Export PDF** from the results window generates a formatted, multi-page report (via ReportLab) containing:
1. A cover page (title, team members, institution/year).
2. An introduction section explaining the problem framing.
3. A methodology section describing all four algorithms and their parameters.
4. A results section with the comparison table, bar chart, and an **automatically generated conclusion** identifying the best-performing configuration and its results.

The report is generated in whichever language is currently active in the app (English, Português, or Español) — including the table headers, section text, and conclusion — so switching the interface language before exporting also changes the report's language.