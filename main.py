from flask import Flask, request, jsonify
import yt_dlp
from openai import OpenAI
import os
import tempfile

app = Flask(__name__)
client = OpenAI()  # OPENAI_API_KEY は環境変数から自動で読み込み

@app.route("/")
def index():
    return """
    <html>
    <body style="font-family: sans-serif; max-width: 800px; margin: 20px auto;">
        <h2>TikTok 文字起こしツール（自分専用）</h2>
        <p>TikTok のURLか動画のURLを貼って「文字起こし」を押してください。</p>
        <input id="url" style="width: 100%; padding: 8px;" placeholder="https://vt.tiktok.com/…">
        <button onclick="run()" style="padding: 10px 16px; margin-top: 10px;">文字起こし</button>
        <pre id="result" style="white-space: pre-wrap; margin-top: 20px; border: 1px solid #ccc; padding: 10px;"></pre>

        <script>
            async function run() {
                const url = document.getElementById("url").value;
                const result = document.getElementById("result");
                result.innerText = "処理中…";

                const res = await fetch("/transcribe", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url })
                });

                const data = await res.json();
                if (data.text) {
                    result.innerText = data.text;
                } else {
                    result.innerText = "エラー: " + (data.error || "不明なエラー");
                }
            }
        </script>
    </body>
    </html>
    """

@app.route("/transcribe", methods=["POST"])
def transcribe():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL が指定されていません"}), 400

    try:
        # 一時ディレクトリに音声をダウンロード
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "%(id)s.%(ext)s")

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_path,
                "quiet": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                audio_path = ydl.prepare_filename(info)

            # Whisper API で文字起こし
            with open(audio_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=f,
                    language="ja"  # 日本語として扱う
                )

            return jsonify({"text": transcript.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Render では gunicorn main:app で起動するので、以下はローカルデバッグ用
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
