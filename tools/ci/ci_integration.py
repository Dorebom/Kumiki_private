#!/usr/bin/env python3
import os, sys, subprocess, json, datetime, argparse

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def changed_files():
    out = sh("git status --porcelain").stdout.strip().splitlines()
    files = []
    for line in out:
        if not line: continue
        files.append(line.split()[-1])
    return files

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update-mkdocs", action="store_true", help="mkdocs.yml も更新する")
    # ap.add_argument("--auto-commit", action="store_true", help="push イベント時に自動コミットを試行")
    ap.add_argument("--auto-commit", action="store_true", help="push イベント時に自動コミットを試行")
    ap.add_argument("--no-fail-on-diff", action="store_true", help="PRでも未コミット差分でFailしない（警告のみ）")
    ap.add_argument("--out", default="artifacts/integration")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # 1) generate index (& mkdocs)
    cmd = "python tools/ci/gen_index.py"
    if args.update_mkdocs:
        cmd += " --update-mkdocs"
    res = sh(cmd)
    gen_ok = (res.returncode == 0)
    # collect changed files
    files = changed_files()

    # 2) If push and auto-commit requested, try to commit changes
    event_name = os.environ.get("GITHUB_EVENT_NAME","")
    tried_commit = False
    commit_ok = False
    commit_msg = ""
    auto_commit = getattr(args, "auto_commit", False)
    if event_name == "push" and auto_commit and files:
    # if event_name == "push" and args.auto-commit and files:
        tried_commit = True
        sh('git config user.email "github-actions[bot]@users.noreply.github.com"')
        sh('git config user.name "github-actions[bot]"')
        sh("git add docs/index.md mkdocs.yml tools/docops_cli/config/nav_order.yml 2>/dev/null || true")
        c = sh('git commit -m "chore(docs): regenerate index & mkdocs [skip ci]"')
        if c.returncode == 0:
            p = sh("git push")
            commit_ok = (p.returncode == 0)
            commit_msg = p.stderr.strip() or p.stdout.strip()
        else:
            commit_msg = c.stderr.strip() or c.stdout.strip()

    report = {
        "ts_utc": datetime.datetime.utcnow().isoformat()+"Z",
        "gen_cmd": cmd,
        "gen_ok": gen_ok,
        "changed_files": files,
        "event": event_name,
        "tried_commit": tried_commit,
        "commit_ok": commit_ok,
        "commit_msg": commit_msg
    }
    with open(os.path.join(args.out, "gen_index_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Exit policy:
    # - On PR: fail (exit 2) if changed_files exist → 開発者にコミットを促す
    # - On push: OK. If auto-commit requested but failed, still succeed (warn in report)
    if event_name == "pull_request" and files:
        print(json.dumps(report, ensure_ascii=False))
        sys.exit(2)

    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0 if gen_ok else 1)

if __name__ == "__main__":
    main()
