import os
import tempfile
import subprocess
import sys
import requests
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
YT_DLP = os.path.join(SCRIPT_DIR, 'yt-dlp.exe' if sys.platform == 'win32' else 'yt-dlp')

def download_ytdlp():
    try:
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/"
        url += "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp"

        print(f"Downloading yt-dlp from {url}...")
        response = requests.get(url, stream=True)
        with open(YT_DLP, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if sys.platform != "win32":
            os.chmod(YT_DLP, 0o755)

        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def clean_vtt(raw_text):
    lines = raw_text.splitlines()
    clean_lines = []

    for line in lines:
        line = line.strip()

        # Skip timestamps and formatting lines
        if re.match(r"^\d\d:\d\d:\d\d\.\d\d\d", line):
            continue
        if "-->" in line:
            continue
        if line.startswith("NOTE") or line.startswith("WEBVTT"):
            continue
        if line == "":
            continue

        # Remove any <tags> or &nbsp; type stuff
        line = re.sub(r"<.*?>", "", line)
        line = re.sub(r"&[^ ]+;", "", line)

        clean_lines.append(line)

    return "\n".join(clean_lines)

def get_subtitles(video_url, language='en'):
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            cmd = [
                YT_DLP,
                '--skip-download',
                '--write-subs',
                '--write-auto-subs',
                '--sub-lang', language,
                '--sub-format', 'vtt',
                '--output', os.path.join(tmp_dir, 'subtitle'),
                video_url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return None, f"yt-dlp error: {result.stderr}"

            subtitle_files = [f for f in os.listdir(tmp_dir) if f.endswith('.vtt')]
            if not subtitle_files:
                return None, "No subtitles found."

            file_path = os.path.join(tmp_dir, subtitle_files[0])
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
                cleaned = clean_vtt(raw_text)
                return cleaned, None

        except Exception as e:
            return None, f"Unexpected error: {e}"

@app.route('/api/subtitles', methods=['GET'])
def get_subs():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({'error': 'Missing URL parameter'}), 400
    
    subtitles, error = get_subtitles(video_url)

    if error:
        return jsonify({'error': error}), 500

    return jsonify({'subtitles': subtitles})

if __name__ == '__main__':
    if not os.path.exists(YT_DLP):
        print("yt-dlp not found. Downloading...")
        if not download_ytdlp():
            print("Manual download required.")
            sys.exit(1)

    print("Server running at http://127.0.0.1:5000/api/subtitles?url=YOUTUBE_URL")
    app.run(debug=True)