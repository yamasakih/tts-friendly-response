# tts-friendly-response

Claude Code の応答を [Style-Bert-VITS2](https://github.com/litagin02/Style-Bert-VITS2) で自動的に日本語音声読み上げするスキル + フック一式。

## 特徴

- Claude Code の応答完了後に自動で音声が再生される
- TTS サーバーが起動していない場合はフックが静かにスキップされるため、影響なし
- 英語の技術用語をカタカナで応答するスキルにより、TTS の読み上げが自然になる

## 前提条件

- macOS（`afplay` コマンドを使用）
- `jq` がインストール済み（`brew install jq`）
- Python 3.13 が `/opt/homebrew/bin/python3.13` にある

## セットアップ

### 1. このリポジトリの `.claude/` をプロジェクトにコピー

```bash
cp -r .claude/ <your-project>/.claude/
```

スキルをグローバルに使う場合:

```bash
cp -r .claude/skills/tts-friendly-response/ ~/.claude/skills/tts-friendly-response/
```

### 2. venv 作成とパッケージインストール

```bash
/opt/homebrew/bin/python3.13 -m venv ~/.claude/sbv2_venv
CMAKE_POLICY_VERSION_MINIMUM=3.5 ~/.claude/sbv2_venv/bin/pip install style-bert-vits2 soundfile
~/.claude/sbv2_venv/bin/pip install "setuptools<78"
```

### 3. TTS モデルのダウンロード

利用可能なモデル:

| モデル名 | 説明 |
|---|---|
| `jvnv-F1-jp` | 女性話者 1 |
| `jvnv-F2-jp` | 女性話者 2 |
| `jvnv-M1-jp` | 男性話者 1 |
| `jvnv-M2-jp` | 男性話者 2 |

```bash
~/.claude/sbv2_venv/bin/python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='litagin/style_bert_vits2_jvnv',
    allow_patterns=['jvnv-F2-jp/*'],
    local_dir=str(__import__('pathlib').Path.home() / '.claude/sbv2_models')
)
print('Done')
"
```

別のモデルを使う場合は `allow_patterns` と `.claude/hooks/sbv2_server.py` の `MODEL_DIR` / `MODEL_PATH` を変更する。

## 使い方

### TTS サーバーを起動

別ターミナルで以下を実行する（常駐させておく）。

```bash
~/.claude/sbv2_venv/bin/python .claude/hooks/sbv2_server.py
```

初回起動時は BERT モデルのダウンロードが走るため数分かかる。2回目以降はキャッシュから読み込まれる。

### Claude Code を使う

通常通り Claude Code で質問すると、応答完了後に自動で音声が再生される。

## ファイル構成

```
.claude/
├── hooks/
│   ├── sbv2_server.py   # TTS 常駐サーバー（ポート 5588）
│   └── speak.sh         # Stop フックスクリプト
├── skills/
│   └── tts-friendly-response/
│       └── SKILL.md     # TTS フレンドリーな応答スキル
└── settings.json        # Claude Code フック設定
```

グローバルリソース（セットアップ時に作成される）:

```
~/.claude/
├── sbv2_venv/           # Python 仮想環境
└── sbv2_models/
    └── jvnv-F2-jp/      # TTS モデル
```

## 設定

### 読み上げ文字数の上限

`speak.sh` の `MAX_CHARS` を変更する（デフォルト: 200 文字）。

### 音声スタイル

`speak.sh` のリクエストで `style` パラメータを変更できる（デフォルト: `Happy`）:

- `Neutral` — 淡々とした声
- `Happy` — 明るく柔らかい声
- `Sad` — 悲しい声
- `Angry` — 怒った声
- `Fear` — 怯えた声
- `Surprise` — 驚いた声
- `Disgust` — 嫌悪感のある声

`style_weight`（デフォルト: `0.5`）でスタイルの強さを調整できる。

## 動作確認

```bash
# ヘルスチェック
curl http://127.0.0.1:5588/health

# 手動で音声生成・再生
curl -s -X POST http://127.0.0.1:5588/tts \
    -H 'Content-Type: application/json' \
    -d '{"text": "こんにちは", "style": "Happy", "style_weight": 0.5}' \
    --output /tmp/test.wav && afplay /tmp/test.wav
```
