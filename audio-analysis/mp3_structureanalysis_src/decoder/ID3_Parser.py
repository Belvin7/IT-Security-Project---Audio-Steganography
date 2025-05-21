from enum import Enum

from decoder import util
import mp3utils

MPEG_VERSION = 2


class ID3Flags(Enum):

    @property
    def flag(self):
        return self.name

    FooterPresent = 0
    ExperimentalIndicator = 1
    ExtendedHeader = 2
    Unsynchronisation = 3


class ID3FrameFlags(Enum):

    @property
    def flag(self):
        return self.name

    DiscardFrameOnTagAlter = 0
    DiscradFrameOnFileAlter = 1
    ReadOnly = 2
    ZLIBCompression = 3
    FrameEncrypted = 4
    FrameContainsGroupInformation = 5


class ID3Frame:
    """
    The id3 frame class, contains all the information of a current id3 frame in mp3 file.

    :param frame_id: current id3 frame id.
    :type frame_id: list
    :param flags: some flags from the id3 section.
    :type flags: int
    :param content: the id3 content in bytes.
    :type content: bytes
    """

    def __init__(self, frame_id: list, position: int, flags: int, content: bytes, raw: bytes | None, flag_hex: bool):
        self.__frame_id: list = frame_id
        self.__position = position
        self.__content: bytes = content
        self.__frame_flags: list = []
        self.__set_flags(flags)
        self.__raw = raw
        self.__flag_hex: bool = flag_hex

    def __set_flags(self, flags: int):
        for bit_num in range(3):
            if flags >> bit_num & 1:
                self.__frame_flags.append(True)
            else:
                self.__frame_flags.append(False)
        for bit_num in range(8, 11):
            if flags >> bit_num & 1:
                self.__frame_flags.append(True)
            else:
                self.__frame_flags.append(False)

    @property
    def id(self):
        chrs = [chr(k) for k in self.__frame_id]
        return ''.join(chrs)

    @property
    def length(self):
        return 10 + len(self.__content)

    @property
    def position(self):
        return self.__position

    @property
    def content(self):
        try:
            return self.__content.decode('utf-8')
        except:
            return self.__content

    @property
    def raw(self):
        if self.__flag_hex and self.__raw is not None:
            return self.__raw.hex()
        return self.__raw

    @property
    def frame_flags(self):
        flags = []
        for i, flag in enumerate(self.__frame_flags):
            if flag:
                flags.append(ID3FrameFlags(i).flag)
        return flags

    @property
    def json_dict(self):
        d: dict = {
            "human_readable": mp3utils.formatId3v2(self.id, self.content)
        }
        if self.raw is not None:
            d["content"] = str(self.content),
            d["raw"] = str(self.raw)
        return d

