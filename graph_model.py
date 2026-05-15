"""
graph_model.py
==============
Core data model for Signal Flow Graphs.

A Signal Flow Graph (SFG) is a directed weighted graph where:
  - Nodes represent system variables (signals)
  - Directed edges represent gains (transfer functions between nodes)

This module defines the SFGGraph class, which wraps NetworkX DiGraph
and adds domain-specific helpers for SFG analysis.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import networkx as nx


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Node:
    """Represents a signal node in the SFG."""
    id: str                          # Unique identifier (e.g. "x1", "R", "Y")
    label: str                       # Display label
    node_type: str = "signal"        # "source" | "sink" | "signal"
    x: float = 0.0                   # Layout x-coordinate (set by layouter)
    y: float = 0.0                   # Layout y-coordinate


@dataclass
class Edge:
    """Represents a directed branch (gain) between two nodes."""
    from_node: str                   # Source node id
    to_node: str                     # Target node id
    gain: str                        # Symbolic gain string (e.g. "G1", "-H", "1")
    edge_type: str = "forward"       # "forward" | "feedback" | "self"


@dataclass
class SFGGraph:
    """
    Signal Flow Graph built on top of NetworkX DiGraph.

    Attributes
    ----------
    nodes   : list of Node objects
    edges   : list of Edge objects
    source  : id of the input node
    sink    : id of the output node
    nx_graph: underlying NetworkX DiGraph (built lazily)
    """
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    source: Optional[str] = None
    sink: Optional[str] = None
    _nx: Optional[nx.DiGraph] = field(default=None, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Build / rebuild the NetworkX representation
    # ------------------------------------------------------------------
    def build_nx(self) -> nx.DiGraph:
        """Create (or rebuild) the NetworkX DiGraph from nodes and edges."""
        G = nx.DiGraph()
        for n in self.nodes:
            G.add_node(n.id, label=n.label, node_type=n.node_type)
        for e in self.edges:
            # Multiple parallel edges between the same pair are stored as a
            # list in the 'gains' attribute so the graph stays a DiGraph.
            if G.has_edge(e.from_node, e.to_node):
                G[e.from_node][e.to_node]["gains"].append(e.gain)
            else:
                G.add_edge(e.from_node, e.to_node,
                           gain=e.gain,
                           gains=[e.gain],
                           edge_type=e.edge_type)
        self._nx = G
        return G

    @property
    def nx_graph(self) -> nx.DiGraph:
        if self._nx is None:
            self.build_nx()
        return self._nx

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def node_ids(self) -> List[str]:
        return [n.id for n in self.nodes]

    def get_node(self, nid: str) -> Optional[Node]:
        return next((n for n in self.nodes if n.id == nid), None)

    def adjacency(self) -> dict:
        """Return {from_node: [(to_node, gain), ...]} adjacency dict."""
        adj: dict = {n.id: [] for n in self.nodes}
        for e in self.edges:
            adj.setdefault(e.from_node, []).append((e.to_node, e.gain))
        return adj

    def to_dict(self) -> dict:
        """Serialise to plain Python dicts (JSON-friendly)."""
        return {
            "source": self.source,
            "sink": self.sink,
            "nodes": [
                {"id": n.id, "label": n.label, "type": n.node_type,
                 "x": n.x, "y": n.y}
                for n in self.nodes
            ],
            "edges": [
                {"from": e.from_node, "to": e.to_node,
                 "gain": e.gain, "type": e.edge_type}
                for e in self.edges
            ],
        }
