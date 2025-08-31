#!/usr/bin/env python3
import os, argparse, json, random, math, pathlib, textwrap, datetime
from itertools import combinations

TEMPLATE = """---
id: {id}
title: "{title}"
type: "{dtype}"
status: "draft"
version: 0.1.0
created: 2025-01-01
updated: 2025-01-01
tags: ["sample","scale"]
satisfies: ["BG-KMK-01"]
refines: []
depends_on: {depends}
integrates_with: []
constrains: []
---

# {title}

本文（{lang}）。関連: {depends_list}
"""

def mk_id(prefix, idx):
    return f"{prefix}-{idx:04d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='docs')
    ap.add_argument('--size', type=int, required=True)
    ap.add_argument('--seed', type=int, default=4242)
    args = ap.parse_args()
    random.seed(args.seed)

    ja_root = os.path.join(args.root, 'ja', 'scale')
    en_root = os.path.join(args.root, 'en', 'scale')
    os.makedirs(ja_root, exist_ok=True); os.makedirs(en_root, exist_ok=True)

    # graph: each doc depends on previous 2 within a window (small-world-ish)
    window = 5
    ids = [mk_id('SC', i+1) for i in range(args.size)]
    for i, _id in enumerate(ids):
        deps = []
        for j in range(max(0, i-window), i):
            if random.random() < 0.4:
                deps.append(ids[j])
        dlist = json.dumps(deps, ensure_ascii=False)
        title_ja = f"スケール文書 {_id}（試験用）"
        title_en = f"Scale Document {_id} (Test)"
        for lang, root in [('ja', ja_root), ('en', en_root)]:
            path = os.path.join(root, f"{_id}.md")
            title = title_ja if lang=='ja' else title_en
            body = TEMPLATE.format(id=_id, title=title, dtype='design', depends=dlist, depends_list=', '.join(deps), lang=lang)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(body)
    print(f"generated {args.size}*2 files under {args.root}/(ja|en)/scale")


if __name__ == '__main__':
    main()
