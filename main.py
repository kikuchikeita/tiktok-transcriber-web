from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import whisper
import os
import uvicorn

MODEL_NAME = "medium"
model = whisper.load_model(MODEL_NAME)

app = FastAPI()

class Request(BaseModel):
    url: str

@app.post("/transcribe")
def transcribe_audio(request: Request):
    url = request.url
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(download_dir, "%(id)s.%(ext)s"),
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(info)

        result = model.transcribe(audio_path, language="ja")
        return {"text": result["text"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
