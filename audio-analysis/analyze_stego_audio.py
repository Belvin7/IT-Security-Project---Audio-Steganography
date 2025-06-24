from flask import Flask, render_template_string
import hashlib
import os
import subprocess
import sys

app = Flask(__name__)


def sha256sum(filename):
    h = hashlib.sha256()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def recompress_audio(input_file, output_file, codec, bitrate="128k"):
    cmd = [
        'ffmpeg',
        '-y',
        '-i', input_file,
        '-c:a', codec,
        '-b:a', bitrate,
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def file_size(path):
    return os.path.getsize(path)


def analyze(stego_path, cover_path):
    size_cover = file_size(cover_path)
    size_stego = file_size(stego_path)
    ratio = size_stego / size_cover if size_cover else float('inf')

    sha_cover = sha256sum(cover_path)
    sha_stego = sha256sum(stego_path)

    # Recompress using LAME
    cover_lame = "temp_cover_lame.mp3"
    stego_lame = f"temp_{os.path.basename(stego_path)}_lame.mp3"
    recompress_audio(cover_path, cover_lame, "libmp3lame")
    recompress_audio(stego_path, stego_lame, "libmp3lame")
    sha_cover_lame = sha256sum(cover_lame)
    sha_stego_lame = sha256sum(stego_lame)
    size_cover_lame = file_size(cover_lame)
    size_stego_lame = file_size(stego_lame)

    # Recompress using Opus
    cover_opus = "temp_cover_opus.opus"
    stego_opus = f"temp_{os.path.basename(stego_path)}_opus.opus"
    recompress_audio(cover_path, cover_opus, "libopus", "96k")
    recompress_audio(stego_path, stego_opus, "libopus", "96k")
    size_cover_opus = file_size(cover_opus)
    size_stego_opus = file_size(stego_opus)

    # Clean up temp files
    for f in [cover_lame, stego_lame, cover_opus, stego_opus]:
        os.remove(f)

    # Ratios & reductions
    ratio_cover_opus = size_cover / ((size_cover + size_cover_opus) / 2) if (size_cover + size_cover_opus) else 0
    ratio_cover_lame = size_cover / ((size_cover + size_cover_lame) / 2) if (size_cover + size_cover_lame) else 0
    ratio_stego_opus = size_stego / ((size_stego + size_stego_opus) / 2) if (size_stego + size_stego_opus) else 0
    ratio_stego_lame = size_stego / ((size_stego + size_stego_lame) / 2) if (size_stego + size_stego_lame) else 0

    reduction_lame = (size_stego - size_stego_lame) / size_stego if size_stego else 0
    reduction_opus = (size_stego - size_stego_opus) / size_stego if size_stego else 0

    return {
        "Stego File": os.path.basename(stego_path),
        "Cover Size": size_cover,
        "Stego Size": size_stego,
        "SHA256 Cover": sha_cover,
        "SHA256 Stego": sha_stego,
        "Stego/Cover Ratio": f"{ratio:.4f}",
        "SHA256 Stego Recomp.": sha_stego_lame,
        "SHA256 Cover Recomp.": sha_cover_lame,
        "Recomp. Opus Size": size_stego_opus,
        "Recomp. LAME Size": size_stego_lame,
        "Ratio for Cover for Opus": f"{ratio_cover_opus:.4f}",
        "Ratio for Cover for LAME": f"{ratio_cover_lame:.4f}",
        "Ratio of Stego for Opus": f"{ratio_stego_opus:.4f}",
        "Ratio of Stego for LAME": f"{ratio_stego_lame:.4f}",
        "Durchschnittsreduktion for LAME": f"{reduction_lame:.2%}",
        "Durchschnittsreduktion for Opus": f"{reduction_opus:.2%}",
    }


@app.route("/")
def show_table():
    if len(sys.argv) != 3:
        return "<h3>Usage: python app.py cover.mp3 stego_folder/</h3>"

    cover_path = sys.argv[1]
    stego_folder = sys.argv[2]

    if not os.path.isfile(cover_path):
        return f"<h3>Error: {cover_path} is not a valid file</h3>"
    if not os.path.isdir(stego_folder):
        return f"<h3>Error: {stego_folder} is not a valid folder</h3>"

    stego_files = [
        os.path.join(stego_folder, f)
        for f in os.listdir(stego_folder)
        if f.lower().endswith(".mp3")
    ]

    if not stego_files:
        return "<h3>No .mp3 files found in stego folder.</h3>"

    rows = [analyze(stego, cover_path) for stego in stego_files]
    headers = list(rows[0].keys())

    html_template = """
    <html>
    <head>
        <title>Stego Analysis Table</title>
        <style>
            body { font-family: Arial; margin: 2em; }
            table { border-collapse: collapse; width: 100%; font-size: 14px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
            th { background-color: #f4f4f4; }
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
    </head>
    <body>
        <h2>📊 Stego Analysis Table</h2>
        <p><strong>Cover File:</strong> {{ cover_file }}</p>
        <table>
            <thead>
                <tr>{% for h in headers %}<th>{{ h }}</th>{% endfor %}</tr>
            </thead>
            <tbody>
                {% for row in rows %}
                <tr>{% for val in row.values() %}<td>{{ val }}</td>{% endfor %}</tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """
    return render_template_string(html_template, rows=rows, headers=headers, cover_file=os.path.basename(cover_path))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python app.py cover.mp3 stego_folder/")
    else:
        app.run(debug=True)
