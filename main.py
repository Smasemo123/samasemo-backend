from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import subprocess
import tempfile
import os
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Sama Music Remover"
    }

@app.post("/remove")
async def remove_music(file: UploadFile = File(...)):
    work = tempfile.mkdtemp(prefix="sama_")

    safe_name = os.path.basename(file.filename or "audio.mp4")
    input_name = f"{uuid.uuid4()}_{safe_name}"
    input_path = os.path.join(work, input_name)

    with open(input_path, "wb") as f:
        f.write(await file.read())

    subprocess.run(
        [
            "python",
            "-m",
            "demucs.separate",
            "-n",
            "htdemucs",
            "--two-stems=vocals",
            "-o",
            work,
            input_path,
        ],
        check=True,
    )

    base = os.path.splitext(input_name)[0]

    result = os.path.join(
        work,
        "htdemucs",
        base,
        "vocals.wav",
    )

    if not os.path.isfile(result):
        raise RuntimeError(
            f"Demucs did not create the output file: {result}"
        )

    return FileResponse(
        result,
        media_type="audio/wav",
        filename="sama_instrumental.wav",
    )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
