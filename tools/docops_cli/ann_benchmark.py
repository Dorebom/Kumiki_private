# tools/docops_cli/ann_benchmark.py
import os, time, json, argparse, importlib
import numpy as np
from connectors.embedding.local_mini import LocalMiniEmbedding
from connectors.ann.numpy_conn import NumpyExactANN

def load_rules(path):
    import yaml, io
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def build_corpus(n=2000, seed=42):
    rng = np.random.default_rng(seed)
    topics = ['alpha','bravo','charlie','delta','echo','foxtrot','golf','hotel']
    docs = []
    for i in range(n):
        t = topics[i % len(topics)]
        noise = ''.join(chr(97 + int(x%26)) for x in rng.integers(0,26, size=20))
        docs.append(f"{t} {t} {noise} #{i}")
    ids = [f"D{i:05d}" for i in range(n)]
    return ids, docs

def hit_at_k(results, truths, k=3):
    hit = 0
    for r, t in zip(results, truths):
        topk_ids = [x[0] for x in r[:k]]
        if t in topk_ids:
            hit += 1
    return hit / len(results)

def mrr_at_k(results, truths, k=10):
    s = 0.0
    for r, t in zip(results, truths):
        for rank, (rid, _) in enumerate(r[:k], start=1):
            if rid == t:
                s += 1.0/rank
                break
    return s / len(results)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rules', default='tools/docops_cli/config/ann_connectors.yml')
    ap.add_argument('--out', default='artifacts/ann_eval')
    ap.add_argument('--topk', type=int, default=None)
    args = ap.parse_args()

    rules = load_rules(args.rules)
    topk = args.topk or int(rules.get('eval',{}).get('topk',3))
    tol = float(rules.get('eval',{}).get('degrade_tolerance',0.03))

    # Build synthetic corpus and queries
    ids, docs = build_corpus(n=1000, seed=42)
    embedder = LocalMiniEmbedding(dim=int(rules['provider']['dim']), seed=int(rules['provider']['seed']))
    X = embedder.embed(docs)

    # Baseline exact
    base = NumpyExactANN(embedder.dim, metric=rules['ann']['metric'])
    t0 = time.time(); base.fit(X, ids); build_ms = (time.time()-t0)*1000

    # Queries: use a subset with small perturbations
    q_texts = [d + ' extra' for d in docs[:200]]
    q_ids = ids[:200]
    Q = embedder.embed(q_texts)

    t0 = time.time(); base_res = base.search(Q, topk=topk); base_ms = (time.time()-t0)*1000
    base_hit3 = hit_at_k(base_res, q_ids, k=3)
    base_mrr = mrr_at_k(base_res, q_ids, k=10)

    # Target backend
    backend = rules['ann']['backend']
    if backend == 'numpy':
        target = base
    elif backend == 'faiss_flat':
        from connectors.ann.faiss_conn import FaissFlatANN
        target = FaissFlatANN(embedder.dim, metric=rules['ann']['metric'])
    elif backend == 'annoy':
        from connectors.ann.annoy_conn import AnnoyANN
        p = rules['ann']['params'].get('annoy',{})
        target = AnnoyANN(embedder.dim, metric=rules['ann']['metric'], n_trees=int(p.get('n_trees',50)), search_k=int(p.get('search_k',0)))
    elif backend == 'scann':
        from connectors.ann.scann_conn import ScannANN
        p = rules['ann']['params'].get('scann',{})
        target = ScannANN(embedder.dim, metric=rules['ann']['metric'], leaves=int(p.get('leaves',2000)), reordering=int(p.get('reordering',100)))
    else:
        raise SystemExit(f'unknown backend: {backend}')

    t0 = time.time(); target.fit(X, ids); tgt_build_ms = (time.time()-t0)*1000
    t0 = time.time(); tgt_res = target.search(Q, topk=topk); tgt_ms = (time.time()-t0)*1000

    tgt_hit3 = hit_at_k(tgt_res, q_ids, k=3)
    tgt_hit1 = hit_at_k(tgt_res, q_ids, k=1)
    tgt_mrr = mrr_at_k(tgt_res, q_ids, k=10)

    degrade = float(base_hit3 - tgt_hit3)

    os.makedirs(args.out, exist_ok=True)
    report = {
        "summary": {
            "backend": backend,
            "metric": rules['ann']['metric'],
            "hit1": tgt_hit1,
            "hit3": tgt_hit3,
            "mrr": tgt_mrr,
            "hit3_base": base_hit3,
            "degrade_points": degrade,
            "qps": (len(q_texts) / (tgt_ms/1000.0)) if tgt_ms>0 else None,
            "build_time_ms": tgt_build_ms,
            "time_sec": (tgt_ms + tgt_build_ms)/1000.0
        }
    }
    with open(os.path.join(args.out, "ann_eval_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # CI friendly verdict
    ok = degrade <= tol
    print(json.dumps(report, ensure_ascii=False))
    if not ok:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
