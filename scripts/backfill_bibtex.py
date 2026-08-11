#!/usr/bin/env python3
"""既存の要約mdの`### BibTeX`を、DOIから取得した正式なBibTeXへ差し替える。

背景：夜間バッチが doi2bib.org の存在しないエンドポイントを叩いて失敗し、書誌情報から
手で組み立てたBibTeXを書いていた（号が欠けるなどの欠落があった）。取得経路を直したため、
既存分をまとめて差し替える。

対象：`### BibTeX`から次の`## `見出しまで。他の行には触れない。

使い方：
    python3 scripts/backfill_bibtex.py            # 差分を表示するだけ（既定）
    python3 scripts/backfill_bibtex.py --apply    # 実際に書き換える

出力：ファイルごとに、取得の成否と、取得したyearが本文の出版年と食い違う場合の警告。
食い違いは自動で直さない。doi.orgは先行公開年を返すことがあり、どちらが正しいかは
PDFを見ないと決められないため。
"""

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from doi2bib import fetch, format_bibtex  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUMMARY_DIRS = [ROOT / "論文要約", ROOT / "論文要約" / "WebDB用"]

# 日本語を含まない範囲でDOIを取る。全角括弧や読点で止める
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
SECTION_RE = re.compile(r"(?m)^### BibTeX[ \t]*\n(.*?)(?=^## |\Z)", re.S)


def find_doi(text):
    """書誌情報のDOI行を優先し、なければBibTeXブロックから拾う。"""
    m = re.search(r"^-\s*DOI[^\n]*$", text, flags=re.M)
    candidates = []
    if m:
        candidates += DOI_RE.findall(m.group(0))
    candidates += DOI_RE.findall(text)
    for c in candidates:
        c = c.rstrip(".,;/")
        if c:
            return c
    return None


def stated_year(text, path):
    m = re.search(r"^-\s*出版年[：:]\s*(\d{4})", text, flags=re.M)
    if m:
        return m.group(1)
    m = re.match(r"(\d{4})_", path.name)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="実際に書き換える")
    ap.add_argument(
        "--all",
        action="store_true",
        help="取得失敗の注記がないファイルも対象にする（既定は注記のあるものだけ）",
    )
    args = ap.parse_args()

    files = []
    for d in SUMMARY_DIRS:
        files += sorted(p for p in d.glob("*.md") if p.name != "テンプレート.md")

    changed = warned = failed = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        sec = SECTION_RE.search(text)
        if not sec:
            print(f"skip  {path.name}: ### BibTeX 節がない")
            continue

        body = sec.group(1)
        # 取得に失敗して手で組み立てた痕跡があるものだけを既定の対象にする
        handmade = bool(re.search(r"取得でき[なず]|doi2bib|構成したもの", body)) or not re.search(
            r"(?m)^@\w+\{", body
        )
        if not handmade and not args.all:
            continue

        doi = find_doi(text)
        if not doi:
            print(f"skip  {path.name}: DOIが見つからない（和文誌などは対象外）")
            continue

        try:
            bib = format_bibtex(fetch(doi))
        except Exception as e:  # noqa: BLE001 1本の失敗で全体を止めない
            failed += 1
            print(f"FAIL  {path.name}: {e}")
            continue

        new_body = "\n```bibtex\n" + bib + "\n```\n\n"
        if body == new_body:
            print(f"same  {path.name}")
            continue

        y_fetched = re.search(r"year=\{?(\d{4})", bib)
        y_stated = stated_year(text, path)
        note = ""
        if y_fetched and y_stated and y_fetched.group(1) != y_stated:
            warned += 1
            note = f"  ← 年の相違 取得={y_fetched.group(1)} 本文={y_stated}"

        label = "手作り" if handmade else "取得済み"
        print(f"{'書換' if args.apply else '差分'}  {path.name}  [{label}→doi.org]{note}")
        changed += 1

        if args.apply:
            path.write_text(text[: sec.start(1)] + new_body + text[sec.end(1) :], encoding="utf-8")

    print(f"\n対象{len(files)}本／{'書換' if args.apply else '要書換'}{changed}／年の相違{warned}／取得失敗{failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
