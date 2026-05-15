/**
 * app.js
 * ======
 * Main application controller for SFG Analyzer.
 *
 * Responsibilities:
 *  - State management (edges, blocks, mode)
 *  - API communication with Flask backend
 *  - Results rendering (TF, paths, loops, steps)
 *  - Example loading
 *  - Theme toggle
 *  - Export PNG
 */

'use strict';

// ── Application state ────────────────────────────────────────────────────────

const State = {
  mode:        'edges',   // 'edges' | 'block'
  edges:       [],        // [{from, to, gain}]
  blocks:      [],        // block diagram blocks
  lastResult:  null,      // last API response
  analysing:   false,
  editingBlock: null,     // index of block being edited (modal)
};

// ── Initialisation ────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  SFGRenderer.init('sfg-canvas');
  loadExamples();
});

// ── Mode switching ────────────────────────────────────────────────────────────

function switchMode(mode) {
  State.mode = mode;
  const isEdge = mode === 'edges';
  document.getElementById('mode-edges').style.display = isEdge ? '' : 'none';
  document.getElementById('mode-block').style.display = isEdge ? 'none' : '';
  document.getElementById('tab-edges').classList.toggle('active', isEdge);
  document.getElementById('tab-block').classList.toggle('active', !isEdge);
}

// ── Edge list management ──────────────────────────────────────────────────────

function addEdge() {
  const f = $v('ef').trim(), t = $v('et').trim(), g = $v('eg').trim();
  if (!f || !t || !g) { showError('Fill in From, To, and Gain fields'); return; }
  State.edges.push({ from: f, to: t, gain: g });
  $('ef').value = ''; $('et').value = ''; $('eg').value = '';
  renderEdgeList();
  hideError();
}

function removeEdge(i) {
  State.edges.splice(i, 1);
  renderEdgeList();
}

function clearEdges() {
  State.edges = [];
  renderEdgeList();
  SFGRenderer.clear();
  clearResults();
}

function renderEdgeList() {
  const el = $('edges-list');
  $('edges-count').textContent = `${State.edges.length} edge${State.edges.length === 1 ? '' : 's'}`;
  if (!State.edges.length) {
    el.innerHTML = '<div class="empty-hint">Add edges above to build your SFG</div>';
    return;
  }
  el.innerHTML = State.edges.map((e, i) => `
    <div class="edge-item animated">
      <span class="edge-item-label">
        <span class="edge-item-from">${e.from}</span>
        <span style="color:var(--text3)"> → </span>
        <span class="edge-item-to">${e.to}</span>
        <span class="edge-item-gain"> : ${e.gain}</span>
      </span>
      <button class="edge-del" onclick="removeEdge(${i})" title="Remove">✕</button>
    </div>
  `).join('');
}

// ── Block diagram management ───────────────────────────────────────────────────

const BLOCK_TEMPLATES = {
  tf: {
    title: 'Transfer Function Block',
    fields: [
      { id: 'from', label: 'From node', placeholder: 'e.g. E' },
      { id: 'to',   label: 'To node',   placeholder: 'e.g. Y' },
      { id: 'gain', label: 'Gain',       placeholder: 'e.g. G1 or 1/(s+2)' },
    ],
    tag: 'TF', tagClass: 'bd-tag-tf',
    summary: b => `${b.from} → ${b.to} [${b.gain}]`,
  },
  summing: {
    title: 'Summing Junction',
    fields: [
      { id: 'output',  label: 'Output node', placeholder: 'e.g. E' },
      { id: 'inputs',  label: 'Inputs (node:sign, ...)', placeholder: 'R:+, Y_fb:-' },
    ],
    tag: 'SUM', tagClass: 'bd-tag-sum',
    summary: b => `Σ → ${b.output}  (inputs: ${b.inputs})`,
  },
  feedback: {
    title: 'Feedback Branch',
    fields: [
      { id: 'from', label: 'From node (output side)', placeholder: 'e.g. Y' },
      { id: 'to',   label: 'To node (input side)',   placeholder: 'e.g. E_fb' },
      { id: 'gain', label: 'Feedback gain',            placeholder: 'e.g. -H or 1' },
    ],
    tag: 'FB', tagClass: 'bd-tag-fb',
    summary: b => `${b.from} → ${b.to} [${b.gain}]`,
  },
  branch: {
    title: 'Branch (Signal Splitter)',
    fields: [
      { id: 'from', label: 'From node', placeholder: 'e.g. Y' },
      { id: 'to',   label: 'To nodes (comma-separated)', placeholder: 'e.g. Y1, Y2' },
    ],
    tag: 'BR', tagClass: 'bd-tag-branch',
    summary: b => `${b.from} → [${b.to}]`,
  },
};

