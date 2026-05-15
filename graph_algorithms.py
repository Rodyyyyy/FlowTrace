"""
graph_algorithms.py
===================
Core graph-theory algorithms for Signal Flow Graph analysis.

Implements:
  1. Forward-path enumeration   — DFS from source to sink
  2. Loop (cycle) detection     — simple cycle enumeration via DFS+backtracking
  3. Non-touching loop sets     — finds all subsets of loops that share no node
  4. Path-gain calculation      — symbolic product of edge gains along a path

All algorithms work on the SFGGraph's adjacency dict so they remain
independent of NetworkX internals and are easy to unit-test.
"""

from __future__ import annotations
from itertools import combinations
from typing import List, Tuple

from .graph_model import SFGGraph


# ─────────────────────────────────────────────────────────────────────────────
# Type aliases
# ─────────────────────────────────────────────────────────────────────────────
Path      = List[str]           # ordered list of node ids
PathGain  = str                 # symbolic gain product string
LoopInfo  = Tuple[Path, PathGain]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Forward-path detection
# ─────────────────────────────────────────────────────────────────────────────

def find_forward_paths(graph: SFGGraph) -> List[dict]:
    """
    Find all simple (node-revisit-free) paths from source to sink using DFS.

    Returns
    -------
    list of dicts, each with keys:
        path  : list of node ids
        gain  : symbolic string (product of edge gains, e.g. "G1·G2·G3")
        index : 1-based path index
    """
    if not graph.source or not graph.sink:
        raise ValueError("Graph must have source and sink set")

    adj = graph.adjacency()
    results: list[dict] = []
    path_index = [0]   # mutable counter for closure

    def dfs(current: str, path: list, gain_parts: list) -> None:
        if current == graph.sink:
            path_index[0] += 1
            results.append({
                "index": path_index[0],
                "path":  list(path),
                "gain":  _join_gains(gain_parts),
                "gain_parts": list(gain_parts),
            })
            return
        for (neighbor, gain) in adj.get(current, []):
            if neighbor not in path:             # simple path – no revisit
                path.append(neighbor)
                gain_parts.append(gain)
                dfs(neighbor, path, gain_parts)
                path.pop()
                gain_parts.pop()

    dfs(graph.source, [graph.source], [])
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 2. Loop (cycle) detection
# ─────────────────────────────────────────────────────────────────────────────

def find_loops(graph: SFGGraph) -> List[dict]:
    """
    Enumerate all simple cycles in the graph using DFS + backtracking.

    Each cycle is stored with the canonical (lexicographically smallest
    starting node) form so duplicates are filtered.

    Returns
    -------
    list of dicts, each with keys:
        index     : 1-based loop index
        path      : list of node ids forming the loop (start node appears once)
        gain      : symbolic gain product
        gain_parts: individual gain strings
    """
    adj   = graph.adjacency()
    nodes = list(graph.nx_graph.nodes)
    seen_signatures: set[str] = set()
    loops: list[dict] = []

    def dfs(start: str, current: str, path: list, gain_parts: list) -> None:
        for (neighbor, gain) in adj.get(current, []):
            if neighbor == start and len(path) > 1:
                # Found a cycle back to start
                signature = _cycle_signature(path)
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    loops.append({
                        "path":       list(path),
                        "gain":       _join_gains(gain_parts + [gain]),
                        "gain_parts": gain_parts + [gain],
                    })
            elif neighbor not in path:
                path.append(neighbor)
                gain_parts.append(gain)
                dfs(start, neighbor, path, gain_parts)
                path.pop()
                gain_parts.pop()

    for start in nodes:
        dfs(start, start, [start], [])

    # Sort by path length then by path string for deterministic output
    loops.sort(key=lambda l: (len(l["path"]), l["path"]))
    for i, lp in enumerate(loops, 1):
        lp["index"] = i

    return loops


# ─────────────────────────────────────────────────────────────────────────────
# 3. Non-touching loop sets
# ─────────────────────────────────────────────────────────────────────────────

