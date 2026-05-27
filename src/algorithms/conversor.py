"""
algorithms/conversor.py
===================
Helper para conversões de grafos em tuplas.
"""


class Conversor(object):
    """Helper class para conversões e cálculos."""
    
    def str_to_tuple(s: str) -> tuple:
        """'(2,3)' → (2, 3)"""
        s = s.strip().strip("()")
        r, c = s.split(",")
        return (int(r), int(c))

    def tuple_to_str(t: tuple) -> str:
        """(2, 3) → '(2,3)'"""
        return f"({t[0]},{t[1]})"
    
    def super_str_to_key(s: str) -> tuple:
        """'M2:(3,4)' → (2, (3, 4))"""
        mid, coords = s.split(":", 1)
        map_id = int(mid[1:])
        r, c = coords.strip("()").split(",")
        return (map_id, (int(r), int(c)))

    def key_to_super_str(key: tuple) -> str:
        """(2, (3, 4)) → 'M2:(3,4)'"""
        map_id, (r, c) = key
        return f"M{map_id}:({r},{c})"