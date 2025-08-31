#!/usr/bin/env python3
import os, sys, json, yaml

def read_json(p):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def exists(p):
    return os.path.exists(p)

def main():
    rules_path = sys.argv[1] if len(sys.argv) > 1 else "tools/docops_cli/config/publish_rules.yml"
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    paths = rules["paths"]
    required = set(rules["gate"]["required"])
    optional = set(rules["gate"].get("optional", []))
    thresholds = rules["gate"].get("thresholds", {})

    status = {}
    # DocLint
    dl = read_json(paths.get("doclint_report", ""))
    status["doclint"] = bool(dl) and (dl.get("errors", 0) == 0 or dl.get("ok") is True)

    # Trace
    status["trace"] = exists(paths.get("trace_graph", ""))

    # Indexing
    smeta = read_json(paths.get("search_meta", ""))
    status["indexing"] = bool(smeta) if thresholds.get("search_meta_required", True) else exists(paths.get("search_meta", ""))

    # SecScan
    sec = read_json(paths.get("secscan_report", ""))
    if sec is None:
        status["secscan"] = True
    else:
        high = int(sec.get("summary", {}).get("high", 0))
        status["secscan"] = high <= int(thresholds.get("secscan_high", 0))

    # Optional reports (existence-based pass if present)
    opt_map = {"reach":"reach_report","idcheck":"id_report","i18n":"i18n_report","impact":"impact_report"}
    for opt, key in opt_map.items():
        if opt in optional:
            status[opt] = exists(paths.get(key, "")) or True

    missing_required = [k for k in required if not status.get(k, False)]
    ok = (len(missing_required) == 0) and status.get("secscan", True)

    summary = {"ok": ok, "missing_required": missing_required, "status": status}
    os.makedirs("artifacts/gate", exist_ok=True)
    with open("artifacts/gate/gate_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False))
    sys.exit(0 if ok else 2)

if __name__ == "__main__":
    main()
