"""
layout.py
=========
Graph layout algorithms for the Signal Flow Graph visualizer.

Provides a spring-layout that wraps NetworkX's spring_layout and maps
the resulting (−1..1) coordinates into pixel space suitable for the
frontend canvas (default 900 × 500 px).
"""

from __future__ import annotations
import math
import networkx as nx
from .graph_model import SFGGraph


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def spring_layout(
    graph: SFGGraph,
    width: int = 900,
    height: int = 500,
    padding: int = 80,
    seed: int = 42,
) -> None:
    """
    Compute 2-D spring-layout positions and write them back into each Node.

    Uses NetworkX Fruchterman-Reingold if the graph has more than 1 node,
    otherwise places the single node at the centre.

    Parameters
    ----------
    graph   : SFGGraph to lay out (mutates node.x / node.y in-place)
    width   : canvas width in pixels
    height  : canvas height in pixels
    padding : minimum distance from canvas edges
    seed    : random seed for reproducibility
    """
    G = graph.nx_graph
    n = G.number_of_nodes()

    if n == 0:
        return

    if n == 1:
        nid = list(G.nodes)[0]
        node = graph.get_node(nid)
        if node:
            node.x, node.y = width / 2, height / 2
        return

    # ── Fruchterman-Reingold layout ─────────────────────────────────────────
    # Pin source left-centre, sink right-centre to encourage left→right flow
    fixed_pos = {}
    pin_nodes = []
    if graph.source and graph.source in G:
        fixed_pos[graph.source] = (-0.85, 0.0)
        pin_nodes.append(graph.source)
    if graph.sink and graph.sink in G:
        fixed_pos[graph.sink] = (0.85, 0.0)
        pin_nodes.append(graph.sink)

    pos = nx.spring_layout(
        G,
        k=2.0 / math.sqrt(max(n, 1)),
        iterations=80,
        seed=seed,
        pos=fixed_pos if fixed_pos else None,
        fixed=pin_nodes if pin_nodes else None,
    )

    # ── Map (−1..1) → pixel space ───────────────────────────────────────────
    usable_w = width  - 2 * padding
    usable_h = height - 2 * padding

    xs = [v[0] for v in pos.values()]
    ys = [v[1] for v in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)

    for nid, (nx_, ny_) in pos.items():
        node = graph.get_node(nid)
        if node is None:
            continue
        node.x = padding + (nx_ - min_x) / span_x * usable_w
        node.y = padding + (ny_ - min_y) / span_y * usable_h


def hierarchical_layout(
    graph: SFGGraph,
    width: int = 900,
    height: int = 500,
    padding: int = 80,
) -> None:
    """
    Alternative BFS-layer layout that places the source on the left and
    assigns nodes to columns by their BFS depth.

    Used as a fallback when the spring layout produces poor results for
    strictly left-to-right pipelines.
    """
    G = graph.nx_graph
    if G.number_of_nodes() == 0:
        return

    start = graph.source or list(G.nodes)[0]

    # BFS to assign layers
    layers: dict[str, int] = {}
    q = [start]
    layers[start] = 0
    while q:
        cur = q.pop(0)
        for nb in G.successors(cur):
            if nb not in layers:
                layers[nb] = layers[cur] + 1
                q.append(nb)
    # Nodes not reachable from source get layer 0
    for nid in G.nodes:
        layers.setdefault(nid, 0)

    max_layer = max(layers.values(), default=0)
    by_layer: dict[int, list] = {}
    for nid, lyr in layers.items():
        by_layer.setdefault(lyr, []).append(nid)

    usable_w = width  - 2 * padding
    usable_h = height - 2 * padding
    x_step = usable_w / max(max_layer, 1)

    for lyr, nodes_in_layer in by_layer.items():
        y_step = usable_h / max(len(nodes_in_layer), 1)
        for i, nid in enumerate(nodes_in_layer):
            node = graph.get_node(nid)
            if node:
                node.x = padding + lyr * x_step
                node.y = padding + i * y_step + y_step / 2