function addBlock(type) {
  State.editingBlock = null;
  openBlockModal(type, {});
}

function openBlockModal(type, data) {
  const tmpl = BLOCK_TEMPLATES[type];
  if (!tmpl) return;
  $('modal-title').textContent = tmpl.title;
  $('block-modal').dataset.blockType = type;
  $('block-modal').style.display = 'flex';

  $('modal-body').innerHTML = tmpl.fields.map(f => `
    <div class="modal-field">
      <label>${f.label}</label>
      <input id="mf-${f.id}" class="inp" placeholder="${f.placeholder}" value="${data[f.id] || ''}">
      ${f.hint ? `<div class="modal-hint">${f.hint}</div>` : ''}
    </div>
  `).join('');
}

function saveBlock() {
  const type = $('block-modal').dataset.blockType;
  const tmpl = BLOCK_TEMPLATES[type];
  if (!tmpl) return;

  const block = { id: `${type}_${Date.now()}`, type };
  tmpl.fields.forEach(f => {
    block[f.id] = document.getElementById(`mf-${f.id}`)?.value.trim() || '';
  });

  // Validate required fields
  for (const f of tmpl.fields) {
    if (!block[f.id]) { alert(`Please fill in: ${f.label}`); return; }
  }

  if (State.editingBlock !== null) {
    State.blocks[State.editingBlock] = block;
  } else {
    State.blocks.push(block);
  }

  closeModal();
  renderBlockList();
}

function closeModal(e) {
  if (e && e.target !== $('block-modal')) return;
  $('block-modal').style.display = 'none';
}

function clearBlocks() { State.blocks = []; renderBlockList(); }

function renderBlockList() {
  const el = $('bd-blocks-list');
  if (!State.blocks.length) {
    el.innerHTML = '<div class="empty-hint">Add blocks above</div>';
    return;
  }
  el.innerHTML = State.blocks.map((b, i) => {
    const tmpl = BLOCK_TEMPLATES[b.type] || {};
    const summary = tmpl.summary ? tmpl.summary(b) : b.type;
    const tagClass = tmpl.tagClass || '';
    const tag = tmpl.tag || b.type.toUpperCase();
    return `<div class="bd-block-item animated">
      <span class="bd-tag ${tagClass}">${tag}</span>
      <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;margin:0 6px">${summary}</span>
      <button class="edge-del" onclick="State.blocks.splice(${i},1);renderBlockList()" title="Remove">✕</button>
    </div>`;
  }).join('');
}

// ── Example loading ───────────────────────────────────────────────────────────

async function loadExamples() {
  try {
    const res  = await fetch('/api/examples');
    const data = await res.json();
    const el   = $('examples-list');
    if (!data.success) { el.innerHTML = '<div class="loading-text">Failed to load</div>'; return; }
    el.innerHTML = data.examples.map((ex, i) => `
      <button class="example-btn animated" onclick="loadExample(${i})">
        <span class="example-name">${ex.name}</span>
        <span class="example-desc">${ex.description}</span>
      </button>
    `).join('');
    // Cache examples
    window._examples = data.examples;
  } catch (e) {
    $('examples-list').innerHTML = '<div class="loading-text">Server unavailable</div>';
  }
}

async function loadExample(i) {
  const ex = window._examples?.[i];
  if (!ex) return;

  hideError();
  if (ex.type === 'edge_list') {
    State.mode = 'edges';
    switchMode('edges');
    State.edges = [...ex.data.edges];
    $('esrc').value = ex.data.source;
    $('esnk').value = ex.data.sink;
    renderEdgeList();
  } else if (ex.type === 'block_diagram') {
    State.mode = 'block';
    switchMode('block');
    State.blocks = [...ex.data.blocks];
    $('bd-source').value = ex.data.source;
    $('bd-sink').value   = ex.data.sink;
    renderBlockList();
  }
  // Auto-analyze
  await analyze();
}

// ── Analysis ──────────────────────────────────────────────────────────────────

