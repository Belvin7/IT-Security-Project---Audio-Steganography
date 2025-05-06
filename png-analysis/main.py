import argparse
import os
import sys
import json
import csv
import hashlib
from io import BytesIO
import threading
import webbrowser
import http.server
import socketserver

import cv2
from kaitaistruct import KaitaiStream
from png import Png


### ────────────────────── Argument Parsing ────────────────────── ###
def parse_args():
    parser = argparse.ArgumentParser(description="Sherloq-compatible PNG forensic analyzer.")
    parser.add_argument("files", nargs="+", help="Paths to one or more PNG files")

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", help="Output as JSON")
    output_group.add_argument("--csv", action="store_true", help="Output as CSV")
    output_group.add_argument("--pretty", action="store_true", help="Pretty printed table view")
    output_group.add_argument("--serve", action="store_true", help="Serve HTML report via localhost (default)")

    return parser.parse_args()


### ────────────────────── Core File Analyzer ────────────────────── ###
def analyze_file(filepath):
    result = {"path": filepath}
    try:
        data = read_file_binary(filepath)
        png = parse_png(data)
        metadata = extract_png_metadata(png, filepath, data)
        hashes = compute_image_hashes(filepath)

        result.update(metadata)
        result.update(hashes)

    except Exception as e:
        result["Error"] = str(e)

    return result


def read_file_binary(filepath):
    with open(filepath, "rb") as f:
        return f.read()


def parse_png(data):
    return Png(KaitaiStream(BytesIO(data)))


def extract_png_metadata(png, filepath, data):
    chunk_counts = {}
    for chunk in png.chunks:
        chunk_counts[chunk.type] = chunk_counts.get(chunk.type, 0) + 1

    sbit = next((c.body.hex() for c in png.chunks if c.type == "sBIT"), None)

    metadata = {
        "Magic bytes": " ".join(f"{b:02X}" for b in png.magic),
        "Image width": png.ihdr.width,
        "Image height": png.ihdr.height,
        "Megapixel": round((png.ihdr.width * png.ihdr.height) / 1_000_000, 4),
        "Bit depth": png.ihdr.bit_depth,
        "Color type": png.ihdr.color_type.name,
        "Compression method": png.ihdr.compression_method,
        "Filter method": png.ihdr.filter_method,
        "Interlace method": png.ihdr.interlace_method,
        "File size": format_filesize(os.path.getsize(filepath)),
        "SHA-256": hashlib.sha256(data).hexdigest(),
        "Chunks present": ", ".join(chunk.type for chunk in png.chunks),
        "Quantity per chunk": ", ".join(f"{k}: {v}" for k, v in chunk_counts.items()),
    }

    if sbit:
        metadata["Significant bits (sBIT)"] = sbit

    return metadata


def compute_image_hashes(filepath):
    image_cv = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
    if image_cv is None:
        raise Exception("OpenCV could not read the image.")

    hash_fns = {
        "Average": cv2.img_hash.averageHash,
        "Block Mean": cv2.img_hash.blockMeanHash,
        "Color Moments": cv2.img_hash.colorMomentHash,
        "Marr-Hildreth": cv2.img_hash.marrHildrethHash,
        "Perceptual": cv2.img_hash.pHash,
        "Radial Variance": cv2.img_hash.radialVarianceHash,
    }

    return {
        k: "[" + " ".join(map(str, fn(image_cv)[0])) + "]"
        for k, fn in hash_fns.items()
    }


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
    from tabulate import tabulate
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
        "<h2>PNG Analysis Report</h2>",
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
