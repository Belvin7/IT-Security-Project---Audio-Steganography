from decoder.Frame import *

HEADER_SIZE = 4

class MP3Parser:
    """
    Class for parsing mp3 files into wav file.

    :param file_data: buffer for the file hexadecimal data.
    :type file_data: list
    :param offset: offset for the file to begin after the id3.
    :type offset: int
    """

    def __init__(self, file_data: list, offset: int):
        # Declarations
        self.__offset: int = offset
        self.__curr_frame: Frame = Frame()
        self.__valid: bool = False
        # List of integers that contain the file (without ID3) data
        self.__file_data: list = []
        self.__buffer: list = []
        self.__frames: np.array = np.array([])
        self.__file_length: int = 0
        # self.__file_path = file_path

        # cut the id3 from hex_data
        self.__buffer: list = file_data[offset:]

        if self.__buffer[0] == 0xFF and self.__buffer[1] >= 0xE0:
            self.__valid: bool = True
            self.__file_data: list = file_data
            self.__file_length: int = len(file_data)
            self.__init_curr_header()
            self.__curr_frame.set_frame_size()
        else:
            self.__valid: bool = False

    def __init_curr_header(self):
        if self.__buffer[0] == 0xFF and self.__buffer[1] >= 0xE0:
            self.__curr_frame.init_header_params(self.__buffer)
        else:
            self.__valid = False

    def __init_curr_frame(self):
        self.__curr_frame.init_frame_params(self.__buffer, self.__file_data, self.__offset)

    def parse_file(self, pbar, flag_data, flag_hex) -> int:
        """
        decoding the mp3 file, frame by frame and saves the final pcm data.

        :return: the number of parsed frames
        :rtype: int
        """
        frames_dict = []
        num_of_parsed_frames = 0

        while self.__valid and self.__file_length > self.__offset + HEADER_SIZE:
            self.__init_curr_header()
            if self.__valid:
                self.__init_curr_frame()
                __encoder = None

                __main_data_raw = bytes(self.__buffer[self.__curr_frame.side_info.side_info_length + 4:self.__curr_frame.frame_size])
                if __main_data_raw[0:4] == b"Xing":
                    __encoder = "Xing"
                if __main_data_raw[0:4] == b"Info":
                    print("found main data info header")
                if __main_data_raw[0:4] == b"LAME":
                    __encoder = "LAME"

                __stego_signatures = {}
                if self.__offset + self.__curr_frame.frame_size > self.__file_length:
                    #mp3stego signature
                    __stego_signatures["mp3stego_defective_payload_ending"] = True
                    print("potential stego-signature found: mp3stego")
                if num_of_parsed_frames == 0 and self.__curr_frame.header.private and self.__curr_frame.header.copyright and self.__curr_frame.header.original and self.__curr_frame.header.emphasis == Emphasis.CCITJ17:
                    #stegonaut signature
                    __stego_signatures["stegonaut_header"] = True
                    print("potential stego-signature found: stegonaut")
                if __main_data_raw[15:19] == b"XXXX":
                    #mp3stegz signature
                    __stego_signatures["mp3stegz_trace"] = True
                    print("potential stego-signature found: mp3stegz")

                frames_dict.append({
                    "position": self.__offset,
                    "length": self.__curr_frame.frame_size,
                    "samples": self.__curr_frame.samples_per_frame,
                    "header": {
                        "bitstring": self.__curr_frame.header.bitstring,
                        "version": self.__curr_frame.header.mpeg_version,
                        "layer": self.__curr_frame.header.layer,
                        "crc": self.__curr_frame.header.crc,
                        "bitrate": self.__curr_frame.get_bitrate(),
                        "samplerate": self.__curr_frame.sampling_rate,
                        "padding": self.__curr_frame.header.padding,
                        "private": self.__curr_frame.header.private,
                        "mode": str(self.__curr_frame.header.channel_mode),
                        "modeExt": str(self.__curr_frame.header.mode_extension),
                        "copyright": self.__curr_frame.header.copyright,
                        "original": self.__curr_frame.header.original,
                        "emphasis": str(self.__curr_frame.header.emphasis)
                    },
                    "side_info": {
                        "bitstring": self.__curr_frame.side_info.bitstring,
                        "position": self.__offset + 4,
                        "length": self.__curr_frame.side_info.side_info_length,
                        "main_data_begin": self.__curr_frame.side_info.main_data_begin,
                        "scfsi": [
                            "".join(["1" if b == 1 else "0" for b in self.__curr_frame.side_info.scfsi[c]]) for c in range(self.__curr_frame.header.channels)
                        ],
                        "granule_info": [{
                            "part2_3_length": [self.__curr_frame.side_info.part2_3_length[g][c] for c in range(self.__curr_frame.header.channels)],
                            "big_value": [self.__curr_frame.side_info.big_value[g][c] for c in range(self.__curr_frame.header.channels)],
                            "global_gain": [self.__curr_frame.side_info.global_gain[g][c] for c in range(self.__curr_frame.header.channels)],
                            "scalefac_compress": [self.__curr_frame.side_info.scale_fac_compress[g][c] for c in range(self.__curr_frame.header.channels)],
                            "slen1": [self.__curr_frame.side_info.slen1[g][c] for c in range(self.__curr_frame.header.channels)],
                            "slen2": [self.__curr_frame.side_info.slen2[g][c] for c in range(self.__curr_frame.header.channels)],
                            "windows_switching_flag": [True if self.__curr_frame.side_info.window_switching[g][c] == 1 else False for c in range(self.__curr_frame.header.channels)],
                            "block_type": [self.__curr_frame.side_info.block_type[g][c] for c in range(self.__curr_frame.header.channels)],
                            "mixed_block_flag": [True if self.__curr_frame.side_info.mixed_block_flag[g][c] == 1 else False for c in range(self.__curr_frame.header.channels)],
                            "table_select": [[self.__curr_frame.side_info.table_select[g][c][r] for r in range(2 if self.__curr_frame.side_info.window_switching[g][c] == 1 else 3)] for c in range(self.__curr_frame.header.channels)],
                            "subblock_gain": [[self.__curr_frame.side_info.sub_block_gain[g][c][w] for w in range(3)] if self.__curr_frame.side_info.window_switching[g][c] == 1 else None for c in range(self.__curr_frame.header.channels)],
                            "region0_count": [self.__curr_frame.side_info.region0_count[g][c] for c in range(self.__curr_frame.header.channels)],
                            "region1_count": [self.__curr_frame.side_info.region1_count[g][c] for c in range(self.__curr_frame.header.channels)],
                            "pre_flag": [True if self.__curr_frame.side_info.pre_flag[g][c] == 1 else False for c in range(self.__curr_frame.header.channels)],
                            "scale_fac_scale": [True if self.__curr_frame.side_info.scale_fac_scale[g][c] == 1 else False for c in range(self.__curr_frame.header.channels)],
                            "count1table_select": [True if self.__curr_frame.side_info.count1table_select[g][c] else False for c in range(self.__curr_frame.header.channels)]
                        } for g in range(2)]
                    },
                    "main_data": {
                        "position": self.__offset + 4 + self.__curr_frame.side_info.side_info_length,
                        "length": self.__curr_frame.frame_size - self.__curr_frame.side_info.side_info_length - 4,
                        "raw": (__main_data_raw.hex() if flag_hex else str(__main_data_raw)) if flag_data else None,
                        "encoder": __encoder
                    },
                    "stego_signatures": __stego_signatures
                })
                # get all bits from the huffman tables
                num_of_parsed_frames += 1
                self.__offset += self.__curr_frame.frame_size
                #PERF_OVERHAUL: added 6912 (theoretical maximum) as limit to speed up performance!
                self.__buffer = self.__file_data[self.__offset:min(len(self.__file_data), self.__offset + 6912)]

                pbar(self.__curr_frame.frame_size, skipped=True)
            else:
                next_sw = bytes(self.__buffer).find(b"\xff", 1)
                if next_sw > 0:
                    awkward_data = bytes(self.__file_data[self.__offset:self.__offset+next_sw])
                    print(f"found {next_sw} bytes of awkward data behind frame {num_of_parsed_frames}")
                    frames_dict.append({
                        "position": self.__offset,
                        "length": next_sw,
                        "raw": awkward_data.hex() if flag_hex else str(awkward_data)
                    })
                    self.__offset += next_sw
                    self.__buffer = self.__file_data[self.__offset:min(len(self.__file_data), self.__offset + 6912)]
                    self.__valid = True
                    pbar(next_sw, skipped=True)

        self.__frames = np.array(frames_dict)

        return num_of_parsed_frames

    def get_bitrate(self) -> int:
        """
        :return: the bitrate of the mp3 file (and the output wav file)
        :rtype: int
        """
        return self.__curr_frame.get_bitrate()

    @property
    def frames(self):
        return self.__frames
