#!/usr/bin/env python3
import sys, json, yaml, os, re
from pathlib import Path

def load_yaml(p):
    if not p.exists(): return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

def read_frontmatter(md: str):
    if not md.startswith("---"): return {}
    end = md.find("\n---", 3)
    if end == -1: return {}
    import yaml as _yaml
    return _yaml.safe_load(md[3:end]) or {}

def main():
    repo = Path(".").resolve()
    docs = repo / "docs" / "00_concept"
    cfg = repo / "tools" / "docops_cli" / "config" / "roadmap.yml"
    conf = load_yaml(cfg)
    # Collect CRs
    cr_files = sorted(docs.glob("CR-KMK-*.md"))
    crs = []
    for p in cr_files:
        fm = read_frontmatter(p.read_text(encoding="utf-8"))
        cid = fm.get("id") or p.stem
        status = (fm.get("status") or "draft").lower()
        crs.append({"id": cid, "status": status, "path": str(p)})
    # Sprint assignment (from config)
    plan = conf.get("sprints", {})
    # Status buckets
    def bucket(status):
        if status in ("done","published","released"): return "done"
        if status in ("review","ready","gate-pass"): return "in-progress"
        return "todo"
    # Compose tables
    lines = []
    lines.append("# バーンダウン（CR / BG / HLF）\n")
    # CR-by-sprint
    lines.append("## CR バーンダウン（スプリント別）\n")
    lines.append("| Sprint | 計画CR | done | in-progress | todo |")
    lines.append("|---|---:|---:|---:|---:|")
    for s, meta in plan.items():
        planned = set(meta.get("cr", []))
        done = inprog = todo = 0
        for c in crs:
            if c["id"] in planned:
                b = bucket(c["status"])
                if b=="done": done+=1
                elif b=="in-progress": inprog+=1
                else: todo+=1
        lines.append(f"| {s} | {len(planned)} | {done} | {inprog} | {todo} |")
    # BG/HLF coverage via CR FM fields
    bg_counts = {}
    hlf_counts = {}
    for c in crs:
        fm = read_frontmatter(Path(c["path"]).read_text(encoding="utf-8"))
        bgs = fm.get("contributes_to") or []
        hlfs = fm.get("satisfies_hlf") or []
        for b in bgs:
            bg_counts.setdefault(b, {"done":0,"in-progress":0,"todo":0,"total":0})
            bg_counts[b]["total"]+=1
            bg_counts[b][bucket(c["status"])]+=1
        for h in hlfs:
            hlf_counts.setdefault(h, {"done":0,"in-progress":0,"todo":0,"total":0})
            hlf_counts[h]["total"]+=1
            hlf_counts[h][bucket(c["status"])]+=1
    lines.append("\n## BG バーンダウン（CR貢献ベース）\n")
    lines.append("| BG | total | done | in-progress | todo |")
    lines.append("|---|---:|---:|---:|---:|")
    for bg in sorted(bg_counts.keys()):
        v = bg_counts[bg]
        lines.append(f"| {bg} | {v['total']} | {v['done']} | {v['in-progress']} | {v['todo']} |")
    lines.append("\n## HLF バーンダウン（CR満たしベース）\n")
    lines.append("| HLF | total | done | in-progress | todo |")
    lines.append("|---|---:|---:|---:|---:|")
    for h in sorted(hlf_counts.keys()):
        v = hlf_counts[h]
        lines.append(f"| {h} | {v['total']} | {v['done']} | {v['in-progress']} | {v['todo']} |")
    out = repo / "docs" / "00_concept" / "ROADMAP_BURNDOWN.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(str(out))

if __name__ == "__main__":
    main()
