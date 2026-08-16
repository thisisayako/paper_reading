#!/bin/bash
# launchd（com.ayako.paper-reading.bibtex）から毎朝呼ばれる。
#
# 夜間バッチ（Claude Desktop）はプロキシに阻まれて doi.org へ到達できず、新規要約の
# BibTeXを空のまま残す。この端末のClaude Codeは到達できるので、朝いちで埋めておく。
#
# 段構え：
#   1. check_bibtex.py（読むだけ）で状態を見る
#   2. 「対応の要る項目なし」なら、Claudeを呼ばずに終了する
#   3. 対応が要るときだけ claude -p を起動し、CLAUDE.mdの手順を実行させる
#
# 手順そのものはここに書かない。CLAUDE.mdの「「bibtexを埋めて」と言われたら」節が正本。
# gitのコミットはしない。書き換えは作業ツリーに残し、朝ユーザーが確かめる。

set -uo pipefail

PROJECT="/Users/ayako/Claude/Projects/paper_reading"
PY="/opt/anaconda3/bin/python3"
CLAUDE="/Users/ayako/.local/bin/claude"
LOG="$HOME/Library/Logs/paper-reading-bibtex.log"

# /opt/homebrew/bin は node のため。プラグインのフックが node を呼ぶので、
# 落とすと claude が SessionEnd で「node: command not found」を吐く
export PATH="/Users/ayako/.local/bin:/opt/homebrew/bin:/opt/anaconda3/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Keychainの認証情報を読むのに要る。launchdは渡してくれるが、素のcronから
# 呼ばれた場合に備えて補う
export USER="${USER:-$(id -un)}"
export LOGNAME="${LOGNAME:-$USER}"

# ログが1MBを超えたら末尾256KBだけ残す。launchdが開いているfdを壊さないよう、
# inodeは差し替えずに中身だけ切り詰める
if [ -f "$LOG" ] && [ "$(stat -f%z "$LOG" 2>/dev/null || echo 0)" -gt 1048576 ]; then
  tail -c 262144 "$LOG" > "$LOG.tmp" 2>/dev/null && cat "$LOG.tmp" > "$LOG" && rm -f "$LOG.tmp"
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S') bibtex_job 開始 ====="

cd "$PROJECT" || { echo "FAIL: プロジェクトへcdできない: $PROJECT"; exit 1; }
[ -x "$PY" ]     || { echo "FAIL: python3が見つからない: $PY"; exit 1; }
[ -x "$CLAUDE" ] || { echo "FAIL: claudeが見つからない: $CLAUDE"; exit 1; }

check="$("$PY" scripts/check_bibtex.py 2>&1)"
echo "$check"

if printf '%s' "$check" | grep -q '対応の要る項目なし'; then
  echo "----- 対応不要。Claudeは起動しない -----"
  exit 0
fi

echo "----- 対応が要る。claude -p を起動する -----"

"$CLAUDE" -p 'BibTeXの補完を実行する。対象プロジェクト: /Users/ayako/Claude/Projects/paper_reading

CLAUDE.md の「「bibtexを埋めて」と言われたら」節に書かれたとおりに実行する。実行するコマンド、実行後に確かめる3点、触ってよいファイルの範囲は、すべてその節に書いてある。このメッセージには手順を書かない。CLAUDE.md の記載が本メッセージと食い違う場合は CLAUDE.md を優先する。

これは無人実行なので、次の2点を守る。
- git の commit・push はしない。書き換えは作業ツリーに残したままにする
- 判断に迷う点（年の相違でどちらが正しいか、DOIのない要約など）は、勝手に決めず未処理のまま報告に挙げる

最後に「書き換えたファイル」「人の判断が要る点」を箇条書きで報告して終了する。CLAUDE.md を読めなかった場合は、何もせずその旨を報告して終了する。' \
  --allowedTools "Read,Grep,Glob,Edit,Bash(python3:*),Bash(git status:*),Bash(git diff:*)" \
  2>&1
rc=$?

echo "===== $(date '+%Y-%m-%d %H:%M:%S') bibtex_job 終了（claude exit=$rc） ====="
exit "$rc"
