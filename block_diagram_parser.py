"""
block_diagram_parser.py
=======================
Converts a block-diagram description (JSON/dict) into an SFGGraph.

Block Diagram JSON schema
--------------------------
{
  "blocks": [
    {"id": "G1", "type": "tf",       "gain": "G1",  "from": "x1", "to": "x2"},
    {"id": "S1", "type": "summing",  "inputs": [{"node":"x0","sign":"+"},
                                                 {"node":"xfb","sign":"-"}],
                                      "output": "x1"},
    {"id": "B1", "type": "branch",   "from": "x2",  "to": ["x3","x4"]}
  ],
  "source": "x0",
  "sink":   "x3"
}

Component types
---------------
tf       – Transfer-function block:  adds a single directed edge with given gain.
summing  – Summing junction:         adds incoming edges (+1 or -1 gain) from
           each listed input to the output node.
branch   – Branch point:             adds edges with gain "1" to each output node.
direct   – Direct edge (gain given explicitly).

The parser also auto-assigns node types (source / sink / signal) and triggers
a simple force-directed layout so the frontend gets initial x/y positions.
"""

from __future__ import annotations
from typing import Any

from .graph_model import SFGGraph, Node, Edge
from .layout import spring_layout


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def parse_block_diagram(data: dict) -> SFGGraph:
    """
    Parse a block-diagram dict and return a fully constructed SFGGraph.

    Parameters
    ----------
    data : dict
        Block diagram description (see module docstring for schema).

    Returns
    -------
    SFGGraph
        Populated graph ready for analysis.

    Raises
    ------
    ValueError
        If required fields are missing or a block type is unknown.
    """
    _validate_input(data)

    source: str = data["source"]
    sink: str   = data["sink"]
    blocks: list = data.get("blocks", [])

    node_set: dict[str, Node] = {}   # id → Node (deduplication)
    edges: list[Edge] = []

    def ensure_node(nid: str, label: str | None = None) -> Node:
        """Return existing node or create a new signal node."""
        if nid not in node_set:
            node_set[nid] = Node(id=nid, label=label or nid)
        return node_set[nid]

    # ── Process each block ──────────────────────────────────────────────────
    for block in blocks:
        btype = block.get("type", "").lower()
        bid   = block.get("id", "?")

        if btype == "tf":
            # Transfer-function block: one directed edge
            fn = block["from"]
            tn = block["to"]
            gain = str(block.get("gain", bid))
            ensure_node(fn)
            ensure_node(tn)
            edges.append(Edge(from_node=fn, to_node=tn, gain=gain,
                              edge_type="forward"))

        elif btype == "summing":
            # Summing junction: multiple inputs fan into one output
            out_node = block["output"]
            ensure_node(out_node, label=f"Σ({out_node})")
            for inp in block.get("inputs", []):
                in_node = inp["node"]
                sign    = "+" if inp.get("sign", "+") == "+" else "-"
                gain    = "1" if sign == "+" else "-1"
                ensure_node(in_node)
                edges.append(Edge(from_node=in_node, to_node=out_node,
                                  gain=gain, edge_type="forward"))

        elif btype == "branch":
            # Branch point: one input fans out to many outputs
            fn = block["from"]
            ensure_node(fn)
            for tn in block.get("to", []):
                ensure_node(tn)
                edges.append(Edge(from_node=fn, to_node=tn, gain="1",
                                  edge_type="forward"))

        elif btype == "direct":
            # Explicit directed edge
            fn   = block["from"]
            tn   = block["to"]
            gain = str(block.get("gain", "1"))
            ensure_node(fn)
            ensure_node(tn)
            etype = "feedback" if block.get("feedback", False) else "forward"
            edges.append(Edge(from_node=fn, to_node=tn, gain=gain,
                              edge_type=etype))

        elif btype == "feedback":
            # Explicit feedback branch
            fn   = block["from"]
            tn   = block["to"]
            gain = str(block.get("gain", "1"))
            ensure_node(fn)
            ensure_node(tn)
            edges.append(Edge(from_node=fn, to_node=tn, gain=gain,
                              edge_type="feedback"))

        else:
            raise ValueError(f"Unknown block type '{btype}' in block '{bid}'")

    # ── Tag source / sink ───────────────────────────────────────────────────
    ensure_node(source).node_type = "source"
    ensure_node(sink).node_type   = "sink"

    # ── Detect self-loops ───────────────────────────────────────────────────
    for e in edges:
        if e.from_node == e.to_node:
            e.edge_type = "self"

    # ── Assemble graph ──────────────────────────────────────────────────────
    graph = SFGGraph(
        nodes=list(node_set.values()),
        edges=edges,
        source=source,
        sink=sink,
    )

    # ── Assign layout positions ─────────────────────────────────────────────
    spring_layout(graph)

    return graph


# ─────────────────────────────────────────────────────────────────────────────
# Direct SFG edge-list parser (used when the user adds edges manually in the UI)
# ─────────────────────────────────────────────────────────────────────────────

def parse_edge_list(data: dict) -> SFGGraph:
    """
    Build an SFGGraph directly from a list of edges.

    Input schema:
    {
      "edges": [{"from": "x1", "to": "x2", "gain": "G1"}, ...],
      "source": "x1",
      "sink":   "x4"
    }
    """
    if "edges" not in data:
        raise ValueError("'edges' key is required")
    if "source" not in data or "sink" not in data:
        raise ValueError("'source' and 'sink' keys are required")

    node_set: dict[str, Node] = {}
    edges: list[Edge] = []

    def ensure_node(nid: str) -> Node:
        if nid not in node_set:
            node_set[nid] = Node(id=nid, label=nid)
        return node_set[nid]

    for e in data["edges"]:
        fn = str(e["from"])
        tn = str(e["to"])
        gain = str(e.get("gain", "1"))
        ensure_node(fn)
        ensure_node(tn)
        etype = "self" if fn == tn else ("feedback" if e.get("feedback") else "forward")
        edges.append(Edge(from_node=fn, to_node=tn, gain=gain, edge_type=etype))

    source = str(data["source"])
    sink   = str(data["sink"])
    ensure_node(source).node_type = "source"
    ensure_node(sink).node_type   = "sink"

    graph = SFGGraph(
        nodes=list(node_set.values()),
        edges=edges,
        source=source,
        sink=sink,
    )
    spring_layout(graph)
    return graph


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _validate_input(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object (dict)")
    for key in ("source", "sink"):
        if key not in data:
            raise ValueError(f"Missing required key: '{key}'")
    if not isinstance(data.get("blocks", []), list):
        raise ValueError("'blocks' must be a list")
