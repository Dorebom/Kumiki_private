
from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional

FM_DELIM = re.compile(r'^---\s*$', re.M)

# Robust matcher: accepts "ID: BG-FOO-01" in bold/list/quote contexts
LOCAL_BG_PATTERN = re.compile(
    r'^[>\s\-*]*\*{0,2}ID\s*:\s*(BG-[A-Za-z0-9]+-\d+)\b',
    re.M
)

ID_IN_FM_PATTERN = re.compile(r'^\s*id\s*:\s*([A-Za-z0-9#\-_\.]+)\s*$', re.M)

@dataclass
class LocalBG:
    doc_id: str
    local_id: str
    fqid: str
    file: str
    anchor: str

class AliasResolver:
    """
    Extract local BG IDs (e.g., 'BG-KMK-01') from a document body and
    build an alias map so any file can refer to 'BG-KMK-01' and resolve to
    'CR-KMK-00#BG-KMK-01' (FQID).

    Also emits lint suggestions to downgrade 'satisfies: [BG-...]' to
    'derives_from' (policy-friendly) without rewriting files.
    """

    def __init__(self, docs_root: str) -> None:
        self.docs_root = docs_root
        self.alias_map: Dict[str, str] = {}
        self.local_index: List[LocalBG] = []

    # ----------------------------- parsing utils -----------------------------
    def _read_text(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _split_fm(self, text: str) -> Tuple[Optional[str], str]:
        m = list(FM_DELIM.finditer(text))
        if len(m) >= 2 and m[0].start() == 0:
            fm = text[m[0].end():m[1].start()]
            body = text[m[1].end():]
            return fm, body
        return None, text

    def _parse_doc_id(self, path: str, fm_text: Optional[str]) -> str:
        if fm_text:
            m = ID_IN_FM_PATTERN.search(fm_text)
            if m:
                return m.group(1).strip()
        base = os.path.basename(path)
        name, _ext = os.path.splitext(base)
        return name.split("_")[0]

    def _parse_fm_relations(self, fm_text: Optional[str]) -> Dict[str, List[str]]:
        rels: Dict[str, List[str]] = {}
        if not fm_text:
            return rels
        for line in fm_text.splitlines():
            if ":" not in line:
                continue
            key, rest = line.split(":", 1)
            key = key.strip()
            arr_m = re.search(r'\[(.*?)\]', rest)
            if not arr_m:
                continue
            items_raw = arr_m.group(1)
            items = [s.strip().strip('"\'') for s in items_raw.split(",") if s.strip()]
            items = [s for s in items if re.match(r'^[A-Za-z0-9#\-_\.]+$', s)]
            if items:
                rels[key] = items
        return rels

    # ----------------------------- extraction -----------------------------
    def extract_local_bgs_from_file(self, path: str) -> List[LocalBG]:
        text = self._read_text(path)
        fm_text, body = self._split_fm(text)
        doc_id = self._parse_doc_id(path, fm_text)

        locals_found: List[LocalBG] = []
        for m in LOCAL_BG_PATTERN.finditer(body):
            local_id = m.group(1)
            fqid = f"{doc_id}#{local_id}"
            locals_found.append(LocalBG(
                doc_id=doc_id,
                local_id=local_id,
                fqid=fqid,
                file=os.path.relpath(path, self.docs_root),
                anchor=local_id
            ))
        return locals_found

    def scan_docs(self) -> None:
        for root, _dirs, files in os.walk(self.docs_root):
            for fn in files:
                if not fn.lower().endswith(".md"):
                    continue
                path = os.path.join(root, fn)
                local_bgs = self.extract_local_bgs_from_file(path)
                self.local_index.extend(local_bgs)

        for item in self.local_index:
            if item.local_id in self.alias_map and self.alias_map[item.local_id] != item.fqid:
                raise RuntimeError(
                    f"Duplicate BG local-id across files: {item.local_id}"
                    f" -> {self.alias_map[item.local_id]} vs {item.fqid}"
                )
            self.alias_map[item.local_id] = item.fqid

    # ----------------------------- relations handling -----------------------------
    def downgrade_bg_satisfies(self, fm_text: Optional[str]) -> Optional[Dict[str, List[str]]]:
        if not fm_text:
            return None
        rels = self._parse_fm_relations(fm_text)
        sat = rels.get("satisfies", [])
        bg_sat = [x for x in sat if x.startswith("BG-")]
        if not bg_sat:
            return None
        derives = rels.get("derives_from", [])
        new_derives = sorted(set(derives + bg_sat))
        remaining_sat = [x for x in sat if not x.startswith("BG-")]
        return {
            "move_to_derives_from": bg_sat,
            "derives_from_after": new_derives,
            "satisfies_after": remaining_sat,
        }

    # ----------------------------- outputs -----------------------------
    def write_outputs(self, out_dir: str) -> Dict[str, str]:
        os.makedirs(out_dir, exist_ok=True)
        alias_path = os.path.join(out_dir, "id_aliases.json")
        index_path = os.path.join(out_dir, "local_bg_index.json")

        with open(alias_path, "w", encoding="utf-8") as f:
            json.dump(self.alias_map, f, ensure_ascii=False, indent=2)

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump([asdict(x) for x in self.local_index], f, ensure_ascii=False, indent=2)

        return {"alias_map": alias_path, "local_index": index_path}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build alias map for local BG IDs (tools/ci path)")
    parser.add_argument("--docs-root", type=str, default="docs")
    parser.add_argument("--out-dir", type=str, default="artifacts/indexing")
    parser.add_argument("--lint-report", type=str, default="artifacts/logs/bg_alias_resolver.lint.json")
    args = parser.parse_args()

    resolver = AliasResolver(args.docs_root)
    resolver.scan_docs()

    # Lint all docs for satisfies->derives_from suggestion
    downgrade_suggestions = {}
    for root, _dirs, files in os.walk(args.docs_root):
        for fn in files:
            if not fn.lower().endswith(".md"):
                continue
            path = os.path.join(root, fn)
            text = resolver._read_text(path)
            fm_text, _body = resolver._split_fm(text)
            sug = resolver.downgrade_bg_satisfies(fm_text)
            if sug:
                rel_path = os.path.relpath(path, args.docs_root)
                downgrade_suggestions[rel_path] = sug

    # Write outputs
    written = resolver.write_outputs(args.out_dir)

    os.makedirs(os.path.dirname(args.lint_report), exist_ok=True)
    with open(args.lint_report, "w", encoding="utf-8") as f:
        json.dump(downgrade_suggestions, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "written": written,
        "lint_suggestions": args.lint_report,
        "count_local_bgs": len(resolver.local_index),
        "count_aliases": len(resolver.alias_map),
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
