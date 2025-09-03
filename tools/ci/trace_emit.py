#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibility wrapper for older workflow steps.
Runs: trace.py build --format json,md
"""
import sys, os, subprocess
from pathlib import Path

def main():
    here = Path(__file__).resolve().parent
    trace_cli = here / "trace.py"
    if not trace_cli.exists():
        print("trace.py not found next to trace_emit.py", file=sys.stderr)
        sys.exit(1)
    out_dir = "artifacts/trace"
    cmd = [sys.executable, str(trace_cli), "build", "--out", out_dir, "--format", "json,md"]
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
