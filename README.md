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

Install the required Python libraries:

```bash
pip install flask flask-cors networkx
```

Or using a requirements file:

```bash
pip install -r requirements.txt
```

Example `requirements.txt`:

```txt
flask
flask-cors
networkx
```

---

## Step 3: Run the Application

Start the Flask server:

```bash
python app.py
```

The application will be available at:

```txt
http://127.0.0.1:5000
```

Open the URL in your web browser.

---

# Usage Guide

## 1. Defining the System

FlowTrace supports two input modes.

### Edge List Mode

Define the graph directly by specifying:

- Source node
- Destination node
- Symbolic gain

Example:

```txt
X1 -> X2 : G1
X2 -> X3 : G2
X3 -> X2 : -H1
```

---

### Block Diagram Mode

Build systems visually using:

- Transfer function blocks
- Summing junctions
- Branch nodes
- Feedback loops

The parser automatically converts the diagram into a signal flow graph.

---

## 2. Running Analysis

Click the **Analyze System** button.

The backend performs:

- Forward path detection
- Feedback loop discovery
- Non-touching loop generation
- Delta calculation
- Cofactor computation
- Final transfer function derivation

---

## 3. Reviewing Results

The results sidebar displays:

### Transfer Function

The symbolic expression of:

```math
T(s)
```

---

### Path Highlighting

Selecting a path or loop highlights it directly on the graph canvas.

---

### Step-by-Step Report

Detailed breakdown of:

- Forward path gains
- Loop gains
- Delta terms
- Cofactors
- Final Mason expansion

---

# Mathematical Implementation

The transfer function is computed using Mason’s Gain Formula:

$$
T(s)=\frac{\sum P_k \Delta_k}{\Delta}
$$

Where:

- \(P_k\)  
  Gain of the \(k\)-th forward path

- \(\Delta\)  
  Graph determinant:

$$
\Delta =
1
-
(\text{sum of individual loop gains})
+
(\text{sum of products of two non-touching loops})
-
(\text{sum of products of three non-touching loops})
+\cdots
$$

- \(\Delta_k\)  
  Cofactor for path \(P_k\), computed using loops that do not touch that path.

---

# Features

## Signal Flow Graph Visualization

- Interactive node dragging
- Zoom and pan support
- Dynamic edge rendering
- Loop highlighting

---

## Mason Analysis Engine

- Automatic forward path generation
- Feedback loop detection
- Non-touching loop analysis
- Symbolic transfer function computation

---

## Educational Reporting

- Step-by-step derivation
- Formula transparency
- Debug-friendly graph breakdowns

---

# Future Improvements

Potential enhancements include:

- Symbolic algebra simplification
- Export to PDF / LaTeX
- Bode and Nyquist plotting
- State-space conversion
- Real-time collaborative editing
- Dark/light theme switching
- Graph persistence and project saving
