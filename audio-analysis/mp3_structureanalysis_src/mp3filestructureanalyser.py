#################### License #########################################
#
# BSD-3-Clause / “New BSD License”
#
# Copyright 2023 Otto-von-Guericke University Magdeburg, Advanced Multimedia and Security Lab (AMSL), Christian Kraetzer, Bernhard Birnbaum
# All rights reserved
#
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  
#
#
#######################################################################

import argparse
import ast
import json
from pathlib import Path
import sys

from alive_progress import alive_bar
from decoder.ID3_Parser import ID3, ID3v1
from decoder.MP3_Parser import MP3Parser
import mp3utils
from texttable import Texttable

parser = argparse.ArgumentParser(
    prog="./mp3filestructureanalyser",
    description="extracts a description of the structure of the analysed mp3 file",
    epilog="MP3 decoder by tomershay100, but heavily tweaked (https://github.com/tomershay100/mp3-steganography-lib)"
)
parser.add_argument("-i", "--input", type=str, required=True, help="input has to be the MP3 file to be analysed")
parser.add_argument("-o", "--output", type=str, default=None, help="output will be a JSON file with the description of the structure of the analysed file")
parser.add_argument("-d", "--data", action='store_true', help="include mpeg frame data in output json")
parser.add_argument("-f", "--force", action='store_true', help="allow overwriting of existing output path")
parser.add_argument("-r", "--reconstruct", action='store_true', help="restore mp3 file from JSON export (given JSON file must have been generated using --data option)")
parser.add_argument("--hex", action='store_true', help="store binary data as hex")

#TODO:
# http://www.mp3-tech.org/programmer/docs/mp3_theory.pdf
# - Coverage-Algorithm
# - tabellensicht mit header infos und generellen infos

args = parser.parse_args()

INPUT_PATH = Path(args.input).resolve()
OUTPUT_PATH = Path(args.output).resolve() if args.output is not None else None
SWITCH_DATA = args.data
SWITCH_FORCE = args.force
SWITCH_RECONSTRUCT = args.reconstruct
SWITCH_HXDATA = args.hex

print("##############################################################################")
print("#                          MP3FileStructureAnalyzer                          #")
print("##############################################################################")

print(f"\n  INPUT_PATH = {INPUT_PATH}\n  OUTPUT_PATH = {OUTPUT_PATH}\n  SWITCH_DATA = {'On' if SWITCH_DATA else 'Off'}\n  SWITCH_FORCE = {'On' if SWITCH_FORCE else 'Off'}\n  SWITCH_RECONSTRUCT = {'On' if SWITCH_RECONSTRUCT else 'Off'}\n  SWITCH_HXDATA = {'On' if SWITCH_HXDATA else 'Off'}\n")

if not INPUT_PATH.exists():
    print(f"ERROR: Could not find input file '{INPUT_PATH}'!")
    sys.exit(1)

if (OUTPUT_PATH is not None) and OUTPUT_PATH.exists() and (not SWITCH_FORCE):
    print(f"ERROR: Output file '{OUTPUT_PATH}' does already exist!")
    sys.exit(1)

