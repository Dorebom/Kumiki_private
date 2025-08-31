#!/usr/bin/env python3
import os, json, argparse, datetime, pathlib, re
from typing import Dict, Any

NOW = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

REQUIRED = {
  "doclint": ["kumiki.doclint.files_total_count","kumiki.doclint.errors_count","kumiki.doclint.duration_ms"],
  "trace": ["kumiki.trace.nodes_total_count","kumiki.trace.edges_total_count","kumiki.trace.duration_ms"],
  "indexing": ["kumiki.index.docs_indexed_count","kumiki.index.index_time_ms"],
  "gate": ["kumiki.gate.gate_ok_count","kumiki.gate.total_ci_time_ms","kumiki.gate.determinism_checksum"],
}

REPORT_PATHS = {
  "doclint": "artifacts/doclint/report.json",
  "trace": "artifacts/trace/graph.json",
  "indexing": "artifacts/search/meta.json",
  "reach": "artifacts/reach/report.json",
  "idcheck": "artifacts/idcheck/report.json",
  "i18n": "artifacts/i18n/report.json",
  "impact": "artifacts/impact/report.json",
  "secscan": "artifacts/secscan/report.json",
  "gate": "artifacts/gate/gate_summary.json"
}

def load_json(path):
  if not os.path.exists(path): return None
  with open(path, "r", encoding="utf-8") as f:
    try: return json.load(f)
    except Exception: return None

