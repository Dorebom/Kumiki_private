#!/usr/bin/env python3
import os, time, json, argparse, subprocess, datetime, csv, statistics
import yaml, random
from pathlib import Path

def run(cmd):
    t0 = time.time()
    res = subprocess.run(cmd, shell=True)
    dt = int((time.time()-t0)*1000)
    return res.returncode, dt

def load_json(p):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def measure_one(size, rules):
    # seed docs
    returncode, _ = run(f"python tools/ci/seed_docs.py --root docs --size {size} --seed {rules['seeds']['docs_seed']}")
    # DocLint
    rc_dl, t_dl = run("python tools/docops_cli/lint.py check --rules tools/docops_cli/config/doclint_rules.yml --out artifacts/doclint --format json,md")
    rc_tr, t_tr = run("python tools/docops_cli/trace.py build --rules tools/docops_cli/config/trace_rules.yml --out artifacts/trace --format json")
    rc_ix, t_ix = run("python tools/docops_cli/search.py index --rules tools/docops_cli/config/search_rules.yml --out artifacts/search")
    rc_sc, t_sc = run("python tools/docops_cli/secscan.py scan --rules tools/docops_cli/config/secscan_rules.yml --allow tools/docops_cli/config/secscan_allowlist.yml --out artifacts/secscan --format json,md || true")
    rc_gt, t_gt = run("python tools/ci/aggregate_gate.py tools/docops_cli/config/publish_rules.yml || true")
    # Measure quality
    dl = load_json('artifacts/doclint/report.json')
    tr = load_json('artifacts/trace/graph.json')
    sc = load_json('artifacts/secscan/report.json')
    idr = load_json('artifacts/idcheck/report.json')
    # Search simple eval via ANN benchmark (uses synthetic queries)
    rc_ev, t_ev = run("python tools/docops_cli/ann_benchmark.py --rules tools/docops_cli/config/ann_connectors.yml --out artifacts/ann_eval")
    ev = load_json('artifacts/ann_eval/ann_eval_report.json')
    hit3 = ev.get('summary',{}).get('hit3', 0.0)
    mrr = ev.get('summary',{}).get('mrr', 0.0)

    quality = {
        'doclint_errors': int(dl.get('errors', 0)),
        'secscan_high': int(sc.get('summary',{}).get('high', 0)),
        'trace_cycles': int(tr.get('cycles', 0)) if isinstance(tr.get('cycles',0), int) else 0,
        'id_issues': int(idr.get('summary',{}).get('duplicates',0)) + int(idr.get('summary',{}).get('broken_refs',0)),
        'hit3_ratio': float(hit3),
        'mrr': float(mrr)
    }
    comp = {
        'doclint_ms': t_dl,
        'trace_ms': t_tr,
        'index_ms': t_ix,
        'secscan_ms': t_sc,
        'gate_ms': t_gt,
        'publish_ms': 0
    }
    ci_time_ms = t_dl + t_tr + t_ix + t_sc + t_gt
    return {'size': size, 'ci_time_ms': ci_time_ms, 'components': comp, 'quality': quality}

def analyze(sizes):
    # linear slope for each component
    comps = ['doclint_ms','trace_ms','index_ms','secscan_ms','gate_ms']
    slopes = {}
    xs = [s['size'] for s in sizes]
    import numpy as np
    X = np.array(xs, dtype=float)
    for c in comps:
        Y = np.array([s['components'][c] for s in sizes], dtype=float)
        # slope via least squares with intercept
        A = np.vstack([X, np.ones_like(X)]).T
        m, b = np.linalg.lstsq(A, Y, rcond=None)[0]
        slopes[c] = m
    total = sum(slopes.values()) or 1.0
    hints = {
        'doclint_ms': '並列ファイル走査・FrontMatterパースのキャッシュ',
        'trace_ms': 'ID辞書キャッシュ・関係計算の増分化',
        'index_ms': 'シャーディングと並列構築、前処理キャッシュ',
        'secscan_ms': '拡張子プリフィルタと高コスト規則の遅延適用',
        'gate_ms': '集約のI/O最適化'
    }
    ranked = sorted([{ 'component':k, 'slope_ms_per_doc':float(v), 'share_ratio':float(v/total), 'hint':hints.get(k,'') } for k,v in slopes.items()], key=lambda x:-x['slope_ms_per_doc'])
    return ranked[:3]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rules', default='tools/docops_cli/config/scale_rules.yml')
    ap.add_argument('--out', default='artifacts/scale')
    args = ap.parse_args()
    rules = yaml.safe_load(open(args.rules,'r',encoding='utf-8'))
    sizes = []
    t0 = time.time()
    for n in rules['sizes']:
        sizes.append(measure_one(int(n), rules))
    wall = int((time.time()-t0)*1000)
    # verdicts
    ok_time = (sizes[-1]['ci_time_ms'] / 60000.0) < float(rules['thresholds']['max_ci_minutes_at_1000'])
    ok_violation = all(s['quality']['doclint_errors']==0 and s['quality']['secscan_high']==0 and s['quality']['trace_cycles']==0 and s['quality']['id_issues']==0 for s in sizes)
    ok = ok_time and ok_violation
    # bottlenecks
    bottlenecks = analyze(sizes)
    # emit report
    run_meta = {
        'ts_utc': datetime.datetime.utcnow().isoformat()+'Z',
        'commit': os.environ.get('GITHUB_SHA',''),
        'workflow': os.environ.get('GITHUB_WORKFLOW',''),
        'runner': os.environ.get('RUNNER_NAME','')
    }
    outdir = os.path.join(args.out, os.environ.get('GITHUB_RUN_ID','local'))
    os.makedirs(outdir, exist_ok=True)
    report = {'run': run_meta, 'sizes': sizes, 'bottlenecks': bottlenecks, 'ok': bool(ok)}
    with open(os.path.join(outdir, 'scale_report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    # timeseries CSV
    import csv
    with open(os.path.join(outdir, 'timeseries.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['size','component','time_ms','doclint_errors','secscan_high','trace_cycles','id_issues','hit3','mrr'])
        for s in sizes:
            for k,v in s['components'].items():
                w.writerow([s['size'], k, v, s['quality']['doclint_errors'], s['quality']['secscan_high'], s['quality']['trace_cycles'], s['quality']['id_issues'], s['quality']['hit3_ratio'], s['quality']['mrr']])
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    main()
