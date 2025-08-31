#!/usr/bin/env python3
# Kumiki CLI: FrontMatter -> Graph -> TF-IDF Index with validation & simple search

import argparse, sys
from pathlib import Path

try:
    import yaml
    import networkx as nx
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
except Exception as e:
    print("Missing dependency. Install via: pip install -r cli/requirements.txt", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DOCS_DIR = ROOT / "docs"

def load_lock():
    with open(CONFIG_DIR/"docops.lock", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1]
    body = parts[2]
    fm = yaml.safe_load(fm_text) or {}
    return fm, body

def iter_md_files(ignore_paths):
    for p in DOCS_DIR.rglob("*.md"):
        sp = str(p.resolve()).replace("\\","/")
        skip = False
        for rel in ignore_paths:
            if sp.startswith(str((ROOT/rel).resolve()).replace("\\","/")):
                skip = True; break
        if skip: continue
        yield p

def is_flat_frontmatter(obj):
    for k,v in obj.items():
        if isinstance(v, list):
            if not all(isinstance(x, str) for x in v):
                return False, f"Field '{k}' has non-string items in array"
        elif isinstance(v, (str,int,float,bool)) or v is None:
            continue
        else:
            return False, f"Field '{k}' has nested object"
    return True, ""

def collect_docs(lock):
    docs = {}
    texts = {}
    ignore = lock.get("docops_cli",{}).get("ignore_paths",[])
    for p in iter_md_files(ignore):
        s = p.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(s)
        docs[p] = fm
        texts[p] = body
    return docs, texts

def validate(docs, lock):
    ok = True
    allowed = set(lock["frontmatter"]["allowed_relations"])
    required = set(lock["frontmatter"]["required_fields"])
    singletons = set(lock["frontmatter"]["singletons"])
    errors = []
    ids = {}

    for p, fm in docs.items():
        missing = [k for k in required if k not in fm]
        if missing:
            ok=False; errors.append((p, f"Missing required fields: {missing}"))
        flat_ok, reason = is_flat_frontmatter(fm)
        if not flat_ok:
            ok=False; errors.append((p, f"Flat check failed: {reason}"))
        for k in singletons:
            if k in fm and isinstance(fm[k], list):
                ok=False; errors.append((p, f"'{k}' must be a single value (not list)"))
        for k,v in fm.items():
            if k in {"id","title","canonical_parent"}: continue
            if isinstance(v, list) and v and k not in allowed:
                ok=False; errors.append((p, f"Relation '{k}' not in allowed_relations"))
        if "id" in fm:
            if fm["id"] in ids:
                ok=False; errors.append((p, f"Duplicate id '{fm['id']}' also in {ids[fm['id']]}"))
            ids[fm["id"]] = p

    return ok, errors, ids

def build_graph(docs, ids, lock):
    G = nx.DiGraph()
    for p,fm in docs.items():
        if "id" in fm:
            G.add_node(fm["id"], path=str(p))
    allowed = set(lock["frontmatter"]["allowed_relations"])
    for p,fm in docs.items():
        src = fm.get("id")
        if not src: continue
        for rel in allowed:
            for tgt in fm.get(rel,[]) or []:
                if isinstance(tgt, str):
                    G.add_edge(src, tgt, rel=rel)
    return G

def tfidf_index(texts, docs):
    corpus, keys = [], []
    for p, body in texts.items():
        fm = docs[p]
        corpus.append(f"{fm.get('title','')} {body}")
        keys.append(fm.get('id', str(p)))
    vec = TfidfVectorizer(max_features=5000)
    X = vec.fit_transform(corpus)
    return vec, X, keys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--graph", action="store_true")
    ap.add_argument("--search", metavar="QUERY")
    args = ap.parse_args()

    lock = load_lock()
    docs, texts = collect_docs(lock)
    ok, errors, ids = validate(docs, lock)
    if args.check:
        if ok:
            print("OK: all checks passed")
        else:
            print("NG: validation errors:")
            for p,msg in errors:
                print(f"- {p}: {msg}")

    G = build_graph(docs, ids, lock)
    if args.graph:
        print(f"Graph nodes: {G.number_of_nodes()} edges: {G.number_of_edges()}")
        root = "RS-00_overview"
        if root in G:
            reachable = set()
            for n in G.nodes:
                try:
                    if nx.has_path(G, root, n):
                        reachable.add(n)
                except Exception:
                    pass
            unreachable = set(G.nodes) - reachable
            if unreachable:
                print("Unreachable from RS-00_overview:", sorted(unreachable))
            else:
                print("All nodes reachable from RS-00_overview")
        else:
            print("Warning: RS-00_overview not found")

    if args.search:
        vec, X, keys = tfidf_index(texts, docs)
        qv = vec.transform([args.search])
        scores = (X @ qv.T).toarray().ravel()
        top = np.argsort(scores)[::-1][:5]
        print("Top hits:")
        for i in top:
            print(f"- {keys[i]} : score={scores[i]:.4f}")

if __name__ == "__main__":
    main()
