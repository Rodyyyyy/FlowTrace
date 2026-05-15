# FlowTrace Studio: Signal Flow and Mason Analysis

FlowTrace Studio is a professional-grade engineering workbench designed to bridge the gap between complex control system definitions and mathematical analysis. It provides an automated environment for converting Block Diagrams and Edge Lists into Signal Flow Graphs (SFG) and deriving transfer functions via Mason's Gain Formula.

---

## Project Overview

In control systems engineering, manually reducing a block diagram into a transfer function is often tedious and error-prone. FlowTrace Studio automates this process using a custom graph-theory engine. The application offers a cinematic, editorial-style interface that visualizes system variables as nodes and transfer functions as directed branches.

### Core Objectives

- **Automated Analysis**  
  Eliminate manual calculation errors when identifying forward paths, loops, and non-touching loops.

- **Visual Clarity**  
  Provide an interactive canvas where users can explore, drag, zoom, and rearrange graph topology.

- **Mathematical Transparency**  
  Generate a detailed step-by-step breakdown of Mason’s Gain Formula for learning and documentation.

---

# Technical Architecture

The project follows a decoupled full-stack architecture.

## Backend (Python / Flask)

The backend handles graph processing, symbolic analysis, and Mason’s Formula computation using Python and NetworkX.

### Main Modules

#### `app.py`
Handles:
- Flask server setup
- REST API routes
- Request validation
- Communication between frontend and solver engine

#### `mason_formula.py`
Implements:
- Mason’s Gain Formula orchestration
- Delta computation
- Transfer function generation

#### `graph_algorithms.py`
Contains:
- DFS-based forward path discovery
- Cycle / loop detection
- Non-touching loop combination generation
- Graph traversal utilities

#### `block_diagram_parser.py`
Converts high-level block diagram elements into signal flow graphs:
- Transfer function blocks
- Summing junctions
- Branch points
- Feedback paths

#### `layout.py`
Provides automatic graph layouts:
- Force-directed (spring) layout
- Hierarchical layout
- Coordinate generation for visualization

---

## Frontend (HTML / CSS / JavaScript)

The frontend focuses on editorial UI design with glassmorphism styling and interactive graph rendering.

### Main Files

#### `index.html`
Provides:
- Main dashboard
- Input panels
- Results sidebar
- Modal structures

#### `style.css`
Implements:
- Warm-vanilla cinematic theme
- Glassmorphism effects
- Ink-inspired typography
- Depth and shadow styling

#### `sfg-renderer.js`
Custom HTML5 Canvas renderer supporting:
- Zooming
- Panning
- Real-time node dragging
- Edge rendering
- Path highlighting

#### `app.js`
Handles:
- Application state management
- API communication
- Modal interactions
- Dynamic UI updates

---

# Installation and Setup

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/flowtrace-studio.git
cd flowtrace-studio
