from enum import Enum, unique


@unique
class ImageType(Enum):
    REGULAR = "0"
    SNAP = "1"
    STICKER = "2"
    RESERVED_3 = "3"
    IMAGE_ANIMATED = "4"
    STICKER_ANIMATED = "5"
    RESERVED_6 = "6"
    RESERVED_7 = "7"


@unique
class VideoType(Enum):
    REGULAR = "8"
    SNAP = "9"
    PTS = "A"
    PTS_B = "B"
    RESERVED_C = "C"
    STICKER = "D"
    RESERVED_E = "E"
    RESERVED_F = "F"


@unique
class AudioType(Enum):
    REGULAR = "G"
    SNAP = "H"
    PTT = "I"
    PTT_J = "J"
    RESERVED_K = "K"
    RESERVED_L = "L"
    RESERVED_M = "M"
    RESERVED_N = "N"


@unique
class Parts(Enum):
    FILE = "file"
    STICKER = "sticker"
    MENTION = "mention"
    VOICE = "voice"
    FORWARD = "forward"
    REPLY = "reply"


@unique
class PayLoadFileType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


@unique
class ChatType(Enum):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"


@unique
class ParseMode(Enum):
    MARKDOWNV2 = "MarkdownV2"
    HTML = "HTML"


@unique
class StyleType(Enum):
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    LINK = "link"
    MENTION = "mention"
    INLINE_CODE = "inline_code"
    PRE = "pre"
    ORDERED_LIST = "ordered_list"
    UNORDERED_LIST = "unordered_list"
    QUOTE = "quote"
