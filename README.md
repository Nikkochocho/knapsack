# Knapsack

<div align = "center">

<img src = "/resources/logo.png" alt = "knapsack logo" title = "racoon fringe">

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
- **Comparative analysis window**: run all algorithms on the same problem and compare cost, depth, and profit side by side in a table and bar chart.
- **Configurable algorithm parameters** (e.g., simulated annealing schedule, genetic algorithm population/generations/crossover/mutation rates, time limit).
- Custom pixel-art tileset and sprite assets for the grid and characters.

## Tech Stack :space_invader:

- **Python 3.11**
- **Tkinter** — GUI framework
- **Pillow (PIL)** — image handling for sprites/tilesets

No other third-party dependencies are required; the rest of the codebase relies on the Python standard library (`dataclasses`, `collections`, `math`, `random`, `pathlib`, `webbrowser`, etc).

## Getting Started :rocket:

### Prerequisites

- Python 3.11+
- [Pillow](https://pypi.org/project/Pillow/)

### Installation

```bash
git clone https://github.com/Nikkochocho/knapsack.git
cd knapsack
pip install Pillow
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
4. Adjust algorithm-specific parameters (time limit, annealing schedule, GA population settings, etc.).
5. Click **Search** to run the algorithm and watch the animated path.
6. Use **Regenerate** to create a new grid, or enable **Multiverse mode** to search across multiple connected maps.
7. Open the **Comparative Analysis** window to run all algorithms on the same setup and compare results in a table/chart.