if SWITCH_RECONSTRUCT:
    with open(INPUT_PATH, "r") as f:
        mp3_stream: bytes = b""

        json_dict = json.loads(f.read())
        id3v2 = json_dict["structure"]["id3v2"]
        frame_data = json_dict["structure"]["mpeg_frame_data"]
        id3v1 = json_dict["structure"]["id3v1.1"]

        if id3v2 is not None:
            if "raw" not in id3v2["data"]:
                print("ERROR: JSON input file does not contain raw data; make sure the given JSON file was generated using --data option!")
                sys.exit(1)
            conv_f = ast.literal_eval if str(id3v2["data"]["raw"])[0:2] == "b'" or str(id3v2["data"]["raw"])[0:2] == "b\"" else bytes.fromhex

            mp3_stream += conv_f(id3v2["data"]["raw"])

            for id3tag in id3v2["tags"]:
                mp3_stream += conv_f(id3tag["data"]["raw"])

            mp3_stream += conv_f(id3v2["data"]["raw_padding"])


        for i, frame in enumerate(frame_data):
            if "raw" in frame:
                conv_f = ast.literal_eval if str(frame["raw"])[0:2] == "b'" or str(frame["raw"])[0:2] == "b\"" else bytes.fromhex

                mp3_stream += conv_f(frame["raw"])
            else:
                if frame["main_data"]["raw"] is None:
                    print("ERROR: JSON input file does not contain raw data; make sure the given JSON file was generated using --data option!")
                    sys.exit(1)
                conv_f = ast.literal_eval if str(frame["main_data"]["raw"])[0:2] == "b'" or str(frame["main_data"]["raw"])[0:2] == "b\"" else bytes.fromhex

                header = b"".join([int(bytestr, 2).to_bytes(1, "big") for bytestr in frame["header"]["bitstring"].split(" ")])
                side_info = b"".join([int(bytestr, 2).to_bytes(1, "big") for bytestr in frame["side_info"]["bitstring"].split(" ")])
                main_data = conv_f(frame["main_data"]["raw"])

                mp3_stream += header
                mp3_stream += side_info
                mp3_stream += main_data

        if id3v1 is not None:
            mp3_stream += conv_f(id3v1["data"]["raw"])

        print("\n##############################################################################\n")
        if OUTPUT_PATH is not None:
            print(f"Saving MP3 output stream to '{OUTPUT_PATH}'...")
            with open(OUTPUT_PATH, "wb") as f2:
                f2.write(mp3_stream)
                f2.close()
        f.close()
