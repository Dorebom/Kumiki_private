# tools/ci/search.py
# Minimal Search Index builder (BM25-lite via TF-IDF) + manifest/eval出力
import argparse, yaml, json, re, sys
from pathlib import Path
from datetime import datetime

def load_rules(p):
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def read_frontmatter(text: str):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    import yaml as _y
    return _y.safe_load(text[3:end]) or {}

def collect_docs(include_globs, exclude_globs):
    import glob
    files = set()
    for g in include_globs or ["docs/**/*.md"]:
        for p in glob.glob(g, recursive=True):
            files.add(Path(p))
    def excluded(p: Path):
        s = str(p)
        for g in exclude_globs or []:
            if Path().glob(g):
                # fallback: simple substring check to avoid heavy glob on each file
                pass
        for g in exclude_globs or []:
            if Path().match.__doc__:  # no-op
                pass
        # simple check
        ex = any(re.search(g.replace("**/","").replace("*","[^/]*"), s) for g in (exclude_globs or []))
        return ex
    return sorted([p for p in files if p.is_file()])

def build_index(docs):
    # 最小：id→path のマッピングと、全文結合のTF-IDFを作る（将来ANN差替え前提）
    texts, ids, paths = [], [], []
    for p in docs:
        t = p.read_text(encoding="utf-8", errors="ignore")
        fm = read_frontmatter(t)
        _id = fm.get("id") or p.stem
        body = t.split("\n---",2)[-1] if t.startswith("---") else t
        ids.append(_id); paths.append(str(p)); texts.append(body)
    # ベクトル化（ダミー実装：依存最小化のため保存はスキップ）
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer(ngram_range=(1,2), min_df=1)
    X = vec.fit_transform(texts)  # noqa: F841  # 実体は使わずにmanifestだけ
    return {"ids": ids, "paths": paths, "vocab_size": len(vec.vocabulary_)}

def write_outputs(out_dir: Path, idx_meta: dict):
    (out_dir / "index").mkdir(parents=True, exist_ok=True)
    (out_dir / "eval").mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "kumiki.search.index/v1",
        "ann_backend": "none",
        "embedding_dim": 0,
        "files": {
            "bm25": "index/tfidf.npz",     # 予約名（将来差し替え用）
            "map":  "index/id_to_path.json"
        },
        "build": {
            "ts": datetime.utcnow().isoformat(timespec="seconds")+"Z",
            "count": len(idx_meta["ids"]),
            "vocab": idx_meta["vocab_size"]
        }
    }
    (out_dir / "index" / "id_to_path.json").write_text(
        json.dumps(dict(zip(idx_meta["ids"], idx_meta["paths"])), ensure_ascii=False, indent=2),
        encoding="utf-8")
    (out_dir / "index" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8")
    # 最小の評価レポート（ベースライン確立用）
    eval_report = {"dataset": "bootstrap", "metrics": {"hit@3": None, "ndcg@10": None}}
    (out_dir / "eval" / "report.json").write_text(json.dumps(eval_report, ensure_ascii=False, indent=2), encoding="utf-8")

def cmd_index(args):
    rules = load_rules(args.rules)
    paths = rules.get("paths", {})
    include = paths.get("include") or ["docs/**/*.md"]
    exclude = paths.get("exclude") or ["**/.obsidian/**","node_modules/**"]
    docs = collect_docs(include, exclude)
    idx_meta = build_index(docs)
    write_outputs(Path(args.out), idx_meta)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ap_i = sub.add_parser("index")
    ap_i.add_argument("--rules", required=True)
    ap_i.add_argument("--out", required=True)
    ap_i.set_defaults(func=cmd_index)
    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
