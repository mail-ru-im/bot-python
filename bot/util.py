import signal
from collections import namedtuple

from baseconv import BaseConverter

from bot.constant import ImageType, VideoType, AudioType

BASE62_CONVERTER = BaseConverter("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def decode_file_id(file_id):
    file_type = file_id[0]
    for t in (ImageType, VideoType, AudioType):
        try:
            file_type = t(file_type)
            break
        except ValueError:
            pass
    else:
        file_type = None

    width = height = length = color = None
    if file_type:
        type_class = type(file_type)
        if type_class in (ImageType, VideoType):
            # TWWHHCCCxxxxxxxxxxxxxxxxxxxxxxxxx
            width = int(BASE62_CONVERTER.decode(file_id[1:3]))
            height = int(BASE62_CONVERTER.decode(file_id[3:5]))
            if file_type not in (VideoType.PTS, VideoType.PTS_B):
                color = hex(int(BASE62_CONVERTER.decode(file_id[5:8])))

        if file_type in (VideoType.PTS, VideoType.PTS_B):
            # TWWHHLLLLCCCxxxxxxxxxxxxxxxxxxxxx
            length = int(BASE62_CONVERTER.decode(file_id[5:9]))
            color = hex(int(BASE62_CONVERTER.decode(file_id[9:12])))
        elif file_type in (AudioType.PTT, AudioType.PTT_J):
            # TLLLLxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            length = int(BASE62_CONVERTER.decode(file_id[1:5]))

    return namedtuple("_", ("file_type", "width", "height", "length", "color"))(file_type, width, height, length, color)


_signals = {getattr(signal, n): n for n in dir(signal) if n.startswith("SIG") and "_" not in n}


def signal_name_by_code(code):
    return _signals[code]


def invalidate_cached_property(o, name):
    if hasattr(o, name):
        delattr(o, name)


def wrap(string, length):
    return (string[i:i + length] for i in range(0, len(string), length))
