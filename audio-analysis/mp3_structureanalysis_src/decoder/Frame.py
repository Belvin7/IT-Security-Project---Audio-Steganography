import numpy as np

from decoder.FrameHeader import *
from decoder.FrameSideInformation import FrameSideInformation

NUM_PREV_FRAMES = 9
NUM_OF_SAMPLES = 576

SQRT2 = math.sqrt(2)
PI = math.pi

class Frame:
    """
    The frame class, contains all the information of a current frame in mp3 file.
    """

    def __init__(self):
        # Declarations
        self.__pcm: np.ndarray = np.array([])
        self.__buffer: list = []
        self.__prev_frame_size: np.ndarray = np.zeros(NUM_PREV_FRAMES)
        self.__frame_size: int = 0
        self.__side_info: FrameSideInformation = FrameSideInformation()
        self.__header: FrameHeader = FrameHeader()
        self.__samples_per_frame = 0
        self.all_huffman_tables: list = []

    def init_frame_params(self, buffer: list, file_data: list, curr_offset: int):
        """
        Init the mp3 frame.

        :param buffer: buffer that contains the bytes of the mp3 frame.
        :type buffer: list
        :param file_data: buffer that contains the bytes of the mp3 file.
        :type file_data: list
        :param curr_offset: the offset of the file_data to the beginning of the frame.
        :type curr_offset: int
        """
        self.__buffer = buffer
        self.set_frame_size()
        self.__pcm = np.zeros((2 * NUM_OF_SAMPLES, self.__header.channels))

        starting_side_info_idx = 6 if self.__header.crc == 0 else 4
        #PERF_OVERHAUL: added 32 as limit to speed up performance!
        self.__side_info.set_side_info(self.__buffer[starting_side_info_idx:starting_side_info_idx+32], self.__header)

        self.all_huffman_tables.append(self.__get_frame_huffman_tables())

    def set_frame_size(self):
        """
        Determine the frame size.
        """
        samples_per_frame = 0

        if self.__header.layer == 3:
            if self.__header.mpeg_version == 1:
                samples_per_frame = 1152
            else:
                samples_per_frame = 576

        elif self.__header.layer == 2:
            samples_per_frame = 1152

        elif self.__header.layer == 1:
            samples_per_frame = 384

        self.__samples_per_frame = samples_per_frame

        # Minimum frame size = 1152 / 8 * 32000 / 48000 = 96
        # Minimum main_data size = 96 - 36 - 2 = 58
        # Maximum main_data_begin = 2^9 = 512
        # Therefore remember ceil(512 / 58) = 9 previous frames.
        for i in range(NUM_PREV_FRAMES - 1, 0, -1):
            self.prev_frame_size[i] = self.prev_frame_size[i - 1]
        self.prev_frame_size[0] = self.frame_size

        self.frame_size = int(((samples_per_frame / 8) * self.__header.bit_rate) / self.__header.sampling_rate)
        if self.__header.padding == 1:
            self.frame_size += 1

    @property
    def frame_size(self):
        return self.__frame_size

    @frame_size.setter
    def frame_size(self, frame_size):
        self.__frame_size = frame_size

    @property
    def prev_frame_size(self):
        return self.__prev_frame_size

    @prev_frame_size.setter
    def prev_frame_size(self, prev_frame_size):
        self.__prev_frame_size = prev_frame_size

    @property
    def side_info(self):
        return self.__side_info

    @property
    def pcm(self):
        return self.__pcm

    @property
    def header(self):
        return self.__header

    @property
    def samples_per_frame(self):
        return self.__samples_per_frame

    @property
    def sampling_rate(self):
        return self.__header.sampling_rate

    def init_header_params(self, buffer):
        self.__header.init_header_params(buffer)

    def get_bitrate(self):
        return self.__header.bit_rate

    def __get_frame_huffman_tables(self):
        """
        :return: list that contains all the huffman tables used in that frame
        """
        tmp = []
        for ch in range(self.__header.channels):
            for gr in range(2):
                for region in range(3):
                    tmp.append(int(self.__side_info.table_select[gr][ch][region]))
        return tmp
