# Style-Bert-VITS2 による Claude Code 応答読み上げ

Claude Code の応答を Style-Bert-VITS2 で自動的に音声読み上げする仕組み。

## 前提条件

- macOS（`afplay` コマンドを使用）
- `jq` がインストール済み（`brew install jq`）
- Python 3.13 が `/opt/homebrew/bin/python3.13` にある

## セットアップ

初回のみ以下を実行する。

### 1. venv 作成とパッケージインストール

```bash
/opt/homebrew/bin/python3.13 -m venv ~/.claude/sbv2_venv
CMAKE_POLICY_VERSION_MINIMUM=3.5 ~/.claude/sbv2_venv/bin/pip install style-bert-vits2 soundfile
~/.claude/sbv2_venv/bin/pip install "setuptools<78"
```

### 2. TTS モデルのダウンロード

```bash
~/.claude/sbv2_venv/bin/python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='litagin/style_bert_vits2_jvnv',
    allow_patterns=['jvnv-F1-jp/*'],
    local_dir=str(__import__('pathlib').Path.home() / '.claude/sbv2_models')
)
print('Done')
"
```

## 使い方

### TTS サーバーを起動

別ターミナルで以下を実行する（常駐させておく）。

```bash
~/.claude/sbv2_venv/bin/python .claude/hooks/sbv2_server.py
```

初回起動時は BERT モデルのダウンロードが走るため数分かかる。2回目以降はキャッシュから読み込まれる。

起動完了すると以下のように表示される:

```
TTS server listening on http://127.0.0.1:5588
  POST /tts   - Text to Speech
  GET  /health - Health check
```

### Claude Code を使う

通常通り Claude Code で質問すると、応答完了後に自動で音声が再生される。

サーバーが起動していない場合はフックが静かにスキップされるため、影響はない。

## ファイル構成

```
.claude/
├── hooks/
│   ├── sbv2_server.py   # TTS 常駐サーバー（ポート 5588）
│   ├── speak.sh         # Stop フックスクリプト
│   └── README.md        # このファイル
└── settings.json        # Claude Code フック設定
```

グローバルリソース:

```
~/.claude/
├── sbv2_venv/           # Python 仮想環境
└── sbv2_models/
    └── jvnv-F1-jp/      # TTS モデル
```

## 動作確認

```bash
# ヘルスチェック
curl http://127.0.0.1:5588/health

# 手動で音声生成・再生
curl -s -X POST http://127.0.0.1:5588/tts \
    -H 'Content-Type: application/json' \
    -d '{"text": "こんにちは"}' \
    --output /tmp/test.wav && afplay /tmp/test.wav
```

## 設定

### 読み上げ文字数の上限

`speak.sh` の `MAX_CHARS` を変更する（デフォルト: 200文字）。

### 音声スタイル

TTS サーバーへのリクエストで `style` パラメータを指定できる:

- `Neutral`（デフォルト）
- `Happy`
- `Sad`
- `Angry`
- `Fear`
- `Surprise`
- `Disgust`
