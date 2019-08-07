import re
from abc import ABCMeta, abstractmethod

import six

from bot.constant import Parts, PayLoadFileType


@six.add_metaclass(ABCMeta)
class FilterBase(object):
    def __init__(self):
        super(FilterBase, self).__init__()

    def __call__(self, event):
        return self.filter(event)

    def __and__(self, other):
        return AndFilter(self, other)

    def __or__(self, other):
        return OrFilter(self, other)

    def __invert__(self):
        return InvertFilter(self)

    @abstractmethod
    def filter(self, event):
        pass


class CompositeFilter(FilterBase):
    def __init__(self, filter_1, filter_2):
        super(CompositeFilter, self).__init__()

        self.filter_1 = filter_1
        self.filter_2 = filter_2


class AndFilter(CompositeFilter):
    def filter(self, event):
        return self.filter_1(event) and self.filter_2(event)


class OrFilter(CompositeFilter):
    def filter(self, event):
        return self.filter_1(event) or self.filter_2(event)


class IterableFilter(FilterBase):
    def __init__(self, iterable):
        super(IterableFilter, self).__init__()

        self.iterable = iterable


class AllFilter(IterableFilter):
    def filter(self, event):
        return all(f(event) for f in self.iterable)


class AnyFilter(IterableFilter):
    def filter(self, event):
        return any(f(event) for f in self.iterable)


class InvertFilter(FilterBase):
    def __init__(self, filter_):
        super(InvertFilter, self).__init__()

        self.filter_ = filter_

    def filter(self, event):
        return not self.filter_(event)


class MessageFilter(FilterBase):
    def filter(self, event):
        return "text" in event.data and isinstance(event.data["text"], six.string_types)


class CommandFilter(MessageFilter):
    COMMAND_PREFIXES = ("/", ".")

    def filter(self, event):
        return super(CommandFilter, self).filter(event) and any(
            event.data["text"].strip().startswith(p) for p in CommandFilter.COMMAND_PREFIXES
        )


class RegexpFilter(MessageFilter):
    def __init__(self, pattern):
        super(RegexpFilter, self).__init__()

        self.pattern = re.compile(pattern) if isinstance(pattern, six.string_types) else pattern

    def filter(self, event):
        return super(RegexpFilter, self).filter(event) and self.pattern.search(event.data["text"])


class SenderFilter(MessageFilter):
    def __init__(self, user_id):
        super(SenderFilter, self).__init__()

        self.user_id = user_id

    def filter(self, event):
        return super(SenderFilter, self).filter(event) and 'from' in event.data \
               and event.data['from']['userId'] == self.user_id


class FileFilter(MessageFilter):
    def filter(self, event):
        return super(FileFilter, self).filter(event) and 'parts' in event.data and any(
           p['type'] == Parts.FILE.value for p in event.data['parts']
        )


class ImageFilter(FileFilter):
    def filter(self, event):
        return super(ImageFilter, self).filter(event) and any(
            p['payload']['type'] == PayLoadFileType.IMAGE.value for p in event.data['parts'] if 'type' in p['payload']
        )


class VideoFilter(FileFilter):
    def filter(self, event):
        return super(VideoFilter, self).filter(event) and any(
            p['payload']['type'] == PayLoadFileType.VIDEO.value for p in event.data['parts'] if 'type' in p['payload']
        )


class AudioFilter(FileFilter):
    def filter(self, event):
        return super(AudioFilter, self).filter(event) and any(
            p['payload']['type'] == PayLoadFileType.AUDIO.value for p in event.data['parts'] if 'type' in p['payload']
        )


class StickerFilter(FileFilter):
    def filter(self, event):
        return super(FileFilter, self).filter(event) and 'parts' in event.data and any(
           p['type'] == Parts.STICKER.value for p in event.data['parts']
        )


class MentionFilter(MessageFilter):
    def __init__(self, user_id=None):
        super(MentionFilter, self).__init__()

        self.user_id = user_id

    def filter(self, event):
        return super(MentionFilter, self).filter(event) and 'parts' in event.data and any(
           p['type'] == Parts.MENTION.value and (
               p['payload']['userId'] == self.user_id if self.user_id else True
           ) for p in event.data['parts']
        )


class ForwardFilter(MessageFilter):
    def filter(self, event):
        return 'parts' in event.data and any(p['type'] == Parts.FORWARD.value for p in event.data['parts'])


class ReplyFilter(MessageFilter):
    def filter(self, event):
        return super(ReplyFilter, self).filter(event) and 'parts' in event.data and any(
           p['type'] == Parts.REPLY.value for p in event.data['parts']
        )


class URLFilter(RegexpFilter):
    REGEXP = re.compile(r"^\s*https?://\S+\s*$", re.IGNORECASE)

    __FILTER = InvertFilter(FileFilter())  # Files are also URLs, but we need to skip it.

    def __init__(self):
        super(URLFilter, self).__init__(URLFilter.REGEXP)

    def filter(self, event):
        return super(URLFilter, self).filter(event) and URLFilter.__FILTER(event)


class Filter(object):
    message = MessageFilter()
    command = CommandFilter()
    file = FileFilter()
    image = ImageFilter()
    video = VideoFilter()
    audio = AudioFilter()
    media = image | video | audio
    data = file & ~media
    sticker = StickerFilter()
    url = URLFilter()
    text = message & ~(command | sticker | file | url)
    regexp = RegexpFilter
    mention = MentionFilter
    forward = ForwardFilter()
    reply = ReplyFilter()
    sender = SenderFilter

