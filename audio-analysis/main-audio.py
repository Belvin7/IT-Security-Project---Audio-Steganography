import subprocess
import json
import os
from tabulate import tabulate
import hashlib

def run_ffprobe(file_path):
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries",
        "format=filename,format_name,format_long_name,duration,size,bit_rate,format_tags=encoder,"
        "stream=index,codec_name,codec_long_name,channels,channel_layout,sample_rate",
        "-show_streams",
        "-of", "json", file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return json.loads(result.stdout)

def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_info(data):
    stream = data['streams'][0]
    format_info = data['format']
    
    duration = float(format_info.get('duration', 0))
    sample_rate = int(stream.get('sample_rate', 0))
    num_samples = int(duration * sample_rate) if duration and sample_rate else "N/A"

    return [
        ["File", format_info.get("filename")],
        ["Format", format_info.get("format_long_name")],
        ["Codec", stream.get("codec_long_name")],
        ["Channels", stream.get("channels")],
        ["Channel Layout", stream.get("channel_layout")],
        ["Sample Rate", sample_rate],
        ["Bit Rate", format_info.get("bit_rate")],
        ["Duration (s)", duration],
        ["Number of Samples", num_samples],
        ["Writing Library", format_info.get("tags", {}).get("encoder", "Unknown")],
        ["SHA256", calculate_sha256(format_info.get("filename"))]
    ]

def main():
    file_path = input("Enter path to MP3 file: ").strip()

    if not os.path.isfile(file_path):
        print("Invalid file path.")
        return

    metadata = run_ffprobe(file_path)
    info_table = extract_info(metadata)

    print("\nAudio File Analysis:\n")
    print(tabulate(info_table, headers=["Property", "Value"], tablefmt="fancy_grid"))

if __name__ == "__main__":
    main()