async function analyze() {
  if (State.analysing) return;
  hideError();

  let url, body;
  if (State.mode === 'edges') {
    const src = $v('esrc').trim(), snk = $v('esnk').trim();
    if (!State.edges.length) { showError('Add at least one edge'); return; }
    if (!src || !snk) { showError('Set source and sink nodes'); return; }
    url  = '/api/analyze/edge_list';
    body = { edges: State.edges, source: src, sink: snk };
  } else {
    const src = $v('bd-source').trim(), snk = $v('bd-sink').trim();
    if (!State.blocks.length) { showError('Add at least one block'); return; }
    if (!src || !snk) { showError('Set source and sink nodes'); return; }
    url  = '/api/analyze/block_diagram';
    body = {
      source: src,
      sink:   snk,
      blocks: _buildBlocksPayload(),
    };
  }

  // Loading state
  State.analysing = true;
  $('btn-analyze').disabled = true;
  $('analyze-label').textContent = 'Analyzing…';

  try {
    const res  = await fetch(url, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body),
    });
    const data = await res.json();

    if (!data.success) {
      showError(data.error || 'Analysis failed');
      return;
    }
    if (data.analysis.error) {
      showError(data.analysis.error);
    }

    State.lastResult = data;
    $('canvas-empty').style.display = 'none';
    SFGRenderer.render(data.graph);
    renderResults(data.analysis);

  } catch (e) {
    showError(`Network error: ${e.message}`);
  } finally {
    State.analysing = false;
    $('btn-analyze').disabled = false;
    $('analyze-label').textContent = 'Analyze →';
  }
}

function _buildBlocksPayload() {
  return State.blocks.map(b => {
    if (b.type === 'summing') {
      const inputs = b.inputs.split(',').map(s => {
        const [node, sign] = s.trim().split(':');
        return { node: node?.trim(), sign: (sign?.trim() || '+') };
      });
      return { id: b.id, type: 'summing', inputs, output: b.output };
    }
    if (b.type === 'branch') {
      return { id: b.id, type: 'branch', from: b.from, to: b.to.split(',').map(s => s.trim()) };
    }
    if (b.type === 'feedback') {
      return { id: b.id, type: 'feedback', from: b.from, to: b.to, gain: b.gain };
    }
    // tf
    return { id: b.id, type: 'tf', from: b.from, to: b.to, gain: b.gain };
  });
}

// ── Results rendering ─────────────────────────────────────────────────────────

function renderResults(analysis) {
  // ── Transfer Function tab ──────────────────────────────────────────────────
  if (!analysis.error) {
    $('tf-empty').style.display = 'none';
    $('tf-content').style.display = '';
    const tf = analysis.transfer_function;
    $('tf-num').textContent = tf.numerator;
    $('tf-den').textContent = tf.denominator;
    $('m-paths').textContent  = analysis.forward_paths.length;
    $('m-loops').textContent  = analysis.loops.length;
    $('m-ntsets').textContent = analysis.non_touching_sets.length;
    $('delta-expr').textContent = analysis.delta.expression || '1';
  }

  // ── Paths tab ──────────────────────────────────────────────────────────────
  const pathsEl = $('paths-content');
  if (analysis.forward_paths.length) {
    $('paths-empty').style.display = 'none';
    pathsEl.style.display = '';
    pathsEl.innerHTML = analysis.forward_paths.map((fp, i) => `
      <div class="path-card animated" id="path-card-${i}"
           onclick="highlightPath(${i})" title="Click to highlight on graph">
        <div><span class="card-badge badge-path">Path P${fp.index}</span></div>
        <div class="card-route">${fp.path.join(' → ')}</div>
        <div class="card-gain">Gain: ${fp.gain}</div>
        <div class="card-cofactor">Δ${fp.index} = ${fp.cofactor?.expression || '1'}</div>
      </div>
    `).join('');
  } else {
    $('paths-empty').style.display = '';
    pathsEl.style.display = 'none';
  }

  // ── Loops tab ──────────────────────────────────────────────────────────────
  const loopsEl = $('loops-content');
  if (analysis.loops.length) {
    $('loops-empty').style.display = 'none';
    loopsEl.style.display = '';
    loopsEl.innerHTML = analysis.loops.map((lp, i) => `
      <div class="loop-card animated" id="loop-card-${i}"
           onclick="highlightLoop(${i})" title="Click to highlight on graph">
        <div><span class="card-badge badge-loop">Loop L${lp.index}</span></div>
        <div class="card-route">${lp.path.join(' → ')} → ${lp.path[0]}</div>
        <div class="card-gain">Loop gain: ${lp.gain}</div>
      </div>
    `).join('');
    if (analysis.non_touching_sets.length) {
      loopsEl.innerHTML += `
        <div style="margin-top:10px">
          <div class="result-section-title">Non-touching sets (${analysis.non_touching_sets.length})</div>
          ${analysis.non_touching_sets.map((s, i) => `
            <div class="loop-card animated" style="border-color:var(--green)">
              <div class="card-gain">${s.map(l => `L${l.index}`).join(' × ')}</div>
              <div class="card-route" style="font-size:11px">
                Product: ${s.map(l => `(${l.gain})`).join('·')}
              </div>
            </div>
          `).join('')}
        </div>`;
    }
  } else {
    $('loops-empty').style.display = '';
    loopsEl.style.display = 'none';
    $('loops-empty').textContent = 'No loops detected in this graph';
  }

  // ── Steps tab ──────────────────────────────────────────────────────────────
  const stepsEl = $('steps-content');
  if (analysis.steps?.length) {
    $('steps-empty').style.display = 'none';
    stepsEl.style.display = '';
    stepsEl.innerHTML = analysis.steps.map(s => {
      const isHeading = s.startsWith('Step');
      return `<div class="step-item ${isHeading ? 'step-heading' : 'step-detail'}">${_escapeHtml(s)}</div>`;
    }).join('');
  }
}

