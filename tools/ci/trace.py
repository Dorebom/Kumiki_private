#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trace builder & helper utilities for Kumiki DocOps (tools/ci).
- build   : build graph.json/md from FrontMatter relations
- suggest : propose fixes for unknown_refs (alias/prefix-heuristics)
"""
import argparse, os, json, sys, re, fnmatch
from pathlib import Path

try:
    import yaml
except Exception:
    print("PyYAML が必要です: pip install pyyaml", file=sys.stderr); sys.exit(1)

try:
    import networkx as nx
except Exception:
    print("networkx が必要です: pip install networkx", file=sys.stderr); sys.exit(1)

DEFAULT_RULES_PRI = "tools/ci/config/trace_rules.yml"
DEFAULT_RULES_FALLBACK = "tools/docops_cli/config/trace_rules.yml"  # 後方互換用
DEFAULT_DOCS_ROOT = "docs"
REQ_ID_DEFAULT = "id"

def read_fm(path: Path):
    """YAML FrontMatter を読み取る。壊れている場合は None。"""
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

def _compile_globs(globs):
    return [g for g in (globs or []) if isinstance(g, str) and g.strip()]

def _match_any(path_str, patterns):
    return any(fnmatch.fnmatch(path_str, pat) for pat in patterns)

def load_rules(rules_path: str):
    # ルールファイルの優先度：tools/ci/config → tools/docops_cli/config（後方互換）
    rp = Path(rules_path or DEFAULT_RULES_PRI)
    if not rp.exists():
        rp = Path(DEFAULT_RULES_FALLBACK)
    rules = {}
    if rp.exists():
        try:
            rules = yaml.safe_load(rp.read_text(encoding="utf-8")) or {}
        except Exception as e:
            print(f"[warn] ルール読込に失敗: {rp} ({e})", file=sys.stderr)
            rules = {}
    # 正規化
    rels_node = rules.get("relations", None)
    if isinstance(rels_node, dict) and "relations" in rels_node:
        relations = rels_node.get("relations", [])
    elif isinstance(rels_node, list):
        relations = rels_node
    else:
        relations = [
            {"key":"depends_on","type":"depends_on"},
            {"key":"refines","type":"refines"},
            {"key":"satisfies","type":"satisfies"},
            {"key":"integrates_with","type":"integrates_with"},
            {"key":"constrains","type":"constrains"},
            {"key":"supersedes","type":"supersedes"},
            {"key":"canonical_parent","type":"parent","scalar": True},
        ]
    include_globs = _compile_globs(rules.get("include_globs", []))
    exclude_globs = _compile_globs(rules.get("exclude_globs", ['**/.obsidian/**', '**/.git/**', '**/node_modules/**']))
    aliases = []
    for a in ensure_list(rules.get("aliases")):
        if isinstance(a, dict) and "alias" in a and "target" in a:
            aliases.append({"alias": str(a["alias"]), "target": str(a["target"])})
    id_field = str(rules.get("id_field", REQ_ID_DEFAULT))
    return {
        "relations": relations,
        "include_globs": include_globs,
        "exclude_globs": exclude_globs,
        "aliases": aliases,
        "id_field": id_field,
        "_rules_path": str(rp) if rp.exists() else None,
    }

def collect_md_files(docs_root: str, include_globs, exclude_globs):
    base = Path(docs_root)
    if not base.exists():
        return []
    files = [str(p) for p in base.rglob("*.md") if p.is_file()]
    # filter by globs
    out = []
    for p in files:
        p_norm = p.replace('\\', '/')
        if exclude_globs and _match_any(p_norm, exclude_globs):
            continue
        if include_globs:
            if _match_any(p_norm, include_globs):
                out.append(p)
        else:
            out.append(p)
    return [Path(p) for p in out]

def build_graph(docs_root: str, rules_path: str):
    rules = load_rules(rules_path)
    id_field = rules["id_field"]
    accept_prefixes = [p.upper() for p in (rules.get("accept_id_prefixes") or [])]
    md_files = collect_md_files(docs_root, rules["include_globs"], rules["exclude_globs"])

    # Collect nodes
    id_to_path = {}
    path_to_id = {}
    fm_cache = {}
    def _accept(idstr: str) -> bool:
        if not accept_prefixes:
            return True
        u = (idstr or "").upper()
        return any(u.startswith(pref) for pref in accept_prefixes)

    def _extract_inline_ids(text: str):
        ids = set()
        # 1) 行頭/見出しの "ID: XXX" 形式
        for m in re.finditer(r'(?m)^(?:#{1,6}\s+)?ID:\s*([A-Za-z0-9\-\.]+)\b', text):
            ids.add(m.group(1).strip())
        # 2) 見出し末尾の […] などにも拡張したければここで追加
        return [i for i in ids if _accept(i)]

    for p in md_files:
        fm = read_fm(p)
        fm_cache[str(p)] = fm
        if not isinstance(fm, dict):
            continue
        _id = fm.get(id_field)
        if isinstance(_id, str) and _id.strip():
            id_to_path[_id] = str(p)
            path_to_id[str(p)] = _id
        # 明示宣言された defines_ids をノード化
        for extra in ensure_list(fm.get("defines_ids")):
            if isinstance(extra, str) and extra.strip() and _accept(extra):
                id_to_path[extra] = f"{p}#{extra.lower()}"
        # 本文の ID: XXX 形式を拾ってノード化
        try:
            body = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            body = ""
        for inline in _extract_inline_ids(body):
            if inline not in id_to_path:
                id_to_path[inline] = f"{p}#{inline.lower()}"

    rels = rules["relations"]
    G = nx.DiGraph()
    #for _id, p in id_to_path.items():
    #    G.add_node(_id, path=p)
    for _id, loc in id_to_path.items():
        G.add_node(_id, path=loc)
    unknown_refs = []
    # Build edges
    for p_str, fm in fm_cache.items():
        if not isinstance(fm, dict):
            continue
        src = fm.get(id_field)
        if not src:
            continue
        for r in rels:
            key = r.get("key"); rtype = r.get("type", key)
            vals = ensure_list(fm.get(key))
            for v in vals:
                if not v:
                    continue
                dst = str(v)
                if dst not in id_to_path:
                    unknown_refs.append({"src": src, "ref": dst, "type": rtype, "path": p_str})
                G.add_edge(src, dst, type=rtype)

    # Metrics
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
        "rules_path": rules["_rules_path"],
    }
    return rules, G, unknown_refs, summary

def _numeric_suffix(s: str):
    m = re.search(r'(\d+)$', s)
    return m.group(1) if m else None

def _prefix_token(s: str):
    # 先頭の英字・大文字・記号部分（数字手前）を拾う簡易法
    m = re.match(r'^([A-Za-z\-]+)', s)
    return m.group(1) if m else s

def suggest_unknowns(docs_root: str, rules_path: str, out_dir: str,
                     threshold: float = 0.65, strong_threshold: float = 0.80):
    rules, G, unknown_refs, summary = build_graph(docs_root, rules_path)
    id_to_path = {n: G.nodes[n].get("path","") for n in G.nodes}

    # alias マップ（rules.yaml 由来）
    alias_map = {}
    for a in rules["aliases"]:
        alias_map[a["alias"]] = a["target"]

    suggestions = []
    for u in unknown_refs:
        ref = u["ref"]
        cands = []
        # 1) ルールの alias 指定があれば最優先
        if ref in alias_map and alias_map[ref] in id_to_path:
            cands.append({"id": alias_map[ref], "score": 1.0, "reason": "rules.alias"})
        else:
            # 2) 形式的ヒューリスティクス： prefix + numeric suffix で近似
            suf = _numeric_suffix(ref or "")
            pre = _prefix_token((ref or "").upper())
            for nid in id_to_path.keys():
                nid_u = nid.upper()
                score = 0.0
                if suf and nid_u.endswith(suf):
                    score += 0.5
                if pre and nid_u.startswith(pre):
                    score += 0.5
                if score > 0:
                    cands.append({"id": nid, "score": score, "reason": "prefix/suffix"})
            # 3) 部分一致（緩め）
            if not cands:
                for nid in id_to_path.keys():
                    nid_u = nid.upper()
                    if ref and ref.upper() in nid_u:
                        cands.append({"id": nid, "score": 0.3, "reason": "substring"})
        cands = sorted(cands, key=lambda x: x["score"], reverse=True)[:5]
        # 閾値でフィルタ（表示/要約のため）
        filtered = [c for c in cands if c["score"] >= threshold]
        top_score = cands[0]["score"] if cands else 0.0
        is_strong = top_score >= strong_threshold
        suggestions.append({**u,
                            "candidates": cands,
                            "filtered": filtered,
                            "top_score": top_score,
                            "strong": is_strong})

    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    (outp / "suggest.json").write_text(
        json.dumps({"summary": summary,
                    "threshold": threshold,
                    "strong_threshold": strong_threshold,
                    "suggestions": suggestions},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
    # human-readable
    lines = ["# Suggestions for unknown_refs", "", f"- unknown_refs: {summary['unknown_refs']}", ""]
    for s in suggestions:
        lines.append(f"## {s['src']} -> {s['ref']} ({s['type']}) @ {s['path']}  (top={s['top_score']}, strong={s['strong']})")
        if s["filtered"]:
            lines.append(f"- filtered (>= {threshold}):")
            for c in s["filtered"]:
                lines.append(f"  - {c['id']}  (score={c['score']}, reason={c['reason']})")
        elif s["candidates"]:
            lines.append(f"- candidates (< {threshold}):")
            for c in s["candidates"]:
                lines.append(f"- candidate: {c['id']}  (score={c['score']}, reason={c['reason']})")
        else:
            lines.append("- no candidate")
        lines.append("")
    (outp / "suggest.md").write_text("\n".join(lines), encoding="utf-8")

def write_build_outputs(G, unknown_refs, summary, out_dir: str, fmt: str):
    outp = Path(out_dir); outp.mkdir(parents=True, exist_ok=True)
    data = {
        "cycles": int(summary["cycles"]),
        "summary": summary,
        "nodes": [{"id": n, "path": G.nodes[n].get("path","")} for n in G.nodes],
        "edges": [{"src": s, "dst": t, "type": G.edges[s,t].get("type","")} for s,t in G.edges],
        "unknown_refs": unknown_refs,
    }
    (outp/"graph.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if "md" in (fmt or ""):
        lines = ["# Trace Graph", "",
                 f"- nodes: {summary['nodes']}",
                 f"- edges: {summary['edges']}",
                 f"- cycles: {summary['cycles']}",
                 f"- unknown_refs: {summary['unknown_refs']}", "" ]
        if unknown_refs:
            lines.append("## Unknown References")
            for u in unknown_refs[:200]:
                lines.append(f"- {u['src']} -> {u['ref']} ({u['type']}) @ {u['path']}")
        (outp/"graph.md").write_text("\n".join(lines), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build","suggest"])
    ap.add_argument("--rules", default=DEFAULT_RULES_PRI)
    ap.add_argument("--docs-root", default=DEFAULT_DOCS_ROOT)
    ap.add_argument("--out", default="artifacts/trace")
    ap.add_argument("--format", default="json")
    # suggest 用の閾値（指定されても build では無視される）
    ap.add_argument("--threshold", type=float, default=0.65,
                    help="候補として採用する最小スコア（suggest時）")
    ap.add_argument("--strong-threshold", type=float, default=0.80,
                    help="strong候補と見なすスコア（suggest時）")
    args = ap.parse_args()

    if args.cmd == "build":
        rules, G, unknown_refs, summary = build_graph(args.docs_root, args.rules)
        write_build_outputs(G, unknown_refs, summary, args.out, args.format)
    elif args.cmd == "suggest":
        suggest_unknowns(args.docs_root, args.rules, args.out,
                         threshold=args.threshold,
                         strong_threshold=args.strong_threshold)
if __name__ == "__main__":
    main()
