from abc import ABCMeta

import six

from .dispatcher import StopDispatching
from .event import EventType
from .filter import Filter


@six.add_metaclass(ABCMeta)
class HandlerBase(object):
    def __init__(self, filters=None, callback=None):
        super(HandlerBase, self).__init__()

        self.filters = filters
        self.callback = callback

    def check(self, event, dispatcher):
        return bool(not self.filters or self.filters(event))

    def handle(self, event, dispatcher):
        if self.callback:
            self.callback(bot=dispatcher.bot, event=event)


class DefaultHandler(HandlerBase):
    def __init__(self, callback=None):
        super(DefaultHandler, self).__init__(callback=callback)

    def check(self, event, dispatcher):
        return super(DefaultHandler, self).check(event=event, dispatcher=dispatcher) and not any(
            h.check(event=event, dispatcher=dispatcher) for h in dispatcher.handlers if h is not self
        )

    def handle(self, event, dispatcher):
        super(DefaultHandler, self).handle(event=event, dispatcher=dispatcher)
        raise StopDispatching


class NewChatMembersHandler(HandlerBase):
    def check(self, event, dispatcher):
        return (
            super(NewChatMembersHandler, self).check(event=event, dispatcher=dispatcher) and
            event.type is EventType.NEW_CHAT_MEMBERS
        )


class LeftChatMembersHandler(HandlerBase):
    def check(self, event, dispatcher):
        return (
            super(LeftChatMembersHandler, self).check(event=event, dispatcher=dispatcher) and
            event.type is EventType.LEFT_CHAT_MEMBERS
        )


class PinnedMessageHandler(HandlerBase):
    def check(self, event, dispatcher):
        return (
            super(PinnedMessageHandler, self).check(event=event, dispatcher=dispatcher) and
            event.type is EventType.PINNED_MESSAGE
        )


class UnPinnedMessageHandler(HandlerBase):
    def check(self, event, dispatcher):
        return (
            super(UnPinnedMessageHandler, self).check(event=event, dispatcher=dispatcher) and
            event.type is EventType.UNPINNED_MESSAGE
        )


class MessageHandler(HandlerBase):
    def check(self, event, dispatcher):
        return (
                super(MessageHandler, self).check(event=event, dispatcher=dispatcher) and
                event.type == EventType.NEW_MESSAGE
        )


class EditedMessageHandler(HandlerBase):
    def check(self, event, dispatcher):
        return (
                super(EditedMessageHandler, self).check(event=event, dispatcher=dispatcher) and
                event.type == EventType.EDITED_MESSAGE
        )


class DeletedMessageHandler(HandlerBase):
    def check(self, event, dispatcher):
        return (
                super(DeletedMessageHandler, self).check(event=event, dispatcher=dispatcher) and
                event.type == EventType.DELETED_MESSAGE
        )


class CommandHandler(MessageHandler):
    def __init__(self, command=None, filters=None, callback=None):
        super(CommandHandler, self).__init__(
            filters=Filter.command if filters is None else Filter.command & filters,
            callback=callback
        )

        self.command = command

    def check(self, event, dispatcher):
        if super(CommandHandler, self).check(event=event, dispatcher=dispatcher):
            command = event.data["text"].partition(" ")[0][1:].lower()
            return not self.command or any((c.lower() == command for c in (
                (self.command,) if isinstance(self.command, six.string_types) else self.command
            )))


class HelpCommandHandler(CommandHandler):
    def __init__(self, filters=None, callback=None):
        super(HelpCommandHandler, self).__init__(command="help", filters=filters, callback=callback)


class StartCommandHandler(CommandHandler):
    def __init__(self, filters=None, callback=None):
        super(StartCommandHandler, self).__init__(command="start", filters=filters, callback=callback)


class FeedbackCommandHandler(CommandHandler):
    def __init__(
        self, target, message="Feedback from {source}: {message}", reply="Got it!", error_reply=None,
        command="feedback", filters=None
    ):
        super(FeedbackCommandHandler, self).__init__(command=command, filters=filters, callback=self.message_cb)

        self.target = target
        self.message = message
        self.reply = reply
        self.error_reply = error_reply

    def message_cb(self, bot, event):
        source = event.data['chat']['chatId']
        feedback_text = event.data["text"].partition(" ")[2].strip()

        if feedback_text:
            bot.send_text(chat_id=self.target, text=self.message.format(source=source, message=feedback_text))

            if self.reply is not None:
                bot.send_text(chat_id=source, text=self.reply)
        elif self.error_reply is not None:
            bot.send_text(chat_id=source, text=self.error_reply)


class UnknownCommandHandler(CommandHandler):
    def __init__(self, filters=None, callback=None):
        super(UnknownCommandHandler, self).__init__(filters=filters, callback=callback)

    def check(self, event, dispatcher):
        return super(UnknownCommandHandler, self).check(event=event, dispatcher=dispatcher) and not any(
            h.check(event=event, dispatcher=dispatcher) for h in dispatcher.handlers if
            isinstance(h, CommandHandler) and h is not self
        )

    def handle(self, event, dispatcher):
        super(UnknownCommandHandler, self).handle(event=event, dispatcher=dispatcher)
        raise StopDispatching


class BotButtonCommandHandler(HandlerBase):
    def check(self, event, dispatcher):
        return (
            super(BotButtonCommandHandler, self).check(event=event, dispatcher=dispatcher) and
            event.type is EventType.CALLBACK_QUERY
        )