#!/usr/bin/env python3
"""要約mdのBibTeXが空になっていないか検査する。書き換えはしない。

用途は2つ。
1. Claude CodeのSessionStartフックから呼ばれ、空があればその場で知らせる
2. 夜間バッチが実行の最後に自分の結果を確かめる

出力：空が0件なら1行だけ。1件以上あれば、ファイル名と埋められるかどうかを列挙する。
終了コードは常に0（フックを失敗させないため）。
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIRS = [ROOT / "論文要約", ROOT / "論文要約" / "WebDB用"]
SECTION_RE = re.compile(r"(?m)^### BibTeX[ \t]*\n(.*?)(?=^## |\Z)", re.S)
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")


def main():
    empty_with_doi, empty_no_doi, year_gaps = [], [], []
    total = 0

    for d in DIRS:
        for p in sorted(d.glob("*.md")):
            if p.name == "テンプレート.md":
                continue
            total += 1
            text = p.read_text(encoding="utf-8")
            sec = SECTION_RE.search(text)
            body = sec.group(1) if sec else ""

            if not re.search(r"(?m)^@\w+\{", body):
                doi_line = re.search(r"^-\s*DOI[^\n]*$", text, flags=re.M)
                has_doi = bool(doi_line and DOI_RE.search(doi_line.group(0)))
                (empty_with_doi if has_doi else empty_no_doi).append(p.name)
                continue

            yb = re.search(r"year\s*=\s*\{?(\d{4})", body)
            ys = re.search(r"(?m)^-\s*出版年[：:]\s*(\d{4})", text)
            yf = re.match(r"(\d{4})_", p.name)
            years = {m.group(1) for m in (yb, ys, yf) if m}
            if len(years) > 1:
                year_gaps.append(f"{p.name}（{'・'.join(sorted(years))}）")

    # 対応が要るのは、埋められる空と年の相違だけ。DOIのない空は待つしかないので警告にしない
    if not empty_with_doi and not year_gaps:
        tail = f"（DOIがなく埋められない要約{len(empty_no_doi)}件は待機中）" if empty_no_doi else ""
        print(f"[paper_reading] 要約{total}本のBibTeXに対応の要る項目なし{tail}")
        return 0

    print(f"[paper_reading] 要約{total}本を検査した。対応が要る項目がある")
    if empty_with_doi:
        print(f"  BibTeXが空でDOIあり（埋められる）: {len(empty_with_doi)}件")
        for n in empty_with_doi:
            print(f"    - {n}")
        print("    → python3 scripts/backfill_bibtex.py --apply で埋まる")
    if empty_no_doi:
        print(f"  BibTeXが空でDOIなし（埋められない）: {len(empty_no_doi)}件")
        for n in empty_no_doi:
            print(f"    - {n}")
        print("    → 掲載版のDOIが判明するまで空のままにする。手で組み立てない")
    if year_gaps:
        print(f"  年の相違（BibTeX・出版年・ファイル名）: {len(year_gaps)}件")
        for n in year_gaps:
            print(f"    - {n}")
        print("    → 誌面の巻号年が正しい。BibTeX側を直して理由を1行書く")
    return 0


if __name__ == "__main__":
    sys.exit(main())
