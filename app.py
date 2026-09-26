from flask import Flask, request, send_file
from flask_cors import CORS
import os
import subprocess
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return {
        "status": "ok",
        "service": "Samasemo No Music"
    }


@app.route("/remove", methods=["POST"])
def remove():
    if "video" not in request.files:
        return "No video uploaded", 400

    video = request.files["video"]

    if not video.filename:
        return "Please choose a video", 400

    safe_name = os.path.basename(video.filename)
    video_name = os.path.splitext(safe_name)[0]

    unique_id = uuid.uuid4().hex
    input_filename = f"{unique_id}_{safe_name}"
    input_path = os.path.join(UPLOAD_FOLDER, input_filename)

    video.save(input_path)

    subprocess.run([
        "demucs",
        "--two-stems=vocals",
        "-o",
        OUTPUT_FOLDER,
        input_path
    ], check=True)

    base_name = os.path.splitext(input_filename)[0]

    audio_path = os.path.join(
        OUTPUT_FOLDER,
        "htdemucs",
        base_name,
        "vocals.wav"
    )

    if not os.path.exists(audio_path):
        return "Vocals file was not created", 500

    output_video = os.path.join(
        OUTPUT_FOLDER,
        f"{unique_id}_no_music.mp4"
    )

    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-i", audio_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_video
    ], check=True)

    return send_file(
        output_video,
        as_attachment=True,
        download_name=f"{video_name}_no_music.mp4",
        mimetype="video/mp4"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
