"""
HelixForge — Genome Assembler  |  Precision Biotech Lab UI
Run:  streamlit run app.py
"""

import json, subprocess, tempfile, shutil
from pathlib import Path

import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="HelixForge — Genome Assembler",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR   = Path(__file__).parent
ASSEMBLER  = BASE_DIR / ("assembler.exe" if (BASE_DIR / "assembler.exe").exists() else "assembler")
OUTPUT_DIR = BASE_DIR / "output"

# ─────────────────────────────────────────────
#  GLOBAL CSS — Precision Lab theme
# ─────────────────────────────────────────────
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&family=Syne:wght@600;700;800&display=swap');

:root {
  --bg:        #0d0f12;
  --bg2:       #111417;
  --surface:   #161a1f;
  --surface2:  #1c2128;
  --border:    rgba(255,255,255,.07);
  --border2:   rgba(255,255,255,.12);

  --acid:      #b8ff57;      /* signature accent — acid-green */
  --acid-dim:  rgba(184,255,87,.15);
  --acid-glow: rgba(184,255,87,.08);

  --blue:      #4d9fff;
  --blue-dim:  rgba(77,159,255,.12);
  --teal:      #2dd4bf;
  --amber:     #f59e0b;
  --rose:      #fb7185;

  --text:      #c9d1d9;
  --muted:     rgba(140,150,165,.6);
  --mono:      'IBM Plex Mono', monospace;
  --sans:      'IBM Plex Sans', sans-serif;
  --display:   'Syne', sans-serif;
}

@keyframes fade-up   { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
@keyframes pulse-dot { 0%,100%{opacity:.5;transform:scale(1)} 50%{opacity:1;transform:scale(1.2)} }
@keyframes scan      { 0%{background-position:0 -100%} 100%{background-position:0 200%} }

html,[class*="css"] { font-family: var(--sans); }

.stApp {
  background: var(--bg);
  background-image:
    radial-gradient(ellipse 60% 50% at 80% 10%, rgba(184,255,87,.03) 0%, transparent 60%),
    radial-gradient(ellipse 40% 40% at 10% 90%, rgba(77,159,255,.04) 0%, transparent 60%);
}
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding:1.6rem 2rem 4rem; max-width:1480px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
  background: rgba(184,255,87,.03) !important;
  border: 1px solid rgba(184,255,87,.2) !important;
  border-radius: 6px !important;
  transition: border-color .25s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: rgba(184,255,87,.5) !important;
}

/* ── Slider ── */
[data-testid="stSlider"] [class*="track"]         { background: var(--surface2) !important; }
[data-testid="stSlider"] [class*="track--filled"] { background: var(--acid) !important; }
[data-testid="stSlider"] [class*="thumb"]         {
  background: var(--bg) !important;
  border: 2px solid var(--acid) !important;
  box-shadow: 0 0 10px rgba(184,255,87,.4) !important;
}

/* ── Buttons ── */
.stButton > button {
  background: var(--acid) !important;
  color: #0d0f12 !important;
  font-family: var(--mono) !important;
  font-weight: 600 !important;
  font-size: .78rem !important;
  letter-spacing: .12em !important;
  text-transform: uppercase !important;
  border: none !important;
  border-radius: 4px !important;
  padding: .65rem 1.4rem !important;
  box-shadow: 0 0 20px rgba(184,255,87,.25) !important;
  transition: all .2s !important;
}
.stButton > button:hover {
  filter: brightness(1.1) !important;
  box-shadow: 0 0 32px rgba(184,255,87,.4) !important;
  transform: translateY(-1px) !important;
}

/* ── Download buttons ── */
[data-testid="stDownloadButton"] > button {
  background: transparent !important;
  color: var(--text) !important;
  border: 1px solid var(--border2) !important;
  font-family: var(--mono) !important;
  font-size: .72rem !important;
  border-radius: 4px !important;
  letter-spacing: .05em !important;
  transition: all .2s !important;
}
[data-testid="stDownloadButton"] > button:hover {
  background: var(--surface2) !important;
  border-color: var(--acid) !important;
  color: var(--acid) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
}
[data-testid="stExpander"] summary {
  color: var(--text) !important;
  font-family: var(--mono) !important;
  font-size: .76rem !important;
}
[data-testid="stExpander"] > div { background: var(--surface) !important; }

/* ── Code ── */
pre, code {
  background: #080a0e !important;
  color: var(--acid) !important;
  font-family: var(--mono) !important;
  font-size: .74rem !important;
}
.stCodeBlock * { background: #080a0e !important; color: var(--acid) !important; }

/* ── DataFrames ── */
.stDataFrame { border: 1px solid var(--border) !important; border-radius: 6px !important; }
.stDataFrame thead th {
  background: var(--surface2) !important;
  color: var(--acid) !important;
  font-family: var(--mono) !important;
  font-size: .72rem !important;
  letter-spacing: .06em !important;
}
.stDataFrame tbody td {
  background: var(--surface) !important;
  color: var(--text) !important;
  font-family: var(--mono) !important;
  font-size: .76rem !important;
  border-color: var(--border) !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--acid) !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] { gap:.3rem; border-bottom:1px solid var(--border); }
[data-testid="stTabs"] [role="tab"] {
  font-family: var(--mono) !important;
  font-size: .68rem !important;
  font-weight: 500 !important;
  letter-spacing: .1em !important;
  color: var(--muted) !important;
  border-radius: 4px 4px 0 0 !important;
  border: 1px solid transparent !important;
  border-bottom: none !important;
  padding: .45rem 1rem !important;
  transition: all .2s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  color: var(--acid) !important;
  border-color: var(--border) !important;
  background: var(--surface) !important;
  border-bottom-color: var(--bg) !important;
}

/* ─────────────────────────────
   CUSTOM COMPONENTS
───────────────────────────── */

/* Hero */
.hf-hero { padding:1.8rem 0 .8rem; animation:fade-up .5s ease both; }

.hf-logo-wrap { display:flex; align-items:center; gap:1rem; margin-bottom:.6rem; }
.hf-helix-icon {
  width:38px; height:38px; flex-shrink:0;
  background: var(--acid);
  border-radius:6px;
  display:flex; align-items:center; justify-content:center;
  font-size:1.3rem; line-height:1;
  box-shadow: 0 0 24px rgba(184,255,87,.3);
}
.hf-logo {
  font-family: var(--display);
  font-weight: 800;
  font-size: 2.4rem;
  color: #fff;
  letter-spacing: -.02em;
  line-height: 1;
}
.hf-logo span { color: var(--acid); }
.hf-sub {
  font-family: var(--mono);
  font-size: .64rem;
  color: var(--muted);
  letter-spacing: .18em;
  text-transform: uppercase;
  margin-top: .3rem;
  padding-left: 50px;
}

.hf-divider {
  height: 1px;
  background: var(--border);
  margin: 1rem 0;
  position: relative;
}
.hf-divider::after {
  content:'';
  position:absolute; left:0; top:0;
  width:120px; height:1px;
  background: var(--acid);
  opacity: .6;
}

/* Section label */
.hf-section {
  font-family: var(--mono);
  font-size: .6rem;
  font-weight: 600;
  letter-spacing: .22em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 2rem 0 .9rem;
  display: flex;
  align-items: center;
  gap: .6rem;
}
.hf-section::before {
  content: '';
  width: 3px; height: 3px;
  background: var(--acid);
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px var(--acid);
}
.hf-section::after {
  content: '';
  flex: 1; height: 1px;
  background: var(--border);
}

