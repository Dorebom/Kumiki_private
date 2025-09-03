
import textwrap, json
from tools.ci.bg_aliasing import AliasResolver

def test_extract_local_bgs(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    sample = docs / "CR-KMK-00_concept.md"
    sample.write_text(textwrap.dedent("""
    ---
    id: CR-KMK-00
    ---
    # 概要

    **ID: BG-KMK-01** これは背景1
    - ID: BG-KMK-02 これは背景2
    """), encoding="utf-8")

    ar = AliasResolver(str(docs))
    ar.scan_docs()
    assert ar.alias_map["BG-KMK-01"] == "CR-KMK-00#BG-KMK-01"
    assert ar.alias_map["BG-KMK-02"] == "CR-KMK-00#BG-KMK-02"

def test_downgrade_satisfies(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    sample = docs / "CR-KMK-01_req.md"
    sample.write_text(textwrap.dedent("""
    ---
    id: CR-KMK-01
    satisfies: [BG-KMK-01, XYZ-1]
    derives_from: [ABC-2]
    ---
    """), encoding="utf-8")

    text = sample.read_text(encoding="utf-8")
    fm = text.split('---')[1]
    ar = AliasResolver(str(docs))
    sug = ar.downgrade_bg_satisfies(fm)
    assert sug is not None
    assert "BG-KMK-01" in sug["move_to_derives_from"]
    assert "BG-KMK-01" in sug["derives_from_after"]
    assert "BG-KMK-01" not in sug["satisfies_after"]
