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

from functools import reduce
from statistics import mean, stdev
@staticmethod
def key_max(key):
    return max(zip(key.values(), key.keys()))[1]
@staticmethod
def byteToBits(byte): #convert 1-byte-long-string to 8-bit-string
    return bin(byte)[2:].rjust(8, '0')
@staticmethod
def convertUnicodeString(byteString): #convert unicode string
    return byteString.split(b"\xff\xfe")[-1].replace(b"\x00", b"").decode(errors = "ignore")
@staticmethod
def formatId3v2(id, data):
    try:
        match id:
            #fields to decode (text fields)
            case "TPE1" | "TPE2" | "TCOP" | "TPOS" | "TPUB" | "TCON" | "TCOM" | "TIT2" | "TALB" | "COMM" | "TRCK" | "TYER":
                return data.strip(b"\x00").decode(errors = "ignore") if data.find(b"\xff\xfe") == -1 else convertUnicodeString(data)
            #fields to decode to int (number fields)
            case "TLEN":
                return int(data.strip(b"\x00").decode(errors = "ignore") if data.find(b"\xff\xfe") == -1 else convertUnicodeString(data))
            case _:
                return None
    except TypeError:
        return None
@staticmethod
def default_statistics(lst: list):
    return {
            "avg": mean(lst),
            "stdev": stdev(lst),
            "min": reduce(min, lst),
            "max": reduce(max, lst)
        }
@staticmethod
def default_categorical(lst: list, categories: list = None):
    dictionary = {}
    if categories is not None:
        for i in categories:
            dictionary[i] = 0
    for i in lst:
        if i not in dictionary:
            dictionary[i] = 0
        dictionary[i] += 1
    return dictionary
@staticmethod
def matchId3v1genre(genreByte):
    genre_number = ord(genreByte)
    genre_mapping = {
        0: 'Blues', 1: 'Classic Rock', 2: 'Country', 3: 'Dance', 4: 'Disco',
        5: 'Funk', 6: 'Grunge', 7: 'Hip-Hop', 8: 'Jazz', 9: 'Metal',
        10: 'New Age', 11: 'Oldies', 12: 'Other', 13: 'Pop', 14: 'R&B',
        15: 'Rap', 16: 'Reggae', 17: 'Rock', 18: 'Techno', 19: 'Industrial',
        20: 'Alternative', 21: 'Ska', 22: 'Death Metal', 23: 'Pranks', 24: 'Soundtrack',
        25: 'Euro-Techno', 26: 'Ambient', 27: 'Trip-Hop', 28: 'Vocal', 29: 'Jazz+Funk',
        30: 'Fusion', 31: 'Trance', 32: 'Classical', 33: 'Instrumental', 34: 'Acid',
        35: 'House', 36: 'Game', 37: 'Sound Clip', 38: 'Gospel', 39: 'Noise',
        40: 'Alternative Rock', 41: 'Bass', 42: 'Soul', 43: 'Punk', 44: 'Space',
        45: 'Meditative', 46: 'Instrumental Pop', 47: 'Instrumental Rock', 48: 'Ethnic', 49: 'Gothic',
        50: 'Darkwave', 51: 'Techno-Industrial', 52: 'Electronic', 53: 'Pop-Folk', 54: 'Eurodance',
        55: 'Dream', 56: 'Southern Rock', 57: 'Comedy', 58: 'Cult', 59: 'Gangsta Rap',
        60: 'Top 40', 61: 'Christian Rap', 62: 'Pop/Funk', 63: 'Jungle', 64: 'Native American',
        65: 'Cabaret', 66: 'New Wave', 67: 'Psychedelic', 68: 'Rave', 69: 'Showtunes',
        70: 'Trailer', 71: 'Lo-Fi', 72: 'Tribal', 73: 'Acid Punk', 74: 'Acid Jazz',
        75: 'Polka', 76: 'Retro', 77: 'Musical', 78: 'Rock & Roll', 79: 'Hard Rock',
        80: 'Folk', 81: 'Folk/Rock', 82: 'National Folk', 83: 'Swing', 84: 'Fast-Fusion',
        85: 'Bebop', 86: 'Latin', 87: 'Revival', 88: 'Celtic', 89: 'Bluegrass',
        90: 'Avantgarde', 91: 'Gothic Rock', 92: 'Progressive Rock', 93: 'Psychedelic Rock', 94: 'Symphonic Rock',
        95: 'Slow Rock', 96: 'Big Band', 97: 'Chorus', 98: 'Easy Listening', 99: 'Acoustic',
        100: 'Humour', 101: 'Speech', 102: 'Chanson', 103: 'Opera', 104: 'Chamber Music',
        105: 'Sonata', 106: 'Symphony', 107: 'Booty Bass', 108: 'Primus', 109: 'Porn Groove',
        110: 'Satire', 111: 'Slow Jam', 112: 'Club', 113: 'Tango', 114: 'Samba',
        115: 'Folklore', 116: 'Ballad', 117: 'Power Ballad', 118: 'Rhythmic Soul', 119: 'Freestyle',
        120: 'Duet', 121: 'Punk Rock', 122: 'Drum Solo', 123: 'A Cappella', 124: 'Euro-House',
        125: 'Dance Hall', 126: 'Goa', 127: 'Drum & Bass', 128: 'Club-House', 129: 'Hardcore',
        130: 'Terror', 131: 'Indie', 132: 'BritPop', 133: 'Negerpunk', 134: 'Polsk Punk',
        135: 'Beat', 136: 'Christian Gangsta Rap', 137: 'Heavy Metal', 138: 'Black Metal', 139: 'Crossover',
        140: 'Contemporary Christian', 141: 'Christian Rock', 142: 'Merengue', 143: 'Salsa', 144: 'Thrash Metal',
        145: 'Anime', 146: 'JPop', 147: 'Synthpop', 148: 'Christmas', 149: 'Art Rock',
        150: 'Baroque', 151: 'Bhangra', 152: 'Big Beat', 153: 'Breakbeat', 154: 'Chillout',
        155: 'Downtempo', 156: 'Dub', 157: 'EBM', 158: 'Eclectic', 159: 'Electro',
        160: 'Electroclash', 161: 'Emo', 162: 'Experimental', 163: 'Garage', 164: 'Global',
        165: 'IDM', 166: 'Illbient', 167: 'Industro-Goth', 168: 'Jam Band', 169: 'Krautrock',
        170: 'Leftfield', 171: 'Lounge', 172: 'Math rock', 173: 'New Romantic', 174: 'Nu-Breakz',
        175: 'Post-Punk', 176: 'Post-Rock', 177: 'Psytrance', 178: 'Shoegaze', 179: 'Space Rock',
        180: 'Trop Rock', 181: 'World Music', 182: 'Neoclassical', 183: 'Audiobook', 184: 'Audio Theatre',
        185: 'Neue Deutsche Welle', 186: 'Podcast', 187: 'Indie-Rock', 188: 'G-Funk', 189: 'Dubstep',
        190: 'Garage Rock ', 191: 'Psybient', 255: 'None'
    }

    return genre_mapping.get(genre_number, 'Unknown')
