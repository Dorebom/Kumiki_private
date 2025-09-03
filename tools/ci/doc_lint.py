#!/usr/bin/env python3
import argparse, os, json, sys, re
from pathlib import Path
import argparse, os, json, sys, re, fnmatch
from pathlib import Path, PurePosixPath
try:
    import yaml
except Exception:
    print("PyYAML が必要です: pip install pyyaml", file=sys.stderr); sys.exit(1)

#REQ_KEYS = ["id","title","type","status","version","created","updated"]
DEFAULT_REQ_KEYS = ["id","title","type","status","version","created","updated"]

def read_fm(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"): return None
    end = text.find("\n---", 3)
    if end == -1: return None
    fm_text = text[3:end]
    try:
        return yaml.safe_load(fm_text) or {}
    except Exception:
        return None

def to_posix_rel(path: Path, repo_root: Path) -> str:
    # リポジトリ直下からの相対パスをPOSIX表記で返す
    return str(PurePosixPath(path.resolve().relative_to(repo_root.resolve())))

def load_rules(rules_path: str):
    if not rules_path or not os.path.exists(rules_path):
        return {
            "includes": ["docs/**/*.md"],
            "excludes": [],
            "required_keys": {"default": DEFAULT_REQ_KEYS, "per_path": []},
        }
    with open(rules_path, "r", encoding="utf-8") as f:
        y = yaml.safe_load(f) or {}
    y.setdefault("includes", ["docs/**/*.md"])
    y.setdefault("excludes", [])
    rk = y.setdefault("required_keys", {})
    rk.setdefault("default", DEFAULT_REQ_KEYS)
    rk.setdefault("per_path", [])
    return y

def match_any(posix_rel: str, patterns):
    for pat in patterns or []:
        if fnmatch.fnmatch(posix_rel, pat):
            return True
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--rules", default="tools/docops_cli/config/doclint_rules.yml")
    ap.add_argument("--docs-root", default="docs")
    ap.add_argument("--out", default="artifacts/doclint")
    ap.add_argument("--format", default="json,md")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    #docs = Path(args.docs_root)
    #md_files = [p for p in docs.rglob("*.md") if p.is_file()]

    repo_root = Path(".").resolve()
    docs_root = Path(args.docs_root).resolve()
    rules = load_rules(args.rules)

    # まず includes で候補を集める（リポジトリ相対でglob）
    candidates = set()
    for pat in rules["includes"]:
        # pat は repo 相対なので、repo_root からglobする
        for p in repo_root.glob(pat):
            if p.is_file() and p.suffix.lower() == ".md":
                candidates.add(p.resolve())

    # excludes を適用（posix 相対で一致）
    md_files = []
    for p in sorted(candidates):
        posix_rel = to_posix_rel(p, repo_root)
        if match_any(posix_rel, rules["excludes"]):
            continue
        md_files.append(p)

    errors = 0
    items = []
    ids = {}
    for p in md_files:
        fm = read_fm(p)
        if fm is None:
            errors += 1
            items.append({"path": str(p), "code": "FM_PARSE", "msg": "FrontMatterを解析できない/未記載"})
            continue
        # 必須キー（per_path で上書き）
        posix_rel = to_posix_rel(p, repo_root)
        req = rules["required_keys"]["default"]
        for rule in rules["required_keys"]["per_path"]:
            if match_any(posix_rel, rule.get("match")):
                req = rule.get("keys", req)
        for k in req:
            if k not in fm or fm[k] in ("", None, []):
                errors += 1
                items.append({"path": str(p), "code": "FM_REQUIRED_MISSING", "msg": f"必須キー欠落: {k}"})
        # id 形式（例: 大文字英数とハイフン/アンダースコア程度）
        if "id" in fm and isinstance(fm["id"], str):
            if not re.match(r"^[A-Za-z0-9_\-:.]+$", fm["id"]):
                errors += 1
                items.append({"path": str(p), "code": "ID_FORMAT", "msg": f"id形式不正: {fm['id']}"})
            # 重複チェック
            ids.setdefault(fm["id"], []).append(str(p))

    for k, paths in ids.items():
        if len(paths) > 1:
            errors += 1
            items.append({"path": paths[0], "code": "ID_DUPLICATE", "msg": f"id重複: {k}（{len(paths)}件）", "extra": {"dups": paths}})

    report = {"errors": errors, "files": len(md_files), "items": items}
    (Path(args.out)/"report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if "md" in args.format:
        lines = ["# DocLint Report", "", f"- files: {len(md_files)}", f"- errors: {errors}", ""]
        for it in items:
            lines.append(f"- [{it.get('code')}] {it.get('path')} — {it.get('msg')}")
        (Path(args.out)/"report.md").write_text("\n".join(lines), encoding="utf-8")

    # errors>0 なら非ゼロ終了
    sys.exit(1 if errors > 0 else 0)

if __name__ == "__main__":
    main()
