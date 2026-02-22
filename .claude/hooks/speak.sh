#!/bin/bash
# Claude Code Stop hook: TTS サーバーに最後の応答を送って音声再生する
#
# stdin から JSON を受け取り、last_assistant_message を抽出して
# TTS サーバーに POST し、afplay で再生する。

set -euo pipefail

TTS_URL="http://127.0.0.1:5588/tts"
MAX_CHARS=200
TMPFILE=$(mktemp /tmp/claude_tts_XXXXXX).wav

cleanup() {
    rm -f "${TMPFILE%.wav}" "$TMPFILE"
}
trap cleanup EXIT

INPUT=$(cat)

# TTS サーバーが起動しているか確認
if ! curl -s --max-time 1 "http://127.0.0.1:5588/health" > /dev/null 2>&1; then
    exit 0
fi

# last_assistant_message を抽出
MESSAGE=$(echo "$INPUT" | jq -r '.last_assistant_message // empty')

if [ -z "$MESSAGE" ]; then
    exit 0
fi

# マークダウン記法やコードブロックを除去し、先頭部分のみ使用
TEXT=$(echo "$MESSAGE" \
    | sed 's/```[^`]*```//g' \
    | sed 's/`[^`]*`//g' \
    | sed 's/\*\*\([^*]*\)\*\*/\1/g' \
    | sed 's/^#\+ //g' \
    | sed 's/^- //g' \
    | sed '/^$/d' \
    | head -c "$MAX_CHARS")

if [ -z "$TEXT" ]; then
    exit 0
fi

# TTS サーバーにリクエスト
PAYLOAD=$(jq -n --arg text "$TEXT" '{"text": $text, "style": "Happy", "style_weight": 0.5}')

curl -s --max-time 25 -X POST "$TTS_URL" \
    -H 'Content-Type: application/json' \
    -d "$PAYLOAD" \
    --output "$TMPFILE" 2>/dev/null

# WAV ファイルが生成されていれば再生
if [ -s "$TMPFILE" ]; then
    afplay "$TMPFILE"
fi