def find_non_touching_sets(loops: List[dict]) -> List[List[dict]]:
    """
    Find all subsets of loops that share no common node (non-touching).

    Uses a greedy set-expansion approach rather than brute-force power set
    to keep complexity manageable for typical SFG sizes (< 20 loops).

    Returns
    -------
    List of groups (each group is a list of loop dicts).
    Groups are ordered by size (pairs first, then triples, etc.)
    """
    n = len(loops)
    node_sets = [set(lp["path"]) for lp in loops]

    result: list[list[dict]] = []

    # Try all combinations of size 2, 3, ... up to min(n, 6)
    for size in range(2, min(n + 1, 7)):
        for combo in combinations(range(n), size):
            nodes_union: set[str] = set()
            touching = False
            for idx in combo:
                if nodes_union & node_sets[idx]:  # intersection non-empty
                    touching = True
                    break
                nodes_union |= node_sets[idx]
            if not touching:
                result.append([loops[i] for i in combo])

    return result


# ─────────────────────────────────────────────────────────────────────────────
# 4. Delta and cofactor computation (symbolic)
# ─────────────────────────────────────────────────────────────────────────────

def compute_delta(
    loops: List[dict],
    nt_sets: List[List[dict]],
) -> dict:
    """
    Compute the graph determinant Δ symbolically.

        Δ = 1 − ΣL_i + ΣL_i·L_j − ΣL_i·L_j·L_k + ...

    where L_i are loop gains and the higher-order sums are over
    non-touching loop combinations.

    Returns
    -------
    dict with keys:
        expression : full symbolic string
        terms      : list of individual term strings (for step-by-step display)
    """
    terms = ["1"]
    step_info = [{"level": 0, "term": "1", "description": "Starting value"}]

    # − ΣL_i  (order 1: individual loops)
    for lp in loops:
        term = f"({lp['gain']})"
        terms.append(f"-{term}")
        step_info.append({
            "level": 1,
            "term": f"-{term}",
            "description": f"Loop L{lp['index']}: {_path_str(lp['path'])}",
        })

    # Higher-order non-touching combinations
    by_size: dict[int, list] = {}
    for s in nt_sets:
        by_size.setdefault(len(s), []).append(s)

    for size in sorted(by_size.keys()):
        sign = "+" if size % 2 == 0 else "-"
        for group in by_size[size]:
            product = "·".join(f"({l['gain']})" for l in group)
            path_desc = "  ×  ".join(_path_str(l["path"]) for l in group)
            terms.append(f"{sign}{product}")
            step_info.append({
                "level": size,
                "term": f"{sign}{product}",
                "description": f"Order-{size} non-touching: {path_desc}",
            })

    return {
        "expression": " ".join(terms),
        "terms": step_info,
    }


def compute_cofactor(
    forward_path: dict,
    loops: List[dict],
    nt_sets: List[List[dict]],
) -> dict:
    """
    Compute Δ_k — the cofactor for a given forward path.

    Δ_k is the graph determinant computed using only loops that do NOT
    touch the forward path (share no node with it).

    Returns
    -------
    Same structure as compute_delta() but for the reduced graph.
    """
    path_nodes = set(forward_path["path"])

    # Filter loops that don't touch the forward path
    remote_loops = [lp for lp in loops
                    if not (set(lp["path"]) & path_nodes)]

    # Filter non-touching sets to those made entirely of remote loops
    remote_loop_indices = {lp["index"] for lp in remote_loops}
    remote_nt = [s for s in nt_sets
                 if all(l["index"] in remote_loop_indices for l in s)]

    return compute_delta(remote_loops, remote_nt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _join_gains(parts: list[str]) -> str:
    """Produce a symbolic product string from a list of gain factors."""
    if not parts:
        return "1"
    clean = [p for p in parts if p not in ("1", "+1")]
    if not clean:
        return "1"
    return "·".join(clean)


def _cycle_signature(path: list[str]) -> str:
    """
    Return a canonical string for a cycle so rotations of the same cycle
    map to the same signature (prevents duplicates).
    """
    n = len(path)
    rotations = [tuple(path[i:] + path[:i]) for i in range(n)]
    return str(min(rotations))


def _path_str(path: list[str]) -> str:
    return " → ".join(path)
