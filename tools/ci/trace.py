#!/usr/bin/env python3
import argparse, os, json, sys, re
from pathlib import Path
try:
    import yaml
except Exception:
    print("PyYAML が必要です: pip install pyyaml", file=sys.stderr); sys.exit(1)

try:
    import networkx as nx
except Exception:
    print("networkx が必要です: pip install networkx", file=sys.stderr); sys.exit(1)

REQ_ID = "id"

def read_fm(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith('---'):
        return None
    end = text.find('\n---', 3)
    if end == -1:
        return None
    fm_text = text[3:end]
    try:
        return yaml.safe_load(fm_text) or {}
    except Exception:
        return None

def ensure_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def build_graph(docs_root: str, rules_path: str):
    docs = Path(docs_root)
    md_files = [p for p in docs.rglob("*.md") if p.is_file()]
    # Collect nodes
    id_to_path = {}
    path_to_id = {}
    fm_cache = {}
    for p in md_files:
        fm = read_fm(p)
        fm_cache[str(p)] = fm
        if not isinstance(fm, dict): 
            continue
        _id = fm.get(REQ_ID)
        if isinstance(_id, str) and _id.strip():
            id_to_path[_id] = str(p)
            path_to_id[str(p)] = _id

    # Load rules
    try:
        rules = yaml.safe_load(open(rules_path, "r", encoding="utf-8")) or {}
    except FileNotFoundError:
        rules = {}
    rels_node = rules.get("relations", None)
    if isinstance(rels_node, dict) and "relations" in rels_node:
        rels = rels_node.get("relations", [])
    elif isinstance(rels_node, list):
        rels = rels_node
    else:
        rels = [
        {"key":"depends_on","type":"depends_on"},
        {"key":"refines","type":"refines"},
        {"key":"satisfies","type":"satisfies"},
        {"key":"integrates_with","type":"integrates_with"},
        {"key":"constrains","type":"constrains"},
        {"key":"supersedes","type":"supersedes"},
        {"key":"canonical_parent","type":"parent","scalar": True},
    ]

    G = nx.DiGraph()
    for _id, p in id_to_path.items():
        G.add_node(_id, path=p)

    unknown_refs = []
    edges = []
    # Build edges
    for p_str, fm in fm_cache.items():
        if not isinstance(fm, dict): 
            continue
        src = fm.get(REQ_ID)
        if not src:
            continue
        for r in rels:
            key = r.get("key"); rtype = r.get("type", key)
            vals = ensure_list(fm.get(key))
            for v in vals:
                if not v: 
                    continue
                dst = str(v)
                edges.append((src, dst, rtype))
                if dst not in id_to_path:
                    unknown_refs.append({"src": src, "ref": dst, "type": rtype, "path": p_str})
                G.add_edge(src, dst, type=rtype)

    # Metrics
    # cycles: count SCCs (>1) + self-loops
    sccs_all = list(nx.strongly_connected_components(G))
    sccs = [list(c) for c in sccs_all if len(c) > 1]
    self_loops = sum(1 for n in G.nodes if G.has_edge(n, n))
    cycles = len(sccs) + self_loops

    orphans = [n for n in G.nodes if G.in_degree(n) == 0 and G.out_degree(n) == 0]

    summary = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "cycles": cycles,
        "scc_groups": len(sccs),
        "self_loops": self_loops,
        "orphans": len(orphans),
        "unknown_refs": len(unknown_refs),
    }
    return G, edges, orphans, sccs, unknown_refs, summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--rules", default="tools/docops_cli/config/trace_rules.yml")
    ap.add_argument("--docs-root", default="docs")
    ap.add_argument("--out", default="artifacts/trace")
    ap.add_argument("--format", default="json")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    G, edges, orphans, sccs, unknown_refs, summary = build_graph(args.docs_root, args.rules)

    # Write JSON (primary artifact; approval_gate.py expects top-level 'cycles')
    data = {
        "cycles": int(summary["cycles"]),
        "summary": summary,
        "nodes": [{"id": n, "path": G.nodes[n].get("path","")} for n in G.nodes],
        "edges": [{"src": s, "dst": t, "type": G.edges[s,t].get("type","")} for s,t in G.edges],
        "orphans": orphans,
        "sccs": sccs,
        "unknown_refs": unknown_refs,
    }
    (Path(args.out)/"graph.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    if "md" in args.format:
        lines = ["# Trace Graph", ""]
        lines += [f"- nodes: {summary['nodes']}", f"- edges: {summary['edges']}", f"- cycles: {summary['cycles']}", f"- unknown_refs: {summary['unknown_refs']}", ""]
        if unknown_refs:
            lines.append("## Unknown References")
            for u in unknown_refs[:100]:
                lines.append(f"- {u['src']} -> {u['ref']} ({u['type']}) @ {u['path']}")
        (Path(args.out)/"graph.md").write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
