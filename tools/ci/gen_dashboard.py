#!/usr/bin/env python3
import json, os, sys, glob, yaml
from pathlib import Path

def read_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None

def main():
    repo = Path(".").resolve()
    art = repo / "artifacts"
    lines = []
    lines.append("# ロードマップ・ダッシュボード（自動生成）\n")
    dl = read_json(art / "doclint" / "report.json")
    if dl:
        major = sum(1 for it in dl.get("items",[]) if (it.get("severity") in ("major","critical")))
        lines.append(f"- **DocLint**: files={dl.get('files','?')} / major+critical={major} / errors={dl.get('errors','?')}  \n  ↳ `artifacts/doclint/report.json`")
    else:
        lines.append("- **DocLint**: まだデータがありません")
    tr = read_json(art / "trace" / "graph.json")
    if tr:
        nodes = tr.get('summary',{}).get('nodes', tr.get('nodes') and len(tr.get('nodes')))
        edges = tr.get('summary',{}).get('edges', tr.get('edges') and len(tr.get('edges')))
        unknown = tr.get('summary',{}).get('unknown_refs', tr.get('unknown_refs') and len(tr.get('unknown_refs')))
        lines.append(f"- **Trace**: nodes={nodes} / edges={edges} / cycles={tr.get('cycles','?')} / unknown={unknown}  \n  ↳ `artifacts/trace/graph.json`")
    else:
        lines.append("- **Trace**: まだデータがありません")
    ss = read_json(art / "secscan" / "findings.json")
    if ss:
        lines.append(f"- **SecScan**: total={ss.get('total','?')}（criticalはFail）  \n  ↳ `artifacts/secscan/findings.json`")
    else:
        lines.append("- **SecScan**: まだデータがありません")
    se = read_json(art / "search" / "eval" / "report.json")
    if se:
        m = se.get("metrics",{})
        lines.append(f"- **Search**: hit@3={m.get('hit@3','?')} / ndcg@10={m.get('ndcg@10','?')}  \n  ↳ `artifacts/search/eval/report.json`")
    else:
        lines.append("- **Search**: まだデータがありません")
    gt = read_json(art / "gate" / "summary.json")
    if gt:
        lines.append(f"- **Gate**: decision={gt.get('decision','?')} / checks={len(gt.get('reasons',[]))}  \n  ↳ `artifacts/gate/summary.json`")
    else:
        lines.append("- **Gate**: まだデータがありません")
    out = repo / "docs" / "00_concept" / "ROADMAP_DASHBOARD.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(str(out))

if __name__ == "__main__":
    main()
