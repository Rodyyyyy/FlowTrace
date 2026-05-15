"""
mason_formula.py
================
Mason's Gain Formula engine.

Mason's Rule computes the overall transfer function of a Signal Flow Graph:

    T(s) = Σ [ P_k · Δ_k ] / Δ

Where:
    P_k  = gain of the k-th forward path
    Δ    = graph determinant
         = 1 − ΣL_i + Σ(L_i·L_j) − Σ(L_i·L_j·L_k) + ...
           (alternating sum over non-touching loop-gain products)
    Δ_k  = cofactor of Δ for path k
         = Δ computed using only loops NOT touching path k

This module orchestrates the sub-algorithms from graph_algorithms.py
and returns a rich, step-by-step result dict suitable for direct
JSON serialisation to the frontend.
"""

from __future__ import annotations
from typing import List

from .graph_model import SFGGraph
from .graph_algorithms import (
    find_forward_paths,
    find_loops,
    find_non_touching_sets,
    compute_delta,
    compute_cofactor,
)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def apply_mason(graph: SFGGraph) -> dict:
    """
    Run the complete Mason's Gain Formula analysis on an SFGGraph.

    Returns
    -------
    dict with the following keys:

    forward_paths     : list of dicts (path, gain, cofactor expression)
    loops             : list of dicts (path, gain)
    non_touching_sets : list of groups (each group is a list of loop dicts)
    delta             : dict (expression, terms)
    transfer_function : dict (numerator, denominator, expression)
    steps             : list of human-readable step strings
    error             : None | string (if analysis failed)
    """
    result: dict = {
        "forward_paths":     [],
        "loops":             [],
        "non_touching_sets": [],
        "delta":             {},
        "transfer_function": {},
        "steps":             [],
        "error":             None,
    }

    steps: list[str] = []

    try:
        # ── Step 1: Forward paths ───────────────────────────────────────────
        steps.append("Step 1 — Identify all forward paths from source to sink")
        forward_paths = find_forward_paths(graph)
        result["forward_paths"] = forward_paths

        if not forward_paths:
            result["error"] = "No forward path found between source and sink."
            result["steps"] = steps
            return result

        for fp in forward_paths:
            steps.append(
                f"  P{fp['index']} = {' → '.join(fp['path'])}  "
                f"│  gain = {fp['gain']}"
            )

        # ── Step 2: Loops ───────────────────────────────────────────────────
        steps.append("Step 2 — Detect all feedback loops")
        loops = find_loops(graph)
        result["loops"] = loops

        if loops:
            for lp in loops:
                steps.append(
                    f"  L{lp['index']} = {' → '.join(lp['path'])} → {lp['path'][0]}"
                    f"  │  gain = {lp['gain']}"
                )
        else:
            steps.append("  (No loops detected)")

        # ── Step 3: Non-touching sets ───────────────────────────────────────
        steps.append("Step 3 — Find non-touching loop combinations")
        nt_sets = find_non_touching_sets(loops)
        result["non_touching_sets"] = [
            [{"index": l["index"], "path": l["path"], "gain": l["gain"]}
             for l in group]
            for group in nt_sets
        ]

        if nt_sets:
            for group in nt_sets:
                labels = " × ".join(f"L{l['index']}" for l in group)
                steps.append(f"  Non-touching: {labels}")
        else:
            steps.append("  (No non-touching loop pairs)")

        # ── Step 4: Graph determinant Δ ─────────────────────────────────────
        steps.append("Step 4 — Compute graph determinant Δ")
        delta = compute_delta(loops, nt_sets)
        result["delta"] = delta
        steps.append(f"  Δ = {delta['expression']}")

        # ── Step 5: Cofactors Δ_k ──────────────────────────────────────────
        steps.append("Step 5 — Compute cofactor Δ_k for each forward path")
        for fp in forward_paths:
            cofactor = compute_cofactor(fp, loops, nt_sets)
            fp["cofactor"] = cofactor
            steps.append(f"  Δ{fp['index']} = {cofactor['expression']}")

        # ── Step 6: Apply Mason's formula ───────────────────────────────────
        steps.append("Step 6 — Apply Mason's Gain Formula:  T = Σ(Pk·Δk) / Δ")
        num_terms: list[str] = []
        for fp in forward_paths:
            pk    = fp["gain"]
            dk    = fp["cofactor"]["expression"]
            # Simplify P_k · Δ_k when Δ_k = 1
            if dk.strip() == "1":
                term = pk
            else:
                term = f"({pk})·({dk})"
            num_terms.append(term)
            steps.append(f"  P{fp['index']}·Δ{fp['index']} = {term}")

        numerator   = " + ".join(num_terms) if num_terms else "0"
        denominator = delta["expression"]
        expression  = f"T(s) = [{numerator}] / [{denominator}]"

        result["transfer_function"] = {
            "numerator":   numerator,
            "denominator": denominator,
            "expression":  expression,
        }
        steps.append(f"  {expression}")

    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)

    result["steps"] = steps
    return result