class ID3:
    """
    ID3 contains metadata irrelevant to the decoder. The header contains an offset used to determine the location of
    the first MP3 header.
    | Header | Additional header (optional) | Meta Data | Footer (optional) |

    :param buffer: buffet that contains bytes of id3 section in mp3 file
    :type buffer: list
    """

    def __init__(self, buffer: list, flag_data: bool, flag_hex: bool):
        # Declarations
        self.__buffer: list = buffer
        self.__offset: int
        self.__valid: bool
        self.__start: int
        self.__version: str
        self.__id3_flags: list = [False, False, False, False]
        self.__extended_header_size: int
        self.__id3_frames: list = []
        self.__flag_data: bool = flag_data
        self.__flag_hex: bool = flag_hex

        if chr(buffer[0]) == 'I' and chr(buffer[1]) == 'D' and chr(buffer[2]) == '3':
            self.__raw_header: bytes = bytes(buffer[0:10]) if flag_data else None
            self.__set_version(self.__buffer[3], self.__buffer[4])
            if self.__set_flags(self.__buffer[5]):
                self.__valid: bool = True
                self.__set_offset(util.char_to_int(self.__buffer[6:10]))
                self.__set_extended_header_size(util.char_to_int(self.__buffer[10:14]))
                self.__set_frames(10 + self.__extended_header_size)
            else:
                self.__valid: bool = False
        else:
            self.__valid: bool = False

    def __set_version(self, version: int, revision: int):
        self.__version = f'{MPEG_VERSION}.{version}.{revision}'

    def __set_offset(self, offset: int):
        if self.__id3_flags[ID3Flags.FooterPresent.value]:
            self.__offset = offset + 20
        else:
            self.__offset = offset + 10

    def __set_flags(self, flags: int):
        # These flags must be unset for frame to be valid (protected bits)
        for bit_num in range(4):
            if flags >> bit_num & 1:
                return False
        # Check flags
        for bit_num in range(4, 8):
            self.__id3_flags[bit_num - 4] = True if flags >> bit_num & 1 else False

        self.__id3_flags = tuple(self.__id3_flags)
        return True

    def __set_extended_header_size(self, size: int):
        if self.__id3_flags[2]:
            self.__extended_header_size = size
        else:
            self.__extended_header_size = 0

    def __set_frames(self, start):
        footer_size = self.__id3_flags[0] * 10
        size = self.__offset - self.__extended_header_size - footer_size
        i = 0

        valid = True
        while i < size and valid:
            frame_id = self.__buffer[start + i: start + i + 4]
            tag_position = start + i
            for c in frame_id:
                if not (chr(c).isupper() or chr(c).isdigit()):  # Check for legal ID
                    valid = False
                    break
            if valid:
                i += 4
                #field_size = util.char_to_int(self.__buffer[start + i: start + i + 4])  # 4 Bytes
                #BUG_FIX:
                field_size = int.from_bytes(bytes(self.__buffer[start + i: start + i + 4]), byteorder = "big")
                i += 4
                frame_flags = util.get_bits(self.__buffer, util.BYTE_LENGTH * (start + i), 16)  # 2 Bytes
                i += 2
                frame_content = bytes(self.__buffer[start + i: start + i + field_size])
                i += field_size
                self.__id3_frames.append(ID3Frame(frame_id, tag_position, frame_flags, frame_content, bytes(self.__buffer[tag_position:tag_position+10+len(frame_content)]) if self.__flag_data else None, self.__flag_hex))

    @property
    def offset(self):
        return self.__offset

    @property
    def is_valid(self):
        return self.__valid

    @property
    def version(self):
        return self.__version

    @property
    def id3_flags(self):
        flags = []
        for i, flag in enumerate(self.__id3_flags):
            if flag:
                flags.append(ID3Flags(i).flag)
        return flags

    @property
    def extended_header_size(self):
        return self.__extended_header_size

    @property
    def id3_frames(self):
        return self.__id3_frames

    @property
    def raw_header(self) -> bytes | None:
        return self.__raw_header
    @property
    def json_dict(self):
        d: dict = {
            "version": self.version,
            "flags": self.id3_flags
        }
        if self.raw_header is not None:
            padding: bytes = bytes(self.__buffer[self.id3_frames[-1].position + self.id3_frames[-1].length:self.offset])
            d["raw"] = self.raw_header.hex() if self.__flag_hex else str(self.raw_header)
            d["raw_padding"] = padding.hex() if self.__flag_hex else str(padding)

        return d

class ID3v1:
    def __init__(self, buffer: list, flag_data: bool, flag_hex: bool):
        # Declarations
        self.__buffer: list = buffer
        self.__is_valid = len(buffer) >= 128 and bytes(buffer[0:3]) == b"TAG"
        if self.__is_valid:
            tgBytes = bytes(buffer[0:128])
            self.__title = tgBytes[3:33].rstrip(b"\x00\x20").decode(errors = "ignore")
            self.__artist = tgBytes[33:63].rstrip(b"\x00\x20").decode(errors = "ignore")
            self.__album = tgBytes[63:93].rstrip(b"\x00\x20").decode(errors = "ignore")
            self.__year = tgBytes[93:97].decode(errors = "ignore")
            self.__comment = tgBytes[97:125].rstrip(b"\x00\x20").decode(errors = "ignore")
            self.__track = None if tgBytes[125:127] == b"\x00\x00" else ord(tgBytes[126:127])
            self.__genre = mp3utils.matchId3v1genre(tgBytes[127:128])
            self.__raw: bytes = tgBytes if flag_data else None
        self.__flag_hex: bool = flag_hex
    @property
    def is_valid(self):
        return self.__is_valid
    @property
    def title(self) -> str:
        return self.__title
    @property
    def artist(self) -> str:
        return self.__artist
    @property
    def album(self) -> str:
        return self.__album
    @property
    def year(self) -> str:
        return self.__year
    @property
    def comment(self) -> str:
        return self.__comment
    @property
    def track(self) -> int:
        return self.__track
    @property
    def genre(self) -> str:
        return self.__genre
    @property
    def raw(self) -> bytes | None:
        return self.__raw
    @property
    def json_dict(self) -> dict:
        d: dict = {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "year": self.year,
            "comment": self.comment,
            "track": self.track,
            "genre": self.genre
        }
        if self.raw is not None:
            d["raw"] = self.raw.hex() if self.__flag_hex else str(self.raw)
        return d
