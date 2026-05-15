"""
app.py  —  Flask REST API
==========================
Endpoints
---------
POST /api/analyze/block_diagram   — parse block-diagram JSON → full analysis
POST /api/analyze/edge_list       — parse edge-list JSON → full analysis
GET  /api/examples                — return built-in example systems
GET  /api/health                  — health check
"""

from __future__ import annotations
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core import (
    parse_block_diagram,
    parse_edge_list,
    apply_mason,
)
from examples import EXAMPLES

# ─────────────────────────────────────────────────────────────────────────────
# App bootstrap
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static'),
)
CORS(app)   # Allow cross-origin requests (dev convenience)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ok(data: dict, status: int = 200):
    return jsonify({"success": True,  **data}), status

def _err(msg: str, status: int = 400):
    return jsonify({"success": False, "error": msg}), status

def _validate_graph(graph):
    errors = []
    if not getattr(graph, "source", None):
        errors.append("Source node is missing")
    if not getattr(graph, "sink", None):
        errors.append("Sink node is missing")
    if len(getattr(graph, "nodes", [])) < 2:
        errors.append("Graph must contain at least 2 nodes")
    return errors

def _run_analysis(graph) -> dict:
    """Shared analysis pipeline for all endpoints."""
    validation_errors = _validate_graph(graph)
    mason = apply_mason(graph)
    return {
        "graph":    graph.to_dict(),
        "analysis": mason,
        "validation": validation_errors,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


@app.route("/api/health")
def health():
    return _ok({"message": "SFG Analyzer API is running"})


@app.route("/api/examples")
def get_examples():
    """Return the list of built-in example block diagrams."""
    return _ok({"examples": EXAMPLES})


@app.route("/api/analyze/block_diagram", methods=["POST"])
def analyze_block_diagram():
    """
    Parse a block-diagram description and run full Mason analysis.

    Request body: { blocks:[...], source:"...", sink:"..." }
    """
    try:
        data = request.get_json(force=True)
        if data is None:
            return _err("Request body must be valid JSON")
        graph  = parse_block_diagram(data)
        result = _run_analysis(graph)
        return _ok(result)
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        app.logger.exception("Unexpected error in /analyze/block_diagram")
        return _err(f"Internal error: {e}", 500)


@app.route("/api/analyze/edge_list", methods=["POST"])
def analyze_edge_list():
    """
    Parse a raw edge-list and run full Mason analysis.

    Request body: { edges:[{from,to,gain},...], source:"...", sink:"..." }
    """
    try:
        data = request.get_json(force=True)
        if data is None:
            return _err("Request body must be valid JSON")
        graph  = parse_edge_list(data)
        result = _run_analysis(graph)
        return _ok(result)
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        app.logger.exception("Unexpected error in /analyze/edge_list")
        return _err(f"Internal error: {e}", 500)



@app.route("/api/export_report", methods=["POST"])
def export_report():
    """Export a readable text report for the latest analysis."""
    try:
        data = request.get_json(force=True)
        analysis = data.get("analysis", {})
        lines = [
            "SFG Analyzer Report",
            "=" * 40,
            "",
            "Forward Paths:"
        ]

        for fp in analysis.get("forward_paths", []):
            lines.append(f"P{fp['index']}: {' -> '.join(fp['path'])} | Gain = {fp['gain']}")

        lines.append("\nLoops:")
        for lp in analysis.get("loops", []):
            lines.append(f"L{lp['index']}: {' -> '.join(lp['path'])} | Gain = {lp['gain']}")

        tf = analysis.get("transfer_function", {})
        lines.append("\nTransfer Function:")
        lines.append(tf.get("expression", "N/A"))

        return _ok({"report": "\n".join(lines)})
    except Exception as e:
        return _err(str(e), 500)

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