else:
    with open(INPUT_PATH, "rb") as f:
        hex_data: list = [c for c in f.read()]

        with alive_bar(len(hex_data), title="Analyzing MP3", length=25) as pbar:
            id3v2_decoder: ID3 = ID3(hex_data, SWITCH_DATA, SWITCH_HXDATA)
            parsing_offset = 0
            if id3v2_decoder.is_valid:
                parsing_offset = id3v2_decoder.offset
            if parsing_offset > 0:
                print(f"found {parsing_offset} bytes ID3v2 data")
                pbar(parsing_offset, skipped=True)

            print("mpeg data")
            mp3_parser: MP3Parser = MP3Parser(hex_data, parsing_offset)
            parsed_frames = mp3_parser.parse_file(pbar, SWITCH_DATA, SWITCH_HXDATA)
            print(f"{parsed_frames} mpeg frames parsed")
            if parsed_frames > 0:
                id3v1_offset = mp3_parser.frames[-1]["position"] + mp3_parser.frames[-1]["length"]
                id3v1_decoder: ID3v1 = ID3v1(hex_data[id3v1_offset:], SWITCH_DATA, SWITCH_HXDATA)
                if id3v1_decoder.is_valid:
                    print(f"found {128} bytes ID3v1 data")
                    pbar(128, skipped=True)
            else:
                print("ERROR: Could parse any MPEG frames, sync word not found at expected position!")
                sys.exit(1)

        json_dict = {
            "file": INPUT_PATH.name,
            "size": len(hex_data),
            "frames": parsed_frames,
            "encoder": mp3_parser.frames[0]["main_data"]["encoder"],
            "global_header_info": {
                "length": mp3utils.default_statistics([frame["length"] for frame in mp3_parser.frames]),
                "samples": mp3utils.default_statistics([frame["samples"] for frame in mp3_parser.frames if "samples" in frame]),
                "version": mp3utils.default_categorical([frame["header"]["version"] for frame in mp3_parser.frames if "header" in frame], [1, 2, 2.5]),
                "layer": mp3utils.default_categorical([frame["header"]["layer"] for frame in mp3_parser.frames if "header" in frame], [1, 2, 3]),
                "crc": mp3utils.default_categorical([frame["header"]["crc"] for frame in mp3_parser.frames if "header" in frame], [0, 1]),
                "bitrate": mp3utils.default_statistics([frame["header"]["bitrate"] for frame in mp3_parser.frames if "header" in frame]),
                "samplerate": mp3utils.default_statistics([frame["header"]["samplerate"] for frame in mp3_parser.frames if "header" in frame]),
                "padding": mp3utils.default_categorical([frame["header"]["padding"] for frame in mp3_parser.frames if "header" in frame], [0, 1]),
                "private": mp3utils.default_categorical([frame["header"]["private"] for frame in mp3_parser.frames if "header" in frame], [0, 1]),
                "mode": mp3utils.default_categorical([frame["header"]["mode"] for frame in mp3_parser.frames if "header" in frame], ["ChannelMode.Stereo", "ChannelMode.JointStereo", "ChannelMode.DualChannel", "ChannelMode.Mono"]),
                "modeExt": mp3utils.default_categorical([frame["header"]["modeExt"] for frame in mp3_parser.frames if "header" in frame], ["ModeExtension.IntensityOffMSOff", "ModeExtension.IntensityOnMSOff", "ModeExtension.IntensityOffMSOn", "ModeExtension.IntensityOnMSOn", "ModeExtension.NONE"]),
                "copyright": mp3utils.default_categorical([frame["header"]["copyright"] for frame in mp3_parser.frames if "header" in frame], [0, 1]),
                "original": mp3utils.default_categorical([frame["header"]["original"] for frame in mp3_parser.frames if "header" in frame], [0, 1]),
                "emphasis": mp3utils.default_categorical([frame["header"]["emphasis"] for frame in mp3_parser.frames if "header" in frame], ["Emphasis.NONE", "Emphasis.MS5015", "Emphasis.Reserved", "Emphasis.CCITJ17"])
            },
            "structure": {
                "id3v2": {
                    "length": id3v2_decoder.offset,
                    "data": id3v2_decoder.json_dict,
                    "tags": [{
                        "id": tag.id,
                        "position": tag.position,
                        "payload": tag.position + 10,
                        "length": len(tag.content),
                        "flags": tag.frame_flags,
                        "data": tag.json_dict
                    } for tag in id3v2_decoder.id3_frames]
                } if id3v2_decoder.is_valid else None,
                "mpeg_frame_data": [frame for frame in mp3_parser.frames],
                "id3v1.1": {
                    "position": id3v1_offset,
                    "length": 128,
                    "data": id3v1_decoder.json_dict
                } if id3v1_decoder.is_valid else None
            },
        }

        # finish stego signatures
        global_signatures_dict = {}
        if json_dict["global_header_info"]["bitrate"]["min"] == json_dict["global_header_info"]["bitrate"]["max"]:
            global_signatures_dict["mp3stego"] = {}
            global_signatures_dict["mp3stego"]["mp3stego_constant_bitrate"] = 1
        for frame in [f for f in mp3_parser.frames if "stego_signatures" in f]:
            for sig in frame["stego_signatures"]:
                tool = str(sig).split("_")[0]
                if tool not in global_signatures_dict:
                    global_signatures_dict[tool] = {}
                if sig not in global_signatures_dict[tool]:
                    global_signatures_dict[tool][sig] = 0
                global_signatures_dict[tool][sig] += 1
        json_dict["stego_signatures"] = global_signatures_dict

        # build tables
        print("\n############################### file structure ###############################\n")
        print(f" - file: {json_dict['file']}")
        print(f" - size: {json_dict['size']} bytes")
        print(f" - frames: {json_dict['frames']}")
        print(f" - encoder: {'Unknown' if json_dict['encoder'] is None else json_dict['encoder']}")
        print(" - general structure:\n")
        tab = Texttable()
        tab.set_deco(Texttable.HEADER)
        tab.set_cols_dtype(["t", "i", "i", "f"])
        tab.set_cols_align(["l", "r", "r", "r"])
        tab.header(["Identifier", "Position", "Length", "Percentage"])
        if json_dict["structure"]["id3v2"] is not None:
            tab.add_row([f"ID3v{id3v2_decoder.version}", 0, parsing_offset, round((parsing_offset/len(hex_data)) * 100, 3)])
        tab.add_row(["MPEG frames", parsing_offset, id3v1_offset-parsing_offset, round(((id3v1_offset-parsing_offset)/len(hex_data)) * 100, 3)])
        if json_dict["structure"]["id3v1.1"] is not None:
            tab.add_row(["ID3v1.1", id3v1_offset, 128, round((128/len(hex_data)) * 100, 3)])
        [print(f"   {l}") for l in tab.draw().split("\n")]

        print("\n########################## global frame header info ##########################\n")
        tab = Texttable()
        tab.set_deco(Texttable.HEADER)
        tab.set_cols_dtype(["t", "t"])
        tab.set_cols_align(["l", "l"])
        ghi = json_dict['global_header_info']
        tab.add_rows([
            ["Metric", "Value(s)"],
            ["frame length", f"{round(ghi['length']['min'], 3)}/{round(ghi['length']['avg'], 3)}/{round(ghi['length']['max'], 3)}"],
            ["samples per frame", f"{round(ghi['samples']['avg'], 3)}"],
            ["mpeg version", f"{mp3utils.key_max(ghi['version'])} ({round((ghi['version'][mp3utils.key_max(ghi['version'])] / json_dict['frames']) * 100, 3)}%)"],
            ["mpeg layer", f"{mp3utils.key_max(ghi['layer'])} ({round((ghi['layer'][mp3utils.key_max(ghi['layer'])] / json_dict['frames']) * 100, 3)}%)"],
            ["crc", f"{'Yes' if mp3utils.key_max(ghi['crc']) == 0 else 'No'} ({round((ghi['crc'][mp3utils.key_max(ghi['crc'])] / json_dict['frames']) * 100, 3)}%)"],
            ["bitrate", f"{round(ghi['bitrate']['min'], 3)}/{round(ghi['bitrate']['avg'], 3)}/{round(ghi['bitrate']['max'], 3)} ({'CBR' if ghi['bitrate']['min'] == ghi['bitrate']['max'] else 'VBR'})"],
            ["sample rate", f"{round(ghi['samplerate']['min'], 3)}/{round(ghi['samplerate']['avg'], 3)}/{round(ghi['samplerate']['max'], 3)}"],
            ["padding", f"{'Yes' if mp3utils.key_max(ghi['padding']) == 1 else 'No'} ({round((ghi['padding'][mp3utils.key_max(ghi['padding'])] / json_dict['frames']) * 100, 3)}%)"],
            ["private", f"{'Yes' if mp3utils.key_max(ghi['private']) == 1 else 'No'} ({round((ghi['private'][mp3utils.key_max(ghi['private'])] / json_dict['frames']) * 100, 3)}%)"],
            ["channel mode", f"{mp3utils.key_max(ghi['mode']).split('.')[1]} ({round((ghi['mode'][mp3utils.key_max(ghi['mode'])] / json_dict['frames']) * 100, 3)}%)"],
            ["mode extension", f"{mp3utils.key_max(ghi['modeExt']).split('.')[1]} ({round((ghi['modeExt'][mp3utils.key_max(ghi['modeExt'])] / json_dict['frames']) * 100, 3)}%)"],
            ["copyright", f"{'Yes' if mp3utils.key_max(ghi['copyright']) == 1 else 'No'} ({round((ghi['copyright'][mp3utils.key_max(ghi['copyright'])] / json_dict['frames']) * 100, 3)}%)"],
            ["original", f"{'Yes' if mp3utils.key_max(ghi['original']) == 1 else 'No'} ({round((ghi['original'][mp3utils.key_max(ghi['original'])] / json_dict['frames']) * 100, 3)}%)"],
            ["emphasis", f"{mp3utils.key_max(ghi['emphasis']).split('.')[1]} ({round((ghi['emphasis'][mp3utils.key_max(ghi['emphasis'])] / json_dict['frames']) * 100, 3)}%)"],
        ])
        [print(f"   {l}") for l in tab.draw().split("\n")]
        print("\n##############################################################################\n")
        if OUTPUT_PATH is not None:
            print(f"Saving JSON output to '{OUTPUT_PATH}'...")
            with open(OUTPUT_PATH, "w") as f:
                json.dump(json_dict, f, indent=2)
    print("Done!")
sys.exit(0)