def metrics_from_reports(run_id: str) -> Dict[str, Dict[str, Any]]:
  out = {}
  # DocLint
  r = load_json(REPORT_PATHS["doclint"]) or {}
  out["doclint"] = {
    "kumiki.doclint.files_total_count": r.get("files", 0),
    "kumiki.doclint.errors_count": r.get("errors", 0),
    "kumiki.doclint.warnings_count": r.get("warnings", 0),
    "kumiki.doclint.duration_ms": int(1000 * float(r.get("time_sec", 0)))
  }
  # Trace
  g = load_json(REPORT_PATHS["trace"]) or {}
  out["trace"] = {
    "kumiki.trace.nodes_total_count": len(g.get("nodes", [])) if isinstance(g.get("nodes"), list) else g.get("nodes", 0),
    "kumiki.trace.edges_total_count": len(g.get("edges", [])) if isinstance(g.get("edges"), list) else g.get("edges", 0),
    "kumiki.trace.duration_ms": int(1000 * float(g.get("time_sec", 0)))
  }
  # Indexing
  s = load_json(REPORT_PATHS["indexing"]) or {}
  out["indexing"] = {
    "kumiki.index.docs_indexed_count": s.get("docs", 0),
    "kumiki.index.index_time_ms": int(1000 * float(s.get("build_time_sec", 0))),
    "kumiki.index.query_p95_ms": s.get("query_p95_ms", None)
  }
  # Reach
  rch = load_json(REPORT_PATHS["reach"]) or {}
  if rch:
    out["reach"] = {
      "kumiki.reach.evaluated_count": rch.get("summary",{}).get("evaluated",0),
      "kumiki.reach.roundtrip_ok_count": rch.get("summary",{}).get("roundtrip_ok",0),
      "kumiki.reach.roundtrip_rate_ratio": rch.get("summary",{}).get("roundtrip_rate",0.0),
      "kumiki.reach.duration_ms": int(1000 * float(rch.get("summary",{}).get("time_sec",0)))
    }
  # IDCheck
  idr = load_json(REPORT_PATHS["idcheck"]) or {}
  if idr:
    out["idcheck"] = {
      "kumiki.id.ids_count": idr.get("summary",{}).get("ids",0),
      "kumiki.id.duplicates_count": idr.get("summary",{}).get("duplicates",0),
      "kumiki.id.broken_refs_count": idr.get("summary",{}).get("broken_refs",0),
      "kumiki.id.gaps_count": idr.get("summary",{}).get("gaps",0),
      "kumiki.id.duration_ms": int(1000 * float(idr.get("summary",{}).get("time_sec",0)))
    }
  # I18N
  i18 = load_json(REPORT_PATHS["i18n"]) or {}
  if i18:
    out["i18n"] = {
      "kumiki.i18n.pairs_count": i18.get("summary",{}).get("pairs",0),
      "kumiki.i18n.missing_count": i18.get("summary",{}).get("missing",0),
      "kumiki.i18n.id_mismatch_count": i18.get("summary",{}).get("id_mismatch",0),
      "kumiki.i18n.relation_diff_count": i18.get("summary",{}).get("relation_diff",0),
      "kumiki.i18n.duration_ms": int(1000 * float(i18.get("summary",{}).get("time_sec",0)))
    }
  # Impact
  imp = load_json(REPORT_PATHS["impact"]) or {}
  if imp:
    out["impact"] = {
      "kumiki.impact.changed_files_count": imp.get("summary",{}).get("changed_files",0),
      "kumiki.impact.candidates_count": imp.get("summary",{}).get("candidates",0),
      "kumiki.impact.suggestions_count": imp.get("summary",{}).get("suggestions",0),
      "kumiki.impact.duration_ms": int(1000 * float(imp.get("summary",{}).get("time_sec",0)))
    }
  # SecScan
  sec = load_json(REPORT_PATHS["secscan"]) or {}
  if sec:
    out["secscan"] = {
      "kumiki.secscan.findings_count": sec.get("summary",{}).get("findings",0),
      "kumiki.secscan.high_count": sec.get("summary",{}).get("high",0),
      "kumiki.secscan.medium_count": sec.get("summary",{}).get("medium",0),
      "kumiki.secscan.low_count": sec.get("summary",{}).get("low",0),
      "kumiki.secscan.duration_ms": int(1000 * float(sec.get("summary",{}).get("time_sec",0)))
    }
  # Gate
  gate = load_json(REPORT_PATHS["gate"]) or {}
  out["gate"] = {
    "kumiki.gate.gate_ok_count": 1 if gate.get("ok") else 0,
    "kumiki.gate.total_ci_time_ms": int(1000 * float(gate.get("summary",{}).get("time_sec",0.0)) if "summary" in gate else 0),
    "kumiki.gate.determinism_checksum": gate.get("checksum","")
  }
  return out

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--rules", default="tools/docops_cli/config/obs_rules.yml")
  ap.add_argument("--out", default="artifacts/metrics")
  args = ap.parse_args()

  run_id = os.environ.get("GITHUB_RUN_ID") or os.environ.get("RUN_ID") or "local"
  repo = os.environ.get("GITHUB_REPOSITORY","local/repo")
  branch = os.environ.get("GITHUB_REF_NAME","local")
  sha = os.environ.get("GITHUB_SHA","" )
  workflow = os.environ.get("GITHUB_WORKFLOW","local")

  metrics = metrics_from_reports(run_id)
  outdir = os.path.join(args.out, run_id)
  os.makedirs(outdir, exist_ok=True)

  # Emit metrics.jsonl
  events = []
  for comp, kv in metrics.items():
    for name, value in kv.items():
      events.append({
        "ts_utc": NOW,
        "component": comp,
        "name": name,
        "value": value,
        "unit": "ms" if name.endswith("_ms") else ("count" if name.endswith("_count") else ("ratio" if name.endswith("_ratio") else "other")),
        "labels": {"repo": repo, "branch": branch, "sha": sha, "run_id": run_id, "workflow": workflow, "component": comp},
        "run_id": run_id
      })
  with open(os.path.join(outdir, "metrics.jsonl"), "w", encoding="utf-8") as f:
    for e in events:
      f.write(json.dumps(e, ensure_ascii=False) + "\n")

  # Build summary and missing required
  components = {}
  ok = True
  for comp, kv in metrics.items():
    required_keys = REQUIRED.get(comp, [])
    missing = [k for k in required_keys if k not in kv or kv[k] is None]
    if missing: ok = False
    components[comp] = {"metrics": kv, "missing": missing}

  summary = {"run":{"run_id":run_id,"repo":repo,"branch":branch,"sha":sha,"workflow":workflow,"ts_utc":NOW},
             "components":components, "ok": ok}
  with open(os.path.join(outdir, "metrics_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

  # Timeseries CSV (long format)
  import csv
  with open(os.path.join(outdir, "metrics_timeseries.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ts_utc","component","name","value","unit","run_id"])
    for e in events:
      w.writerow([e["ts_utc"], e["component"], e["name"], e["value"], e["unit"], run_id])

  # Minimal logs.jsonl
  with open(os.path.join(outdir, "logs.jsonl"), "w", encoding="utf-8") as f:
    level = "INFO" if ok else "ERROR"
    f.write(json.dumps({"ts_utc":NOW,"level":level,"component":"obs","message":"metrics collected","data":{"ok":ok}}) + "\n")

  # Fail if missing required
  if not ok:
    print("[obs] Missing required metrics; see metrics_summary.json")
    raise SystemExit(2)

if __name__ == "__main__":
  main()
