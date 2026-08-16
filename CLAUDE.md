# CLAUDE.md — 論文リーディング

修士論文（KAKENデータによるアカデミアの男女の生産性格差）のための論文要約プロジェクト。要約は夜間にClaude Desktopのスケジュール済みタスクが作り、Claude Codeはその後始末と整備を担当する。

規定の正本は`README.md`。手順・粒度・書式はそちらを読む。このファイルは、Claude Codeに口頭で頼まれる定型作業の対応表。

## セッション開始時にBibTeXの警告が出たら

`.claude/settings.json`のSessionStartフックが`scripts/check_bibtex.py`を走らせる。「BibTeXが空でDOIあり（埋められる）」または「年の相違」が報告されたら、依頼を待たずに下の手順で埋め、結果を報告する。「対応の要る項目なし」なら何もしない。

「DOIなし（埋められない）」だけの場合も何もしない。掲載版のDOIが判明するまで待つのが正しい状態で、手で組み立ててはいけない。

## 「bibtexを埋めて」と言われたら

夜間バッチの実行環境（Claude Desktop）はプロキシに阻まれて doi.org と api.crossref.org へ到達できないため、新規要約の`### BibTeX`は「取得できず」の注記つきで空のまま残る。Claude Code側はネットワークに到達できるので、次を実行して埋める。

```bash
cd ~/Claude/Projects/paper_reading
python3 scripts/backfill_bibtex.py          # 対象と差分を表示するだけ
python3 scripts/backfill_bibtex.py --apply  # 実際に書き換える
```

- 対象は「取得できず」の注記があるか、`@`エントリを持たない要約に限られる。本文には触れない
- 実行後に次の3点を確認して報告する
  - 取得した`year`が本文の「出版年」やファイル名の年と食い違っていないか（doi.orgは先行公開年を返すことがある。誌面の巻号年が正しいので、食い違えばBibTeXの側を直し、理由を`### BibTeX`の直前に1行書く）
  - 引用キーが刊行年と揃っているか。またアクセント記号が落ちていないか（例：Liénard → `Li_nard_2018`。ファイル名の綴りに直す）
  - 全要約がBibTeXを持つか

同じ言い方の例：「bibtex取れてないのを埋めて」「要約のbibtexお願い」「バッチが取れなかった分」。

なおこの作業は毎朝6:23にlaunchdが無人で実行している（`scripts/bibtex_job.sh`。詳細は`README.md`の「BibTeX補完の自動実行（launchd）」）。日中に頼まれたときは、すでに済んでいることがある。結果は`tail -40 ~/Library/Logs/paper-reading-bibtex.log`で見られる。

## 「キューを整理して」と言われたら

`要約キュー.md`は夜間バッチが毎回読むので、肥大させない。メモは1行、所見の正本は`論文要約/`配下の要約md、履歴は`処理ログ.md`。詳細は`README.md`の「夜間バッチの手順」。

## Claude Codeが触ってよいもの

`論文要約/`・`要約キュー.md`・`処理ログ.md`・`README.md`・`scripts/`・`夜間バッチ指示.md`。PDFは移動のみで、削除・リネームはしない。

## 関連プロジェクト

`~/Claude/Projects/KAKEN`（修論本体）。要約の引用キーはそちらの`reference.bib`と揃える。食い違いを見つけたらKAKEN側の`TASKS.md`を確認してから直す。
