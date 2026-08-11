#!/usr/bin/env python3
"""DOIからBibTeXを取得する。

目的：要約mdの`### BibTeX`が空になるのを防ぐ。

仕組み：doi.org のコンテンツネゴシエーション（Accept: application/x-bibtex）を第1経路、
Crossrefの変換エンドポイントを第2経路として順に試す。doi2bib.org が内部で使っているのは
第1経路と同じもので、同じ結果が返る。doi2bib.org 自体は公開APIを持たない
（/bib/<DOI> は404）ため、HTMLの取得は行わない。

使い方：
    python3 scripts/doi2bib.py 10.1073/pnas.1510159112
    python3 scripts/doi2bib.py 10.1073/pnas.1510159112 10.1126/sciadv.abd1996
    echo "10.2196/49905" | python3 scripts/doi2bib.py -

出力：整形したBibTeXを標準出力へ。取得できなかったDOIは標準エラーへ理由を出し、
標準出力には何も出さない。終了コードは、1件でも失敗すれば1。

注意：取得できなかった場合、要約mdの`### BibTeX`には「取得できず（理由）」と書く。
書誌情報から手で組み立てて埋めない。DOIを持たない和文誌（例：大学評価とIR）は
このスクリプトの対象外で、手で書く。
"""

import re
import sys
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 30
UA = "doi2bib-local/1.0 (paper_reading project; mailto:hellosingapore1982@gmail.com)"


def normalize(doi):
    """URL形式で渡されたDOIを裸のDOIへ戻す。"""
    doi = doi.strip()
    doi = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi)
    if not doi.startswith("10."):
        raise ValueError(f"DOIの形式ではない: {doi}")
    return doi


def get(url, accept):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
        return res.read().decode("utf-8", errors="replace").strip()


def fetch(doi):
    """DOIのBibTeXを1行の文字列で返す。取得できなければ例外を投げる。

    経路を2つ試す。1つ目が落ちても2つ目で取れることがあるため、片方の失敗では諦めない。
    """
    doi = normalize(doi)
    quoted = urllib.parse.quote(doi, safe="/:")
    sources = [
        ("doi.org", "https://doi.org/" + quoted, "application/x-bibtex"),
        (
            "crossref",
            f"https://api.crossref.org/works/{quoted}/transform/application/x-bibtex",
            "application/x-bibtex",
        ),
    ]

    errors = []
    for name, url, accept in sources:
        try:
            body = get(url, accept)
        except Exception as e:  # noqa: BLE001 経路ごとの失敗を集めて最後に報告する
            errors.append(f"{name}={e}")
            continue
        if body.startswith("@"):
            return body
        errors.append(f"{name}=BibTeXが返らなかった（応答{len(body)}文字）")

    raise ValueError("；".join(errors))


def format_bibtex(raw):
    """1行で返るBibTeXをフィールドごとに改行する。値の中のカンマでは折らない。"""
    m = re.match(r"^(@\w+\{[^,]*,)(.*)\}\s*$", raw, flags=re.S)
    if not m:
        return raw
    head, body = m.group(1), m.group(2).strip()
    # 「, 」の直後に「英字＝」が続く位置だけをフィールド境界とみなす
    fields = re.split(r",\s*(?=[A-Za-z_]+\s*=)", body)
    lines = [head]
    for i, f in enumerate(fields):
        f = f.strip().rstrip(",")
        if f:
            lines.append("  " + f + ("," if i < len(fields) - 1 else ""))
    lines.append("}")
    return "\n".join(lines)


def main(argv):
    args = argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2

    dois = []
    for a in args:
        if a == "-":
            dois += [line for line in sys.stdin.read().split() if line]
        else:
            dois.append(a)

    failed = 0
    for doi in dois:
        try:
            print(format_bibtex(fetch(doi)))
            print()
        except urllib.error.HTTPError as e:
            failed += 1
            print(f"取得できず {doi}: HTTP {e.code}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001 タイムアウト・DNS・形式不正をまとめて報告する
            failed += 1
            print(f"取得できず {doi}: {e}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
