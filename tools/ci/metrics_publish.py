#!/usr/bin/env python3
import os, shutil, argparse, datetime, json, subprocess

def copytree(src, dst):
  os.makedirs(dst, exist_ok=True)
  for root, dirs, files in os.walk(src):
    rel = os.path.relpath(root, src)
    for d in dirs:
      os.makedirs(os.path.join(dst, rel, d), exist_ok=True)
    for fn in files:
      s = os.path.join(root, fn)
      t = os.path.join(dst, rel, fn)
      shutil.copy2(s, t)

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--inroot", default="artifacts/metrics")
  ap.add_argument("--outroot", default="public/metrics")
  ap.add_argument("--worm", action="store_true")
  args = ap.parse_args()

  run_id = os.environ.get("GITHUB_RUN_ID","local")
  ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
  src = os.path.join(args.inroot, run_id)
  dst = os.path.join(args.outroot, f"{ts}-{run_id}")
  if not os.path.exists(src):
    raise SystemExit(f"metrics input not found: {src}")
  copytree(src, dst)

  # Optional: append to WORM ledger via audit.py if present
  if args.worm and os.path.exists("tools/docops_cli/audit.py"):
    try:
      subprocess.run([
        "python","tools/docops_cli/audit.py","append",
        "--rules","tools/docops_cli/config/audit_rules.yml",
        "--out","artifacts/ledger"
      ], check=False)
    except Exception:
      pass

  print(f"Published metrics to {dst}")

if __name__ == "__main__":
  main()