/* KPI cards */
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:.65rem; margin:.4rem 0 1rem; }
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: .9rem .85rem .8rem;
  position: relative;
  overflow: hidden;
  transition: border-color .2s, transform .2s;
}
.kpi-card::after {
  content:'';
  position:absolute; bottom:0; left:0; right:0; height:1px;
  background: var(--accent, var(--acid));
  opacity: .4;
}
.kpi-card:hover { border-color:var(--border2); transform:translateY(-2px); }
.kpi-label { font-family:var(--mono); font-size:.58rem; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); margin-bottom:.4rem; }
.kpi-value { font-family:var(--display); font-weight:700; font-size:1.45rem; color:#fff; line-height:1.1; }
.kpi-unit  { font-family:var(--mono); font-size:.58rem; color:var(--muted); margin-top:.1rem; }

/* Method badge */
.method-badge {
  display:inline-flex; align-items:center; gap:.7rem;
  background: var(--surface);
  border: 1px solid var(--border2);
  border-left: 2px solid var(--acid);
  border-radius: 0 4px 4px 0;
  padding: .5rem 1rem;
  margin: .5rem 0 .9rem;
}
.method-label { font-family:var(--mono); font-size:.62rem; color:var(--muted); letter-spacing:.1em; text-transform:uppercase; }
.method-value { font-family:var(--mono); font-size:.8rem; font-weight:600; color:var(--acid); }

/* Sequence terminal */
.seq-terminal { background:#080a0e; border:1px solid var(--border); border-radius:6px; overflow:hidden; }
.seq-bar {
  background:var(--surface2);
  padding:.45rem .9rem;
  display:flex; align-items:center; gap:.45rem;
  border-bottom:1px solid var(--border);
}
.seq-dot { width:9px; height:9px; border-radius:50%; }
.seq-title { font-family:var(--mono); font-size:.64rem; color:var(--muted); margin-left:.3rem; }
.seq-body {
  font-family: var(--mono); font-size:.71rem; line-height:1.85;
  color: var(--acid); padding:1rem 1rem; max-height:180px;
  overflow-y:auto; word-break:break-all; white-space:pre-wrap;
  opacity: .85;
}
.seq-body::-webkit-scrollbar { width:3px; }
.seq-body::-webkit-scrollbar-thumb { background:var(--border2); border-radius:2px; }

/* Pipeline steps */
.pipeline { display:grid; grid-template-columns:repeat(7,1fr); gap:0; margin:1rem 0 1.8rem; border:1px solid var(--border); border-radius:6px; overflow:hidden; }
.pipe-step {
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 1.1rem .6rem .9rem;
  text-align: center;
  position: relative;
  transition: background .2s;
}
.pipe-step:last-child { border-right:none; }
.pipe-step:hover { background:var(--surface2); }
.pipe-step:hover .pipe-num { color: var(--acid); }
.pipe-num   { font-family:var(--mono); font-size:.56rem; color:var(--muted); letter-spacing:.1em; margin-bottom:.3rem; }
.pipe-icon  { font-size:1.2rem; margin:.2rem 0; }
.pipe-title { font-family:var(--mono); font-weight:600; font-size:.64rem; color:#fff; margin-bottom:.12rem; }
.pipe-sub   { font-family:var(--mono); font-size:.54rem; color:var(--muted); }

/* Problem card */
.problem-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.6rem 1.8rem;
  margin: 1rem 0 1.4rem;
  position: relative;
  overflow: hidden;
}
.problem-card::before {
  content:'';
  position:absolute; top:0; left:0; right:0; height:2px;
  background: linear-gradient(90deg, var(--acid) 0%, var(--blue) 50%, transparent 100%);
  opacity:.5;
}
.problem-title { font-family:var(--display); font-weight:700; font-size:1rem; color:#fff; margin-bottom:.9rem; }
.problem-grid  { display:grid; grid-template-columns:repeat(3,1fr); gap:.85rem; margin-top:.9rem; }
.prob-item     { background:var(--surface2); border:1px solid var(--border); border-radius:6px; padding:.8rem .9rem; }
.prob-item-title { font-family:var(--mono); font-size:.6rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.35rem; }
.prob-item-text  { font-family:var(--sans); font-size:.79rem; color:var(--text); line-height:1.65; }

/* Kmer preview */
.kmer-preview {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: .65rem .9rem;
  font-family: var(--mono);
  font-size: .7rem;
  color: var(--muted);
  margin: .3rem 0 .8rem;
}
.kmer-seq  { font-size:.76rem; letter-spacing:.04em; line-height:1.8; }
.kmer-high { color:#0d0f12; background: var(--acid); border-radius:3px; padding:1px 3px; font-weight:600; }
.kmer-info { margin-top:.3rem; font-size:.62rem; display:flex; gap:1.2rem; flex-wrap:wrap; }
.kmer-info-item { color:var(--muted); }
.kmer-info-item span { color: var(--acid); font-weight:500; }

/* Verify card */
.verify-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.1rem 1.3rem;
  margin: .5rem 0 .9rem;
}
.verify-title { font-family:var(--mono); font-size:.62rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.85rem; color:var(--muted); }
.verify-row {
  display:flex; align-items:center; gap:.75rem;
  padding:.4rem 0; border-bottom:1px solid var(--border);
  font-family:var(--mono); font-size:.74rem;
}
.verify-row:last-child { border-bottom:none; }
.verify-label { color:var(--muted); width:130px; flex-shrink:0; font-size:.66rem; }
.verify-bar-wrap { flex:1; height:4px; background:var(--surface2); border-radius:2px; overflow:hidden; }
.verify-bar { height:100%; border-radius:2px; transition:width .6s ease; }
.verify-status { font-size:.65rem; font-weight:600; letter-spacing:.06em; white-space:nowrap; }
.verify-val { color:#fff; width:80px; text-align:right; flex-shrink:0; font-size:.72rem; }

.blast-btn {
  display:inline-flex; align-items:center; gap:.4rem;
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius:4px; padding:.45rem .9rem;
  font-family:var(--mono); font-size:.68rem;
  color:var(--text); text-decoration:none; margin-top:.5rem;
  transition: all .2s;
}
.blast-btn:hover { border-color:var(--acid); color:var(--acid); }

/* Repeat card */
.repeat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 2px solid var(--amber);
  border-radius: 0 6px 6px 0;
  padding: .9rem 1.1rem;
  margin-top:.5rem;
}
.repeat-title { font-family:var(--mono); font-size:.62rem; font-weight:600; color:var(--amber); letter-spacing:.1em; text-transform:uppercase; margin-bottom:.5rem; }
.repeat-zero { font-family:var(--mono); font-size:.74rem; color:var(--muted); }

/* Info banner */
.info-banner {
  background: var(--acid-glow);
  border: 1px solid rgba(184,255,87,.15);
  border-left: 2px solid var(--acid);
  border-radius: 0 6px 6px 0;
  padding: .8rem 1.1rem;
  font-family: var(--mono);
  font-size: .76rem;
  color: var(--text);
  margin: .7rem 0;
}

/* Sidebar */
.sb-logo {
  font-family: var(--display);
  font-weight: 800;
  font-size: 1.15rem;
  color: #fff;
  padding: .3rem 0 .9rem;
  display:flex; align-items:center; gap:.5rem;
}
.sb-logo span { color: var(--acid); }
.sb-section {
  font-family: var(--mono) !important;
  font-size: .56rem !important;
  font-weight: 600 !important;
  letter-spacing: .2em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  margin: 1rem 0 .4rem !important;
  padding-bottom: .3rem !important;
  border-bottom: 1px solid var(--border) !important;
}

/* Overall badge */
.overall-badge {
  display:inline-flex; align-items:center; gap:.6rem;
  background: var(--acid-glow);
  border: 1px solid rgba(184,255,87,.2);
  border-radius: 4px;
  padding: .45rem .9rem;
  margin-top: .7rem;
}
.overall-label { font-family:var(--mono); font-size:.62rem; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; }
.overall-value { font-family:var(--mono); font-size:.8rem; font-weight:600; color:var(--acid); }

/* Comparison row */
.cmp-row { display:flex; gap:.8rem; margin:.4rem 0 .9rem; }
.cmp-box { flex:1; background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:.65rem .9rem; }
.cmp-box-label { font-family:var(--mono); font-size:.58rem; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }
.cmp-box-value { font-family:var(--display); font-size:.95rem; font-weight:700; margin-top:.2rem; color:#fff; }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HELPERS  (unchanged logic)
# ─────────────────────────────────────────────
def parse_stats(path: Path) -> dict:
    text  = path.read_text(errors="replace")
    lines = text.splitlines()
    data  = {
        "reads":"—","total_kmers":"—","kmer_size":"—",
        "nodes":"—","edges":"—",
        "method":"—","dijk_len":"—","hier_len":"—",
        "final_len":"—","gc":"—","n50":"—",
        "min_repeat":"—","repeat_regions":"0",
        "theoretical":[],"measured":{},"overall":"O(N + V + E)",
    }
    in_theo = False
    in_meas = False

    for line in lines:
        s = line.strip()
        if not s or s.startswith("="):
            continue
        if "Time Complexity" in s:
            in_theo = True;  in_meas = False;  continue
        if "Execution Time"  in s:
            in_theo = False; in_meas = True;   continue
        if ":" not in s:
            continue

        raw_key, _, raw_val = s.partition(":")
        k_str = raw_key.strip()
        v_str = raw_val.strip()
        kl    = k_str.lower()

        if in_theo:
            if "overall" in kl:
                data["overall"] = v_str
            elif v_str:
                step_name = k_str.lstrip("- ").strip()
                if " - " in v_str:
                    complexity, desc_tail = v_str.split(" - ", 1)
                    complexity = complexity.strip(); desc_tail = desc_tail.strip()
                else:
                    parts = v_str.split(None, 1)
                    complexity = parts[0]; desc_tail = parts[1].strip() if len(parts) > 1 else ""
                data["theoretical"].append({"step":step_name,"complexity":complexity,"reason":desc_tail})
        elif in_meas:
            data["measured"][k_str] = v_str
        else:
            if   "reads processed"   in kl: data["reads"]          = v_str
            elif "total k-mer"       in kl: data["total_kmers"]    = v_str
            elif "k-mer size"        in kl or "kmer size" in kl: data["kmer_size"] = v_str
            elif "nodes (v)"         in kl or "graph nodes" in kl: data["nodes"]   = v_str
            elif "edges (e)"         in kl or "graph edges" in kl: data["edges"]   = v_str
            elif "method selected"   in kl: data["method"]         = v_str
            elif "dijkstra length"   in kl: data["dijk_len"]       = v_str
            elif "hierholzer length" in kl: data["hier_len"]       = v_str
            elif "final length"      in kl or "assembly length" in kl:
                data["final_len"] = v_str.replace(" bp","").strip()
            elif "gc content"        in kl: data["gc"]             = v_str.replace(" %","").strip()
            elif "n50"               in kl: data["n50"]            = v_str.replace(" bp","").strip()
            elif "min repeat length" in kl: data["min_repeat"]     = v_str
            elif "repeat regions"    in kl: data["repeat_regions"] = v_str
    return data


def parse_repeats(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    current = {}
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("=") or s.startswith("-") or s.startswith("HelixForge") \
                or s.startswith("Assembly") or s.startswith("Min") or s.startswith("Repeats") \
                or s.startswith("Top") or s.startswith("Rank"):
            continue
        if s[0].isdigit() and len(s.split()) >= 2:
            if current:
                rows.append(current)
            parts = s.split()
            current = {"rank":parts[0],"length":parts[1],"occurrences":parts[2] if len(parts)>2 else "—","positions":"","pattern":""}
            pos_start = s.find("[")
            if pos_start != -1:
                current["positions"] = s[pos_start:]
        elif s.startswith("Pattern:"):
            current["pattern"] = s.replace("Pattern:","").strip()
    if current:
        rows.append(current)
    return rows


def build_3d_graph(graph_path: Path, max_nodes: int):
    gdata = json.loads(graph_path.read_text())
    nodes = gdata["nodes"][:max_nodes]
    node_set = set(nodes)

    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    edge_weights = {}
    for edge in gdata["edges"]:
        if isinstance(edge, list):
            u, v, w = edge[0], edge[1], 1
        else:
            u = edge.get("from",""); v = edge.get("to",""); w = edge.get("weight",1)
        if u in node_set and v in node_set:
            G.add_edge(u, v)
            edge_weights[(u, v)] = w

    pos  = nx.spring_layout(G, dim=3, seed=42, k=0.55)
    degs = [G.degree(n) for n in nodes]

    max_w = max(edge_weights.values(), default=1)
    ex, ey, ez = [], [], []
    for (u, v) in edge_weights:
        if u not in pos or v not in pos:
            continue
        x0,y0,z0 = pos[u]; x1,y1,z1 = pos[v]
        ex += [x0,x1,None]; ey += [y0,y1,None]; ez += [z0,z1,None]

    edge_trace = go.Scatter3d(
        x=ex, y=ey, z=ez, mode="lines",
        line=dict(
            color=[w/max_w for (u,v),w in edge_weights.items() for _ in range(3)],
            colorscale=[[0,"rgba(20,24,30,.3)"],[0.5,"rgba(77,159,255,.5)"],[1,"rgba(184,255,87,.8)"]],
            width=1.2),
        hoverinfo="none", name="edges")

    node_trace = go.Scatter3d(
        x=[pos[n][0] for n in nodes],
        y=[pos[n][1] for n in nodes],
        z=[pos[n][2] for n in nodes],
        mode="markers",
        marker=dict(
            size=[3 + d*.75 for d in degs],
            color=degs,
            colorscale=[
                [0,   "#1c2128"],
                [0.25,"#4d9fff"],
                [0.6, "#2dd4bf"],
                [0.85,"#b8ff57"],
                [1,   "#ffffff"]],
            colorbar=dict(
                title=dict(text="Degree", font=dict(color="#8090cc", size=9)),
                thickness=7, len=.4,
                tickfont=dict(color="#8090cc", size=8)),
            opacity=.9, line=dict(width=0)),
        text=nodes,
        hovertemplate="<b>%{text}</b><br>degree: %{marker.color}<extra></extra>",
        name="nodes")

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        scene=dict(
            xaxis=dict(showgrid=False,zeroline=False,showticklabels=False,showbackground=False),
            yaxis=dict(showgrid=False,zeroline=False,showticklabels=False,showbackground=False),
            zaxis=dict(showgrid=False,zeroline=False,showticklabels=False,showbackground=False),
            bgcolor="rgba(0,0,0,0)"),
        legend=dict(x=.01, y=.99, font=dict(size=9,color="#8090cc"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0,r=0,t=0,b=0), height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="#1c2128", font_size=11, font_family="IBM Plex Mono"))
    return fig


def kpi_html(label, value, unit="", accent="var(--acid)"):
    return (f'<div class="kpi-card" style="--accent:{accent}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-unit">{unit}</div></div>')


def kmer_preview_html(k: int) -> str:
    dna    = "ATCGATCGATCGATCGATCGATCG"
    start  = 3
    end    = min(start + k, len(dna))
    left   = dna[:start]
    middle = dna[start:end]
    right  = dna[end:]
    return f"""
    <div class="kmer-preview">
      <div style="font-size:.56rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;margin-bottom:.3rem">
        k-mer preview — k={k}
      </div>
      <div class="kmer-seq" style="color:rgba(140,150,165,.4)">{left}<span class="kmer-high">{middle}</span>{right}</div>
      <div class="kmer-info">
        <div class="kmer-info-item">size: <span>{k} bp</span></div>
        <div class="kmer-info-item">node: <span>{k-1} bp</span></div>
        <div class="kmer-info-item">slide: <span>O(1)</span></div>
      </div>
    </div>"""


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-logo">⬡ Helix<span>Forge</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Input</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "FASTQ file", type=["fastq","fq","txt"],
        help="Standard 4-line FASTQ. Supports large files.",
        label_visibility="collapsed")
    if not uploaded:
        st.markdown(
            '<div style="font-family:IBM Plex Mono,monospace;font-size:.64rem;'
            'color:rgba(140,150,165,.4);margin-top:.2rem">Drop .fastq / .fq</div>',
            unsafe_allow_html=True)

    st.markdown('<div class="sb-section">k-mer Parameters</div>', unsafe_allow_html=True)
    k = st.slider("k-mer size (k)", min_value=7, max_value=63, value=21, step=2,
                  help="Odd values avoid palindromes. Larger k = more specific but needs more coverage.")
    st.markdown(kmer_preview_html(k), unsafe_allow_html=True)

    max_vis = st.slider("Max graph nodes", 50, 600, 200, 50,
                        help="Capped for performance. Full graph saved to graph_data.json.")

    st.markdown("")
    run_btn = st.button("▶  Run Assembly", type="primary", use_container_width=True)

    if uploaded:
        fsize = len(uploaded.getvalue()) / 1024
        st.markdown(
            f'<div style="font-family:IBM Plex Mono,monospace;font-size:.62rem;'
            f'color:rgba(184,255,87,.5);margin-top:.3rem;text-align:center">'
            f'📁 {uploaded.name} · {fsize:.1f} KB</div>',
            unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Algorithm Notes</div>', unsafe_allow_html=True)
    with st.expander("Why De Bruijn graphs?"):
        st.write("Instead of finding which read connects to which (NP-hard), "
                 "we chop everything into k-mers and ask: which words flow into which? "
                 "Assembly = finding a path that uses every edge once — solvable in O(E) with Hierholzer's algorithm.")
    with st.expander("Why rolling hash?"):
        st.write("Slide the window by one letter, subtract the old letter, add the new one — "
                 "the hash updates in O(1) instead of O(k). Across millions of reads, that's a massive speed-up.")
    with st.expander("Why Bloom filter?"):
        st.write("Error k-mers appear only once. A Bloom filter is a tiny 8 MB checklist — "
                 "if a k-mer shows up twice it's probably real. If only once, it's probably an error. "
                 "We keep only the 'seen twice' ones.")
    with st.expander("Why Dijkstra for assembly?"):
        st.write("When the graph is messy, we treat high-coverage edges (seen many times) as low-cost roads. "
                 "Dijkstra naturally picks the path through the most-trusted data.")
    with st.expander("Why Suffix Array?"):
        st.write("A Suffix Array sorts all possible suffixes alphabetically. "
                 "The LCP array tells us which neighbours share a long starting stretch — those are repeat regions. "
                 "O(n log²n) build, O(n) repeat scan.")


# ─────────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────────
st.markdown("""
<div class="hf-hero">
  <div class="hf-logo-wrap">
    <div class="hf-helix-icon">⬡</div>
    <div class="hf-logo">Helix<span>Forge</span></div>
  </div>
  <div class="hf-sub">
    De-Bruijn · Rolling Hash · Bloom Filter · Dijkstra · Hierholzer · Suffix Array · DP Correction
  </div>
</div>
<div class="hf-divider"></div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  ASSEMBLY RUN
# ─────────────────────────────────────────────
if run_btn:
    if uploaded is None:
        st.error("⚠ Please upload a FASTQ file first."); st.stop()
    if not ASSEMBLER.exists():
        st.error(f"Assembler binary not found at `{ASSEMBLER}`.\n"
                 "Compile with:\n```\ng++ -O2 -std=c++17 -static -o assembler assembler_standalone.cpp\n```")
        st.stop()

    tmp = Path(tempfile.mkdtemp())
    fq  = tmp / "input.fastq"
    fq.write_bytes(uploaded.getvalue())
    out = tmp / "out"; out.mkdir()

    with st.spinner("Running C++ assembly engine — 7-stage pipeline …"):
        res = subprocess.run(
            [str(ASSEMBLER), str(fq), str(k), str(out)],
            capture_output=True, text=True, timeout=600)

    if res.returncode != 0:
        st.error("Assembly engine returned an error:")
        st.code(res.stderr, language="text")
        shutil.rmtree(tmp, ignore_errors=True); st.stop()

    OUTPUT_DIR.mkdir(exist_ok=True)
    for fname in ["genome.fasta","stats.txt","graph_data.json","repeats.txt"]:
        src = out / fname
        if src.exists(): shutil.copy(src, OUTPUT_DIR / fname)

    st.session_state["assembled"] = True
    shutil.rmtree(tmp, ignore_errors=True)
    st.rerun()


# ─────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────
tab_results, tab_problem, tab_complexity = st.tabs(
    ["  ASSEMBLY RESULTS  ", "  PROBLEM STATEMENT  ", "  COMPLEXITY & ALGORITHMS  "])


# ─────────────────────────────────────────────
#  TAB 1 — RESULTS
# ─────────────────────────────────────────────
with tab_results:
    if not st.session_state.get("assembled"):
        st.markdown(
            '<div class="info-banner">Upload a <code>.fastq</code> file in the sidebar, '
            'tune the k-mer slider, then click <strong>Run Assembly</strong>.</div>',
            unsafe_allow_html=True)

        st.markdown('<div class="hf-section">7-Stage Pipeline</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="pipeline">
          <div class="pipe-step"><div class="pipe-num">01</div><div class="pipe-icon">📂</div>
            <div class="pipe-title">FASTQ</div><div class="pipe-sub">Stream · O(N)</div></div>
          <div class="pipe-step"><div class="pipe-num">02</div><div class="pipe-icon">⚡</div>
            <div class="pipe-title">Hash</div><div class="pipe-sub">Rabin-Karp · O(1)</div></div>
          <div class="pipe-step"><div class="pipe-num">03</div><div class="pipe-icon">🌸</div>
            <div class="pipe-title">Bloom</div><div class="pipe-sub">8 MB · O(N)</div></div>
          <div class="pipe-step"><div class="pipe-num">04</div><div class="pipe-icon">🧬</div>
            <div class="pipe-title">De Bruijn</div><div class="pipe-sub">O(V+E)</div></div>
          <div class="pipe-step"><div class="pipe-num">05</div><div class="pipe-icon">🎯</div>
            <div class="pipe-title">Dijkstra</div><div class="pipe-sub">O((V+E)logV)</div></div>
          <div class="pipe-step"><div class="pipe-num">06</div><div class="pipe-icon">🛤</div>
            <div class="pipe-title">Hierholzer</div><div class="pipe-sub">Euler · O(E)</div></div>
          <div class="pipe-step"><div class="pipe-num">07</div><div class="pipe-icon">🔬</div>
            <div class="pipe-title">SA + LCP</div><div class="pipe-sub">O(n log²n)</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── Load outputs ──
    fasta_p   = OUTPUT_DIR / "genome.fasta"
    stats_p   = OUTPUT_DIR / "stats.txt"
    graph_p   = OUTPUT_DIR / "graph_data.json"
    repeats_p = OUTPUT_DIR / "repeats.txt"

    if not stats_p.exists():
        st.error("Output files not found. Re-run the assembly."); st.stop()

    stats   = parse_stats(stats_p)
    repeats = parse_repeats(repeats_p)
    seq_txt = fasta_p.read_text() if fasta_p.exists() else ""
    sequence = "".join(l for l in seq_txt.splitlines() if not l.startswith(">"))

    # ── KPI grid ──
    st.markdown('<div class="hf-section">Assembly Metrics</div>', unsafe_allow_html=True)
    kpis = [
        kpi_html("Reads",      stats["reads"],       "reads",      "var(--acid)"),
        kpi_html("k-mers",     stats["total_kmers"], "k-mers",     "var(--blue)"),
        kpi_html("Nodes (V)",  stats["nodes"],       "(k-1)-mers", "var(--teal)"),
        kpi_html("Edges (E)",  stats["edges"],       "k-mers",     "var(--rose)"),
        kpi_html("Assembly",   stats["final_len"],   "bp",         "var(--amber)"),
        kpi_html("GC Content", stats["gc"],          "%",          "var(--acid)"),
        kpi_html("N50",        stats["n50"],         "bp",         "var(--blue)"),
    ]
    st.markdown(f'<div class="kpi-grid">{"".join(kpis)}</div>', unsafe_allow_html=True)

    # ── Genome Verification ──
    st.markdown('<div class="hf-section">Genome Verification</div>', unsafe_allow_html=True)

    def verify_gc(gc_str):
        try:
            v = float(gc_str)
        except:
            return None, 0, "#555", "NO DATA", "Run assembly first"
        if 40 <= v <= 65:
            color, status = "#b8ff57", "✓ NORMAL"
        elif 30 <= v < 40 or 65 < v <= 75:
            color, status = "#f59e0b", "⚠ BORDERLINE"
        else:
            color, status = "#fb7185", "✗ UNUSUAL"
        note = ("Typical range for plant/fungal barcodes is 40–65 %. "
                "Values outside this can mean contamination or very GC-rich organisms.")
        return v, min(v, 100), color, status, note

    def verify_n50(n50_str, asm_len_str):
        try:
            n50 = int(n50_str)
        except:
            return None, None, "NO DATA", "#555", ""
        try:
            alen = int(asm_len_str)
        except:
            alen = n50
        ratio = n50 / alen if alen > 0 else 0
        if alen <= 100:
            color   = "#fb7185"
            quality = "✗ TRIVIAL — assembly = 1 k-mer, lower k or increase coverage"
        elif ratio >= 0.5 and alen >= 200:
            color, quality = "#b8ff57", "✓ GOOD"
        elif ratio >= 0.2:
            color, quality = "#f59e0b", "⚠ FRAGMENTED"
        else:
            color, quality = "#fb7185", "✗ HIGHLY FRAGMENTED"
        note = ("N50 = the length L where contigs ≥ L cover at least half the assembly. "
                "If N50 ≈ assembly length — good. "
                "If both are tiny (≤ k bp), no path was found — lower k.")
        return n50, alen, quality, color, note

    gc_val, gc_bar, gc_color, gc_status, gc_note = verify_gc(stats["gc"])
    n50_v, alen_v, n50_quality, n50_color, n50_note = verify_n50(stats["n50"], stats["final_len"])

    blast_seq = sequence[:500] if sequence else ""
    import urllib.parse
    blast_url = ("https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi?"
                 "PAGE_TYPE=BlastSearch&PROGRAM=blastn&DATABASE=nt"
                 f"&QUERY={urllib.parse.quote(blast_seq)}&CMD=Put") if blast_seq else ""

    gc_display  = f"{gc_val:.2f} %" if gc_val is not None else "—"
    n50_display = f"{n50_v} bp"     if n50_v  is not None else "—"

    try:
        kmer_size_int = int(stats["kmer_size"])
    except:
        kmer_size_int = 0
    asm_len_int = alen_v or 0
    gc_ok  = gc_val is not None and 30 <= gc_val <= 75
    asm_ok = asm_len_int >= 200

    if asm_ok and gc_ok:
        verdict_color = "#b8ff57"
        verdict_icon  = "✅"
        verdict_text  = "ASSEMBLY LOOKS VALID — GC content normal, length meaningful. BLAST to confirm organism match."
    elif not asm_ok and asm_len_int <= kmer_size_int:
        verdict_color = "#fb7185"
        verdict_icon  = "❌"
        verdict_text  = (f"TRIVIAL ASSEMBLY — output is just one {kmer_size_int}-bp k-mer. "
                         f"Lower k to 15–19 in the sidebar and re-run.")
    elif not asm_ok:
        verdict_color = "#f59e0b"
        verdict_icon  = "⚠️"
        verdict_text  = "SHORT ASSEMBLY — may be fragmented. Try lowering k or using a file with more reads."
    else:
        verdict_color = "#f59e0b"
        verdict_icon  = "⚠️"
        verdict_text  = "UNUSUAL GC CONTENT — check for adapter contamination or verify organism GC range."

    st.markdown(
        f'<div style="background:rgba(255,255,255,.02);border:1px solid {verdict_color}30;'
        f'border-left:3px solid {verdict_color};border-radius:0 6px 6px 0;padding:.7rem 1rem;'
        f'margin-bottom:.7rem;font-family:IBM Plex Mono,monospace;font-size:.76rem;'
        f'color:{verdict_color};line-height:1.5">'
        f'{verdict_icon} <strong>VERDICT</strong> — {verdict_text}</div>',
        unsafe_allow_html=True)

    st.markdown(f"""
    <div class="verify-card">
      <div class="verify-title">Quality Checks</div>

      <div class="verify-row">
        <div class="verify-label">GC Content</div>
        <div class="verify-bar-wrap">
          <div class="verify-bar" style="width:{gc_bar}%;background:{gc_color}"></div>
        </div>
        <div class="verify-val">{gc_display}</div>
        <div class="verify-status" style="color:{gc_color}">{gc_status}</div>
      </div>
      <div style="font-family:IBM Plex Mono,monospace;font-size:.62rem;color:var(--muted);
                  padding:.12rem 0 .5rem 130px;line-height:1.5">{gc_note}</div>

      <div class="verify-row">
        <div class="verify-label">N50 Score</div>
        <div class="verify-bar-wrap">
          <div class="verify-bar" style="width:{min((n50_v or 0)/(alen_v or 1)*100,100):.1f}%;
               background:{n50_color}"></div>
        </div>
        <div class="verify-val">{n50_display}</div>
        <div class="verify-status" style="color:{n50_color}">{n50_quality}</div>
      </div>
      <div style="font-family:IBM Plex Mono,monospace;font-size:.62rem;color:var(--muted);
                  padding:.12rem 0 .5rem 130px;line-height:1.5">{n50_note}</div>

      <div class="verify-row">
        <div class="verify-label">Assembly Length</div>
        <div class="verify-bar-wrap" style="background:transparent"></div>
        <div class="verify-val">{stats["final_len"]} bp</div>
        <div class="verify-status" style="color:{'#b8ff57' if (alen_v or 0) >= 200 else '#fb7185'}">
          {'✓ Meaningful' if (alen_v or 0) >= 200
           else f'✗ = 1 k-mer (k={stats["kmer_size"]}) — lower k'}
        </div>
      </div>
      <div style="font-family:IBM Plex Mono,monospace;font-size:.62rem;color:var(--muted);
                  padding:.12rem 0 .5rem 130px;line-height:1.5">
        Expected: ITS2 ≈ 200–500 bp · rbcL ≈ 550 bp · 18S ≈ 1800 bp · MATK ≈ 900 bp · psbA3 ≈ 450 bp.<br>
        If length = k, no multi-edge path found. <strong style="color:#f59e0b">Lower k in the sidebar.</strong>
      </div>
    </div>
    """, unsafe_allow_html=True)

    vcol1, vcol2 = st.columns([1, 1])
    with vcol1:
        if blast_url and blast_seq:
            st.markdown(
                f'<a class="blast-btn" href="{blast_url}" target="_blank">'
                f'↗ BLAST on NCBI</a>'
                f'<div style="font-family:IBM Plex Mono,monospace;font-size:.6rem;'
                f'color:var(--muted);margin-top:.3rem">'
                f'BLASTn with your assembly — shows closest organism match.</div>',
                unsafe_allow_html=True)
    with vcol2:
        with st.expander("How to improve assembly quality"):
            st.markdown("""
**Assembly too short (< 200 bp):**
- Lower k (try 15–19 for short-read data)
- Check FASTQ has enough reads (ideally 1000+)
- Bloom filter needs each k-mer seen ≥2× — higher coverage helps

**Unusual GC content (< 30% or > 75%):**
- May indicate adapter contamination
- Filter reads with quality < Q10 before assembling

**Verifying biological accuracy:**
1. BLAST → check top hit matches expected organism
2. Compare assembly length to known gene lengths
3. GC should match known values for your species
4. N50 ≈ assembly length → one clean contig ✓
            """)

    st.markdown('<div class="hf-divider"></div>', unsafe_allow_html=True)

    # ── Method badge ──
    method_color = "var(--acid)" if "Hierholzer" in stats["method"] else "var(--blue)"
    st.markdown(
        f'<div class="method-badge">'
        f'<span class="method-label">Method selected</span>'
        f'<span class="method-value" style="color:{method_color}">⬡ {stats["method"]}</span>'
        f'</div>', unsafe_allow_html=True)

    if stats["dijk_len"] != "—" or stats["hier_len"] != "—":
        st.markdown(
            f'<div class="cmp-row">'
            f'<div class="cmp-box"><div class="cmp-box-label">Dijkstra (coverage-weighted)</div>'
            f'<div class="cmp-box-value" style="color:var(--blue)">{stats["dijk_len"]}</div></div>'
            f'<div class="cmp-box"><div class="cmp-box-label">Hierholzer (Eulerian path)</div>'
            f'<div class="cmp-box-value" style="color:var(--acid)">{stats["hier_len"]}</div></div>'
            f'</div>', unsafe_allow_html=True)

    st.markdown('<div class="hf-divider"></div>', unsafe_allow_html=True)

    # ── Main columns ──
    col_left, col_right = st.columns([1, 1.15], gap="large")

    with col_left:
        st.markdown('<div class="hf-section">Assembled Sequence</div>', unsafe_allow_html=True)
        preview = sequence[:3600] + ("…" if len(sequence) > 3600 else "")
        st.markdown(f"""
        <div class="seq-terminal">
          <div class="seq-bar">
            <div class="seq-dot" style="background:#ff5f57"></div>
            <div class="seq-dot" style="background:#febc2e"></div>
            <div class="seq-dot" style="background:#28c840"></div>
            <span class="seq-title">genome.fasta — {len(sequence):,} bp</span>
          </div>
          <div class="seq-body">{preview}</div>
        </div>""", unsafe_allow_html=True)

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("⬇ genome.fasta", seq_txt, "genome.fasta","text/plain", use_container_width=True)
        with dl2:
            st.download_button("⬇ stats.txt", stats_p.read_text(), "stats.txt","text/plain", use_container_width=True)

        # Timing chart
        st.markdown('<div class="hf-section">Execution Timing</div>', unsafe_allow_html=True)
        m = stats.get("measured", {})

        def _ms(m, *keys):
            for key in keys:
                if key in m:
                    try: return float(m[key].replace("ms","").strip())
                    except: pass
            return 0.0

        timing_stages = [
            ("Hashing",     _ms(m, "Hashing", "Hashing Time")),
            ("Graph Build", _ms(m, "Graph Build", "Graph Build Time")),
            ("Dijkstra",    _ms(m, "Dijkstra", "Dijkstra Time")),
            ("Hierholzer",  _ms(m, "Hierholzer", "Traversal Time", "Hierholzer Time", "Traversal")),
            ("DP Correct",  _ms(m, "DP Correction", "DP Time", "DP Correct")),
            ("SA + LCP",    _ms(m, "Suffix Array+LCP", "SA Time", "SA+LCP Time", "Suffix Array")),
        ]
        t_labels = [s[0] for s in timing_stages]
        t_vals   = [s[1] for s in timing_stages]
        colors_bar = ["#b8ff57","#4d9fff","#2dd4bf","#f59e0b","#fb7185","#a78bfa"]

        fig_bar = go.Figure(go.Bar(
            x=t_labels, y=t_vals,
            marker=dict(color=colors_bar, line=dict(width=0), opacity=.85),
            text=[f"{v:.3f}" for v in t_vals], textposition="outside",
            textfont=dict(family="IBM Plex Mono", size=9, color="#8090cc")))
        fig_bar.update_layout(
            yaxis=dict(title="ms", color="#8090cc",
                       gridcolor="rgba(255,255,255,.04)",
                       tickfont=dict(family="IBM Plex Mono",size=8)),
            xaxis=dict(color="#8090cc", tickfont=dict(family="IBM Plex Mono",size=8)),
            height=235, margin=dict(l=10,r=10,t=20,b=5),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(22,26,31,.6)")
        st.plotly_chart(fig_bar, use_container_width=True)

        total_t = m.get("Total", m.get("Total Time", "—"))
        st.markdown(
            f'<div class="overall-badge">'
            f'<span class="overall-label">Total wall time</span>'
            f'<span class="overall-value">{total_t}</span></div>',
            unsafe_allow_html=True)

        # Repeat analysis
        st.markdown('<div class="hf-section">Repeat Analysis (SA + LCP)</div>', unsafe_allow_html=True)
        n_rep = stats["repeat_regions"]
        if n_rep == "0" or n_rep == "—":
            st.markdown(
                f'<div class="repeat-card">'
                f'<div class="repeat-title">Repeat Regions</div>'
                f'<div class="repeat-zero">None found at threshold {stats["min_repeat"]}. '
                f'Assembly appears non-repetitive.</div></div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="repeat-card">'
                f'<div class="repeat-title">{n_rep} Repeat Region(s) Detected</div></div>',
                unsafe_allow_html=True)
            if repeats:
                df_rep = pd.DataFrame(repeats)[["rank","length","occurrences","positions","pattern"]]
                df_rep.columns = ["Rank","Length (bp)","Occurrences","Positions","Pattern (preview)"]
                st.dataframe(df_rep, use_container_width=True, hide_index=True)

        if repeats_p.exists():
            st.download_button("⬇ repeats.txt", repeats_p.read_text(), "repeats.txt","text/plain", use_container_width=True)

        with st.expander("Raw stats.txt"):
            st.code(stats_p.read_text(), language="text")

    with col_right:
        st.markdown('<div class="hf-section">3D De Bruijn Graph</div>', unsafe_allow_html=True)
        with st.spinner("Rendering graph …"):
            fig3d = build_3d_graph(graph_p, max_vis)
        st.plotly_chart(fig3d, use_container_width=True)

        gj = json.loads(graph_p.read_text())
        g_kpis = [
            kpi_html("Total Nodes", str(gj.get("total_nodes","—")), "(k-1)-mers", "var(--acid)"),
            kpi_html("Total Edges", str(gj.get("total_edges","—")), "overlaps",   "var(--blue)"),
        ]
        st.markdown(f'<div class="kpi-grid">{"".join(g_kpis)}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-family:IBM Plex Mono,monospace;font-size:.6rem;'
            'color:rgba(140,150,165,.3);text-align:center;margin-top:.35rem">'
            'node = (k-1)-mer · edge = k-mer overlap · colour = degree · drag to rotate · '
            'edge brightness = coverage weight</div>',
            unsafe_allow_html=True)

        st.download_button("⬇ graph_data.json", graph_p.read_text(),
                           "graph_data.json","application/json", use_container_width=True)

        st.markdown('<div class="hf-section">Complexity Summary</div>', unsafe_allow_html=True)
        theo = stats.get("theoretical", [])
        if theo:
            df_th = pd.DataFrame(theo)
            df_th.columns = ["Algorithm","Complexity","Description"]
            st.dataframe(df_th, use_container_width=True, hide_index=True, height=295)
            st.markdown(
                f'<div class="overall-badge">'
                f'<span class="overall-label">Overall</span>'
                f'<span class="overall-value">{stats["overall"]}</span></div>',
                unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  TAB 2 — PROBLEM STATEMENT  (logic unchanged)
# ─────────────────────────────────────────────
with tab_problem:
    st.markdown('<div class="hf-section">The Genome Assembly Problem</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="problem-card">
      <div class="problem-title">What Is Genome Assembly?</div>
      <p style="font-family:IBM Plex Sans,sans-serif;font-size:.85rem;color:var(--text);line-height:1.75;margin:0 0 1rem">
        A DNA sequencing machine can't read your entire genome in one shot — it's like trying to read
        a book by only ever seeing random 200-letter chunks of it, over and over again.
        What comes out are millions of short DNA snippets called
        <strong style="color:var(--acid)">reads</strong> (each ~75–300 letters long).
        <strong>Genome assembly</strong> is the job of stitching all those tiny overlapping pieces
        back into the full original sequence — with some pieces containing typos from the machine,
        and huge repeated sections that look identical no matter where you are in the genome.
        HelixForge solves this with a 7-stage algorithmic pipeline.
      </p>
      <div class="problem-grid">
        <div class="prob-item">
          <div class="prob-item-title" style="color:var(--acid)">Why Is It Hard?</div>
          <div class="prob-item-text">
            • Each read is only 75–300 letters, but a genome can be <em>billions</em> long<br>
            • The sequencing machine makes ~1% mistakes — so the data has typos<br>
            • Some DNA sections repeat identically 100s of times — hard to place correctly<br>
            • The machine reads both strands of DNA at once, so you get mirrored copies<br>
            • A human genome produces ~1 TB of raw reads to process
          </div>
        </div>
        <div class="prob-item">
          <div class="prob-item-title" style="color:var(--blue)">How HelixForge Solves It</div>
          <div class="prob-item-text">
            We chop every read into tiny fixed-size chunks called <strong>k-mers</strong>
            (e.g. if k=21, each chunk is 21 letters). Then we build a
            <strong>De Bruijn graph</strong> — a map where each chunk connects to
            the next one that overlaps it. The genome sequence is hiding inside this graph
            as a path that visits every connection exactly once.
            We find that path using <strong>Hierholzer's algorithm</strong> in O(E) time.
          </div>
        </div>
        <div class="prob-item">
          <div class="prob-item-title" style="color:var(--rose)">Why Not Just Compare Everything?</div>
          <div class="prob-item-text">
            The obvious approach — compare every read to every other read to find overlaps —
            means O(N²) comparisons. With 5 million reads, that's
            <strong>25 trillion comparisons</strong>. Way too slow.
            Our approach converts the problem into a graph traversal, bringing it down to
            <strong>O(N)</strong> to build the graph and <strong>O(E)</strong> to find the answer.
            That's the difference between hours and milliseconds.
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hf-section">Algorithm Design Decisions</div>', unsafe_allow_html=True)

    decisions = [
        ("Rolling Hash — k-mer extraction from every read", "var(--acid)",
         "<strong>The problem it solves:</strong> For every position in a DNA read, we need a fingerprint "
         "of the next k letters. Recomputing from scratch = k operations × millions of positions = slow.<br><br>"
         "<strong>What rolling hash does:</strong> Keeps the current fingerprint in memory and "
         "<em>slides</em> it one letter at a time — drop the old leftmost letter, add the new rightmost one. "
         "Each slide is 2 math operations: O(1) per step instead of O(k).<br><br>"
         "<strong>Where it runs:</strong> Stage 2 — every single read, every single position.",
         "O(N·k) → O(N)"),

        ("Bloom Filter — filtering out sequencing errors", "var(--blue)",
         "<strong>The problem it solves:</strong> Sequencing machines make typos (~1 per 100 letters). "
         "Those typos create k-mers that appear only once — fake, not real genome. "
         "Keeping all of them fills the graph with junk.<br><br>"
         "<strong>What Bloom filter does:</strong> A tiny 8 MB checklist. "
         "First pass marks a k-mer as 'seen once', second pass upgrades to 'seen twice'. "
         "Only 'seen twice' k-mers are trusted as real genome sequence.<br><br>"
         "<strong>Where it runs:</strong> Stage 3 — before building the graph.",
         "8 MB fixed vs gigabytes of RAM"),

        ("Canonical K-mers — De Bruijn graph construction", "var(--teal)",
         "<strong>The problem it solves:</strong> DNA is two-sided. A read <code>ATCG</code> and its "
         "mirror image <code>CGAT</code> are the same piece of genome — just read from opposite ends. "
         "Without this, we'd build two conflicting nodes for the same location.<br><br>"
         "<strong>What canonical k-mers do:</strong> For every k-mer, compute its reverse complement "
         "and keep whichever comes first alphabetically. Both strands collapse to one node. "
         "Graph size halved, assembly biologically accurate.<br><br>"
         "<strong>Where it runs:</strong> Every time a k-mer is added to the graph (Stage 4).",
         "Graph size ÷ 2"),

        ("Dijkstra — best path when the graph is messy", "var(--amber)",
         "<strong>The problem it solves:</strong> Sometimes the De Bruijn graph is fragmented — "
         "no single clean Euler path. We need a backup that picks the most trustworthy route.<br><br>"
         "<strong>What Dijkstra does here:</strong> Assign each edge a weight based on how often "
         "that k-mer was seen in the reads. High coverage = low cost. "
         "Dijkstra naturally follows the path with the most read support.<br><br>"
         "<strong>Where it runs:</strong> Stage 5 — parallel with Hierholzer. "
         "Longer result wins.",
         "O((V+E) log V)"),

        ("Suffix Array + LCP — repeat region detection", "var(--rose)",
         "<strong>The problem it solves:</strong> Some DNA sections appear many times — "
         "repeats confuse assemblers and are medically important (tandem repeat diseases).<br><br>"
         "<strong>What Suffix Array does:</strong> Sort every possible suffix of the assembled sequence "
         "alphabetically. The LCP array records how many letters each neighbour shares — "
         "a long match = a repeat region.<br><br>"
         "<strong>Where it runs:</strong> Stage 7 — after assembly, purely for analysis.",
         "O(n log²n) build + O(n) repeat scan"),
    ]

    for title, color, desc, complexity in decisions:
        with st.expander(f"◈  {title}"):
            st.markdown(
                f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:.82rem;'
                f'color:var(--text);line-height:1.75;border-left:2px solid {color};'
                f'padding-left:.9rem">{desc}</div>'
                f'<div style="margin-top:.6rem;font-family:IBM Plex Mono,monospace;font-size:.65rem;'
                f'color:{color};background:var(--surface2);border-radius:4px;padding:.3rem .7rem;'
                f'display:inline-block">complexity: {complexity}</div>',
                unsafe_allow_html=True)

    st.markdown('<div class="hf-section">Real-World Impact</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="problem-card" style="border-color:rgba(184,255,87,.15)">
      <div class="problem-title" style="color:var(--acid)">The Same Algorithms Power Real Science</div>
      <div class="problem-grid">
        <div class="prob-item">
          <div class="prob-item-title" style="color:var(--acid)">Fighting Diseases</div>
          <div class="prob-item-text">
            Doctors use genome assembly to find mutations that cause cancer or rare diseases.
            Tools like GATK and SPAdes — used in hospitals worldwide — are built on exactly the
            same De Bruijn graph idea that HelixForge implements.
          </div>
        </div>
        <div class="prob-item">
          <div class="prob-item-title" style="color:var(--blue)">COVID-19 Tracking</div>
          <div class="prob-item-text">
            Every time a new COVID variant was detected, labs assembled the viral genome
            from scratch in hours. The rolling hash + De Bruijn pipeline used here is the same
            approach those labs ran thousands of times per day during the pandemic.
          </div>
        </div>
        <div class="prob-item">
          <div class="prob-item-title" style="color:var(--teal)">Mapping All Life</div>
          <div class="prob-item-text">
            The Earth BioGenome Project wants to sequence every species on Earth (~1.5 million).
            Without fast assembly algorithms like ours, that would take centuries.
            Efficient k-mer hashing and graph traversal make it possible in years.
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  TAB 3 — COMPLEXITY & ALGORITHMS  (logic unchanged)
# ─────────────────────────────────────────────
with tab_complexity:
    st.markdown('<div class="hf-section">Full Complexity Table</div>', unsafe_allow_html=True)

    rows = [
        ("📂 FASTQ Reader",        "O(N)",                   "Read the input file once, line by line. N = total letters in all reads.",                              "Used here: loading raw sequencing data"),
        ("🔄 Reverse Complement",  "O(k)",                   "Flip a k-mer and swap A↔T, C↔G. Needed because both DNA strands get sequenced.",                      "Used here: making canonical k-mers"),
        ("⚡ Rolling Hash (setup)","O(k)",                   "Compute the first hash of a k-letter window — done once per read at the start.",                       "Used here: k-mer fingerprinting"),
        ("⚡ Rolling Hash (slide)","O(1)",                   "Update the hash by dropping one letter and adding another. Much faster than recomputing from scratch.", "Used here: sliding across every read position"),
        ("🌸 Bloom Filter insert", "O(1)",                   "Flip a few bits in an 8 MB checklist. Constant time regardless of how many k-mers we've seen.",        "Used here: tracking which k-mers appeared twice"),
        ("🌸 Bloom Filter query",  "O(1)",                   "Check if those bits are set. If any bit is 0, the k-mer is definitely not there.",                     "Used here: filtering error k-mers before graph build"),
        ("🧬 Graph add_edge",      "O(1) avg",               "Insert a k-mer as an edge into a hash map — average O(1), very fast in practice.",                     "Used here: building the De Bruijn graph"),
        ("🧬 Graph Construction",  "O(V + E)",               "Build the full graph — V unique nodes (k-1-mers) and E unique edges (k-mers).",                        "Used here: Stage 4, after Bloom filtering"),
        ("🎯 Dijkstra SSSP",       "O((V+E) log V)",         "Min-heap shortest path, but 'shortest' = most-covered. Picks the most trusted assembly path.",         "Used here: Stage 5, backup assembly when no Euler path"),
        ("🛤 Hierholzer Euler",    "O(E)",                   "Walk every edge exactly once using a stack. If the graph allows it, gives the full genome path.",       "Used here: Stage 6, primary assembly strategy"),
        ("🔀 Greedy Fallback",     "O(E)",                   "If neither method gives a complete path, greedily follow the highest-frequency edge at each step.",     "Used here: last resort when graph is fragmented"),
        ("🩹 DP Error Correction", "O(N)",                   "Scan the assembled sequence and fix unlikely letters using a sliding window majority vote.",            "Used here: cleaning up the final sequence"),
        ("🔬 Suffix Array build",  "O(n log² n)",            "Sort all suffixes of the assembly alphabetically. Doubling trick — only needs log(n) rounds.",          "Used here: Stage 7, repeat region detection"),
        ("🔬 LCP Array (Kasai)",   "O(n)",                   "Find how many letters adjacent sorted suffixes share. Clever invariant keeps it O(n).",                 "Used here: tells us where repeats start and end"),
        ("🔍 Repeat Finding",      "O(n)",                   "Scan the LCP array — neighbours with a long common prefix are repeat regions.",                         "Used here: reporting tandem repeats in the output"),
        ("📊 GC Content",          "O(n)",                   "Count G and C letters in the assembly, divide by total length. One simple pass.",                       "Used here: genome quality metric"),
        ("📊 N50 Metric",          "O(c log c)",             "Sort contig lengths, sum from longest until you hit 50% of total — that length is N50.",               "Used here: standard assembly quality score"),
        ("💾 JSON Graph Writer",   "O(V + E)",               "Write graph nodes and edges to a file for the 3D visualiser. Capped at 500 nodes for browser speed.",  "Used here: feeding the interactive graph display"),
        ("🏁 Overall Pipeline",    "O(N + (V+E)logV + n log²n)", "Dominated by Dijkstra on graph-heavy data, or by the Suffix Array on long assemblies.",           "All 7 stages combined"),
    ]

    df_full = pd.DataFrame(rows, columns=["Step","Complexity","Plain English — what it does & why","Where it's used"])
    st.dataframe(df_full, use_container_width=True, hide_index=True, height=600)

    st.markdown('<div class="hf-section">Memory Usage (Space Complexity)</div>', unsafe_allow_html=True)
    space_rows = [
        ("Bloom Filters (×2)",  "16 MB fixed",      "Two tiny 8 MB checklists — same size no matter how many reads you process."),
        ("Rolling Hash",        "O(1)",              "Just two numbers in memory: the current hash value and a precomputed power."),
        ("De Bruijn Graph",     "O(V + E)",          "One entry per unique k-mer (edge) and per unique (k-1)-mer (node). Grows with the genome, not read count."),
        ("Dijkstra structures", "O(V)",              "Arrays for distances and a min-heap — one slot per node."),
        ("Suffix Array",        "O(n)",              "Three arrays of length n (the assembly length)."),
        ("LCP Array",           "O(n)",              "One number per suffix — exactly n integers for an assembly of length n."),
        ("Overall",             "O(N + V + E + n)", "The Bloom filter constant is the hero here — without it, storing all k-mers would need gigabytes."),
    ]
    df_space = pd.DataFrame(space_rows, columns=["What","Memory","Why it's this size"])
    st.dataframe(df_space, use_container_width=True, hide_index=True)

    st.markdown('<div class="hf-section">Algorithm & Data Structure Topics Used</div>', unsafe_allow_html=True)
    aps_rows = [
        ("Graph Theory",         "We model the genome as a De Bruijn graph — directed edges are k-mers, nodes are (k-1)-mers. Assembly = path through graph."),
        ("Eulerian Paths",       "Hierholzer's algorithm finds a path that uses every edge exactly once. This is exactly what genome assembly needs. O(E) time."),
        ("Shortest Path (SSSP)", "Dijkstra finds the path through edges with highest read coverage — our backup assembly strategy when no Euler path exists."),
        ("Priority Queue",       "Min-heap powers Dijkstra — always processes the lowest-cost node next. O(log V) per operation."),
        ("Hashing",              "Rabin-Karp rolling hash gives O(1) k-mer fingerprinting per position instead of O(k). Used on every single read."),
        ("Probabilistic DS",     "Bloom Filter — a space-efficient way to check 'have I seen this k-mer twice?' Uses only 8 MB regardless of data size."),
        ("Divide & Conquer",     "Suffix Array built by repeatedly halving the problem — rank by 1 letter, then 2, then 4... Each round doubles what we know."),
        ("String Algorithms",    "Suffix Array sorts all suffixes; LCP Array finds shared prefixes; Kasai's algorithm builds LCP in O(n) by reusing prior work."),
        ("Dynamic Programming",  "Error correction scans the assembly and fixes each letter based on surrounding window — O(1) per step."),
        ("Amortised Analysis",   "Kasai's LCP algorithm: a counter can only decrease n times total, so despite variable individual steps, total is always O(n)."),
        ("Greedy Algorithms",    "When both Dijkstra and Hierholzer fail, we greedily pick the most-seen edge next. Simple but effective."),
        ("Sliding Window",       "Rolling hash slides a fixed-size window across the read — add one letter on right, drop one on left."),
        ("Two-Pointer",          "Kasai's LCP extension works like two pointers — total movements stay within n, keeping the whole thing O(n)."),
        ("Space-Time Tradeoff",  "Bloom filter accepts ~0.02% false positive rate in exchange for 8 MB instead of gigabytes. Speed and memory win over perfect accuracy."),
        ("Canonical Forms",      "For every k-mer, keep min(kmer, reverse_complement) as the 'official' version. Groups both DNA strands under one name."),
        ("Complexity Analysis",  "Every module measured both theoretically and in practice. Both recorded in stats.txt for comparison."),
    ]
    df_aps = pd.DataFrame(aps_rows, columns=["Topic","How HelixForge uses it"])
    st.dataframe(df_aps, use_container_width=True, hide_index=True, height=530)
