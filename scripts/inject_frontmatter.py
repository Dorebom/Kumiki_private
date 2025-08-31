#!/usr/bin/env python3
# Inject minimal FrontMatter into .md files missing it.
import sys, re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

TEMPLATE = {
  "id": "",
  "title": "",
  "canonical_parent": "RS-00_overview",
  "refines": [],
  "derives_from": [],
  "satisfies": [],
  "depends_on": [],
  "integrates_with": [],
  "constrains": [],
  "conflicts_with": [],
  "supersedes": []
}

def has_frontmatter(text: str) -> bool:
  return text.startswith("---\n")

def derive_id_title(path: Path):
  stem = path.stem
  title = stem.replace("_", " ")
  return stem, title

def main():
  count = 0
  for p in DOCS.rglob("*.md"):
    s = p.read_text(encoding="utf-8")
    if has_frontmatter(s):
      continue
    fm = TEMPLATE.copy()
    fm["id"], fm["title"] = derive_id_title(p)
    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    new = f"---\n{fm_yaml}\n---\n\n{s}"
    p.write_text(new, encoding="utf-8")
    count += 1
  print(f"Injected FrontMatter into {count} files.")

if __name__ == '__main__':
  main()
