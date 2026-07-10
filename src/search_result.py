"""
search_result.py
================
Defines the standard return type used by all search algorithms.
"""

from dataclasses import dataclass, field


@dataclass
class SearchResult:
    path:         list[str] = field(default_factory=list)
    cost:         float     = 0.0
    depth:        int       = 0
    profit:       float     = 0.0

    @property
    def found(self) -> bool:
        return len(self.path) > 0

    def to_dict(self) -> dict:
        return {
            'path':         self.path,
            'cost':         self.cost,
            'depth':        self.depth,
            'profit':       self.profit,
        }