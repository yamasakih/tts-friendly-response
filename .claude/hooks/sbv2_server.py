#!/usr/bin/env python3
"""Style-Bert-VITS2 TTS サーバー

モデルを一度だけロードし、HTTP リクエストでテキストを受け取り音声を返す常駐サーバー。

使い方:
    ~/.claude/sbv2_venv/bin/python .claude/hooks/sbv2_server.py

テスト:
    curl -X POST http://localhost:5588/tts \
        -H 'Content-Type: application/json' \
        -d '{"text": "こんにちは"}' \
        --output test.wav
    afplay test.wav
"""

import io
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import numpy as np
import soundfile as sf
from style_bert_vits2.constants import Languages
from style_bert_vits2.nlp import bert_models
from style_bert_vits2.tts_model import TTSModel

HOST = "127.0.0.1"
PORT = 5588

MODEL_DIR = Path.home() / ".claude" / "sbv2_models" / "jvnv-F2-jp"
MODEL_PATH = MODEL_DIR / "jvnv-F2_e166_s20000.safetensors"
CONFIG_PATH = MODEL_DIR / "config.json"
STYLE_VEC_PATH = MODEL_DIR / "style_vectors.npy"

# 日本語 BERT モデル（Hugging Face リポジトリ名）
JP_BERT_REPO = "ku-nlp/deberta-v2-large-japanese-char-wwm"


def load_model() -> TTSModel:
    print("Loading JP BERT tokenizer and model ...")
    bert_models.load_tokenizer(Languages.JP, pretrained_model_name_or_path=JP_BERT_REPO)
    bert_models.load_model(Languages.JP, pretrained_model_name_or_path=JP_BERT_REPO).float()
    print("JP BERT loaded.")

    print(f"Loading TTS model from {MODEL_DIR} ...")
    model = TTSModel(
        model_path=MODEL_PATH,
        config_path=CONFIG_PATH,
        style_vec_path=STYLE_VEC_PATH,
        device="cpu",
    )
    model.load()
    print("TTS model loaded successfully.")
    return model


# グローバルにモデルを保持
tts_model: TTSModel


class TTSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/tts":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body)

        text = data.get("text", "")
        if not text:
            self.send_error(400, "text is required")
            return

        language = data.get("language", "JP")
        style = data.get("style", "Neutral")
        style_weight = data.get("style_weight", 1.0)

        sr, audio = tts_model.infer(
            text=text,
            language=language,
            speaker_id=0,
            style=style,
            style_weight=style_weight,
        )

        buf = io.BytesIO()
        sf.write(buf, audio, sr, format="WAV")
        wav_bytes = buf.getvalue()

        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(wav_bytes)))
        self.end_headers()
        self.wfile.write(wav_bytes)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        self.send_error(404)

    def log_message(self, format, *args):
        print(f"[TTS] {args[0]}")


def main():
    global tts_model
    tts_model = load_model()

    server = HTTPServer((HOST, PORT), TTSHandler)
    print(f"TTS server listening on http://{HOST}:{PORT}")
    print("  POST /tts   - Text to Speech")
    print("  GET  /health - Health check")
    server.serve_forever()


if __name__ == "__main__":
    main()