// ── Highlight control ─────────────────────────────────────────────────────────

function highlightPath(i) {
  const result = State.lastResult;
  if (!result) return;
  const fp = result.analysis.forward_paths[i];
  if (!fp) return;
  SFGRenderer.highlightPath(fp.path);
  // Visual feedback on card
  document.querySelectorAll('.path-card').forEach((el, j) => {
    el.classList.toggle('highlighted', j === i);
  });
  document.querySelectorAll('.loop-card').forEach(el => el.classList.remove('highlighted'));
}

function highlightLoop(i) {
  const result = State.lastResult;
  if (!result) return;
  const lp = result.analysis.loops[i];
  if (!lp) return;
  // Add the start node at the end to complete the visual loop
  SFGRenderer.highlightLoop([...lp.path, lp.path[0]]);
  document.querySelectorAll('.loop-card').forEach((el, j) => {
    el.classList.toggle('highlighted', j === i);
  });
  document.querySelectorAll('.path-card').forEach(el => el.classList.remove('highlighted'));
}

// ── Results tabs ───────────────────────────────────────────────────────────────

function showRTab(name, btn) {
  ['tf','paths','loops','steps'].forEach(t => {
    $(`rp-${t}`).style.display = t === name ? '' : 'none';
    $(`rp-${t}`).classList.toggle('active', t === name);
  });
  document.querySelectorAll('.rtab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  SFGRenderer.clearHighlight();
  document.querySelectorAll('.path-card, .loop-card').forEach(el => el.classList.remove('highlighted'));
}

// ── Layout relayout ────────────────────────────────────────────────────────────

async function relayout(layoutType) {
  if (!State.lastResult) return;
  // Re-request analysis (backend recomputes layout)
  // Simple workaround: just reset view for now
  SFGRenderer.resetView();
}

// ── Theme toggle ───────────────────────────────────────────────────────────────

function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
  $('btn-theme').textContent = isDark ? '☾' : '☀';
  SFGRenderer.draw && SFGRenderer.draw();
}

// ── Export PNG ─────────────────────────────────────────────────────────────────

function exportPNG() { SFGRenderer.exportPNG(); }

// ── Canvas controls ────────────────────────────────────────────────────────────

function zoomIn()   { SFGRenderer.zoomIn();    }
function zoomOut()  { SFGRenderer.zoomOut();   }
function resetView(){ SFGRenderer.resetView(); }

// ── Error display ─────────────────────────────────────────────────────────────

function showError(msg) {
  const el = $('error-box');
  el.textContent = msg;
  el.style.display = '';
}
function hideError() {
  $('error-box').style.display = 'none';
}

function clearResults() {
  ['tf-content','paths-content','loops-content','steps-content'].forEach(id => {
    const el = $(id);
    if (el) el.style.display = 'none';
  });
  ['tf-empty','paths-empty','loops-empty','steps-empty'].forEach(id => {
    const el = $(id);
    if (el) { el.style.display = ''; el.textContent = 'Run analysis to see results'; }
  });
  $('m-paths').textContent = '—';
  $('m-loops').textContent = '—';
  $('m-ntsets').textContent = '—';
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function $(id)    { return document.getElementById(id); }
function $v(id)   { return document.getElementById(id)?.value || ''; }
function _escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Keyboard shortcut: Enter in edge fields → add edge
['ef','et','eg'].forEach(id => {
  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById(id)?.addEventListener('keydown', e => {
      if (e.key === 'Enter') addEdge();
    });
  });
});

async function exportReport() {
  if (!State.lastResult) {
    alert('Run analysis first');
    return;
  }

  const res = await fetch('/api/export_report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ analysis: State.lastResult.analysis })
  });

  const data = await res.json();
  if (!data.success) {
    alert('Failed to export report');
    return;
  }

  const blob = new Blob([data.report], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'SFG_Report.txt';
  a.click();
  URL.revokeObjectURL(url);
}
