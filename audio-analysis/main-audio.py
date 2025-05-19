import argparse
import csv
import glob
import hashlib
import http.server
import json
import os
import socketserver
import subprocess
import sys
import threading
import webbrowser
from tabulate import tabulate


### ────────────────────── Argument Parsing ────────────────────── ###
def parse_args():
    parser = argparse.ArgumentParser(description="Audio forensic analyzer using ffprobe.")
    parser.add_argument("files", nargs="+", help="Paths to one or more audio files (supports wildcards)")

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", help="Output as JSON")
    output_group.add_argument("--csv", action="store_true", help="Output as CSV")
    output_group.add_argument("--pretty", action="store_true", help="Pretty printed table view")
    output_group.add_argument("--serve", action="store_true", help="Serve HTML report via localhost (default)")

    args = parser.parse_args()
    expanded_files = []
    for pattern in args.files:
        expanded_files.extend(glob.glob(pattern))
    args.files = expanded_files
    return args


### ────────────────────── Core File Analyzer ────────────────────── ###
def analyze_file(filepath):
    result = {"File": filepath}
    try:
        ffprobe_data = run_ffprobe(filepath)
        stream = ffprobe_data["streams"][0]
        fmt = ffprobe_data["format"]

        duration = float(fmt.get("duration", 0))
        sample_rate = int(stream.get("sample_rate", 0))
        num_samples = int(duration * sample_rate) if duration and sample_rate else "N/A"

        result.update({
            "Size": format_filesize(os.path.getsize(filepath)),
            "Duration (s)": duration,
            "Number of Samples": num_samples,
            "Format": fmt.get("format_long_name", "Unknown"),
            "Channels": stream.get("channels", "Unknown"),
            "SHA256": compute_sha256(filepath),
            "Bit Rate": fmt.get("bit_rate", "Unknown"),
            "Writing Library": fmt.get("tags", {}).get("encoder", "Unknown"),
            "Channel Layout": stream.get("channel_layout", "Unknown"),
            #"Codec": stream.get("codec_long_name", "Unknown"),
            #"Sample Rate": sample_rate,
            
        })

    except Exception as e:
        result["Error"] = str(e)

    return result


def run_ffprobe(filepath):
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries",
        "format=filename,format_name,format_long_name,duration,size,bit_rate,format_tags=encoder,"
        "stream=index,codec_name,codec_long_name,channels,channel_layout,sample_rate",
        "-show_streams",
        "-of", "json", filepath
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return json.loads(result.stdout)


def compute_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(block)
    return sha256_hash.hexdigest()


def format_filesize(size_bytes):
    return f"{size_bytes} bytes ({round(size_bytes / 1024, 1)} KB)"


### ────────────────────── Output Formatters ────────────────────── ###
def get_all_keys(results):
    seen, keys = set(), []
    for r in results:
        for k in r:
            if k not in seen:
                seen.add(k)
                keys.append(k)
    return keys


def output_json(results):
    print(json.dumps(results, indent=2))


def output_csv(results):
    headers = get_all_keys(results)
    writer = csv.DictWriter(sys.stdout, fieldnames=headers)
    writer.writeheader()
    for row in results:
        writer.writerow({k: row.get(k, "") for k in headers})


def output_pretty(results):
    headers = get_all_keys(results)
    rows = [[r.get(k, "") for k in headers] for r in results]
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))


def serve_html(results, port=8000):
    headers = get_all_keys(results)

    def escape(val):
        return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<style>",
        "body { font-family: sans-serif; padding: 1em; margin: 0; }",
        ".scroll-wrap { overflow-x: auto; padding-bottom: 0.5em; }",
        "table { border-collapse: collapse; width: max-content; min-width: 100%; }",
        "th, td { border: 1px solid #ccc; padding: 6px; font-family: monospace; white-space: nowrap; }",
        "td:hover { background: #eef; cursor: pointer; }",
        "</style>",
        "<script>",
        "function copyText(e) {",
        "  const text = e.target.innerText;",
        "  navigator.clipboard.writeText(text);",
        "  e.target.style.backgroundColor = '#cfc';",
        "  setTimeout(() => e.target.style.backgroundColor = '', 300);",
        "}",
        "</script></head><body>",
        "<h2>Audio Analysis Report</h2>",
        "<div class='scroll-wrap'><table><thead><tr>",
    ]

    html.extend(f"<th>{escape(k)}</th>" for k in headers)
    html.append("</tr></thead><tbody>")
    for row in results:
        html.append("<tr>")
        html.extend(f"<td onclick='copyText(event)'>{escape(row.get(k, ''))}</td>" for k in headers)
        html.append("</tr>")
    html.extend(["</tbody></table></div></body></html>"])
    content = "\n".join(html).encode("utf-8")

    class ReportHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *args):
            pass  # Suppress logging

    try:
        with socketserver.TCPServer(("", port), ReportHandler) as httpd:
            url = f"http://localhost:{port}"
            print(f"[✓] Serving report at {url} (Press Ctrl+C to stop)")
            threading.Timer(1, lambda: webbrowser.open(url)).start()
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n[✓] Server stopped cleanly.")
    except OSError:
        print(f"[!] Port {port} is in use. Try a different one.")


### ─────────────────────────── Main ─────────────────────────── ###
def main():
    args = parse_args()
    results = [analyze_file(path) for path in args.files]

    if args.json:
        output_json(results)
    elif args.csv:
        output_csv(results)
    elif args.pretty:
        output_pretty(results)
    else:
        serve_html(results)


if __name__ == "__main__":
    main()
