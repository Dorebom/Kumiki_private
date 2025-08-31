#!/usr/bin/env python3
import os, sys, json, yaml, subprocess, fnmatch, re, pathlib, textwrap

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def git_diff_names(base):
    # Determine base branch via env when available
    base_ref = os.environ.get("GITHUB_BASE_REF") or "origin/main"
    sh("git fetch origin +refs/heads/*:refs/remotes/origin/* > /dev/null 2>&1")
    merge_base = sh(f"git merge-base {base_ref} HEAD").stdout.strip() or "HEAD~1"
    res = sh(f"git diff --name-only {merge_base}...HEAD")
    files = [l.strip() for l in res.stdout.splitlines() if l.strip()]
    return files, merge_base

def count_changed_lines(merge_base):
    res = sh(f"git diff --numstat {merge_base}...HEAD").stdout.strip().splitlines()
    lines = 0
    for row in res:
        parts = row.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            lines += int(parts[0]) + int(parts[1])
    return lines

def match_any(path, globs):
    return any(fnmatch.fnmatch(path, g) for g in globs)

def frontmatter(path):
    try:
        text = open(path, "r", encoding="utf-8").read()
    except Exception:
        return None
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            import yaml as _yaml
            try:
                return _yaml.safe_load(text[3:end])
            except Exception:
                return None
    return None

def fm_from_git(merge_base, path):
    res = sh(f"git show {merge_base}:{path}")
    if res.returncode != 0:
        return None
    text = res.stdout
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            import yaml as _yaml
            try:
                return _yaml.safe_load(text[3:end])
            except Exception:
                return None
    return None

def read_json(p):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def main():
    rules_path = sys.argv[1] if len(sys.argv) > 1 else "tools/docops_cli/config/approval_rules.yml"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "artifacts/approval"
    os.makedirs(outdir, exist_ok=True)
    rules = yaml.safe_load(open(rules_path, "r", encoding="utf-8"))

    files, base = git_diff_names(base=None)
    changed_lines = count_changed_lines(base)
    reasons = []
    risk = "low"

    # 1) Path-based critical
    crit_paths = rules["critical"]["path_globs"]
    for p in files:
        if match_any(p, crit_paths):
            reasons.append(f"path_critical:{p}")
            risk = "critical"

    # 2) FM changes
    fm_forbid = set(rules["critical"].get("fm_forbid_modify", []))
    fm_sensitive = rules["critical"].get("fm_sensitive", {})
    for p in files:
        if not p.endswith(".md"): continue
        fm_new = frontmatter(p) or {}
        fm_old = fm_from_git(base, p) or {}
        # forbid modify
        for k in fm_forbid:
            if k in fm_new and k in fm_old and fm_new[k] != fm_old[k]:
                reasons.append(f"fm_forbid_modify:{p}:{k}")
                risk = "critical"
        # sensitive: status publish
        if fm_sensitive.get("status_publish", True):
            if fm_old.get("status") != "published" and fm_new.get("status") == "published":
                reasons.append(f"fm_status_promote:{p}")
                risk = "critical"
        # sensitive: required fields removed
        for k in fm_sensitive.get("remove_trace_fields", []):
            if k in fm_old and k not in fm_new:
                reasons.append(f"fm_remove_key:{p}:{k}")
                risk = "critical"

    # 3) Check artifacts
    doclint = read_json("artifacts/doclint/report.json") or {}
    if int(doclint.get("errors", 0)) > int(rules["critical"]["checks"].get("doclint_errors_gt", 0)):
        reasons.append("check_doclint_errors>0"); risk = "critical"
    secscan = read_json("artifacts/secscan/report.json") or {}
    if int(secscan.get("summary", {}).get("high", 0)) > int(rules["critical"]["checks"].get("secscan_high_gt", 0)):
        reasons.append("check_secscan_high>0"); risk = "critical"
    trace = read_json("artifacts/trace/graph.json") or {}
    cycles = int(trace.get("cycles", 0)) if isinstance(trace.get("cycles", 0), int) else 0
    if cycles > int(rules["critical"]["checks"].get("trace_cycles_gt", 0)):
        reasons.append("check_trace_cycles>0"); risk = "critical"
    idr = read_json("artifacts/idcheck/report.json") or {}
    id_issues = int(idr.get("summary", {}).get("duplicates", 0)) + int(idr.get("summary", {}).get("broken_refs", 0))
    if id_issues > int(rules["critical"]["checks"].get("id_issues_gt", 0)):
        reasons.append("check_id_issues>0"); risk = "critical"

    # 4) Size thresholds
    max_lines = int(rules["critical"]["size_threshold"]["max_changed_lines"])
    max_files = int(rules["critical"]["size_threshold"]["max_changed_files"])
    if changed_lines > max_lines or len(files) > max_files:
        reasons.append(f"size_large:lines={changed_lines},files={len(files)}")
        risk = "critical"

    # Labels from event
    labels_present = []
    try:
        ev = json.load(open(os.environ.get("GITHUB_EVENT_PATH",""), "r", encoding="utf-8"))
        labels_present = [l["name"] for l in ev.get("pull_request", {}).get("labels", [])]
    except Exception:
        pass

    require_manual = (risk == "critical")
    manual_label = rules.get("manual_approval_label", "approved:human")
    needs_label = rules.get("labels", {}).get("needs_approval", "needs-approval")
    allow_label = rules["automerge"]["allow_label"]
    can_automerge = (not require_manual) and (allow_label in labels_present or rules["automerge"]["allow_label"] in labels_present)

    # If manual label exists, we pass gate even if critical (human acknowledged)
    gate_ok = True
    if require_manual and (manual_label not in labels_present):
        gate_ok = False

    # Compose report
    report = {
        "risk": risk,
        "reasons": reasons,
        "require_manual": bool(require_manual),
        "can_automerge": bool(can_automerge and gate_ok),
        "labels": {"present": labels_present, "added": [], "removed": []},
        "ci": {"checks_passed": None, "artifacts": [
            "artifacts/doclint/report.json",
            "artifacts/secscan/report.json",
            "artifacts/trace/graph.json",
            "artifacts/idcheck/report.json"
        ]}
    }
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Also emit audit event stub
    ae = {
        "kind":"approval_gate",
        "risk": risk,
        "require_manual": bool(require_manual),
        "ts_utc": __import__("datetime").datetime.utcnow().isoformat()+"Z",
        "reasons": reasons,
        "labels": labels_present
    }
    with open(os.path.join(outdir, "audit_event.json"), "w", encoding="utf-8") as f:
        json.dump(ae, f, ensure_ascii=False, indent=2)

    # Exit codes: 0 ok; 2 require manual (no manual label); 3 general error
    if not gate_ok:
        print(json.dumps(report, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0)

if __name__ == "__main__":
    main()
