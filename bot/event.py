from enum import Enum, unique


@unique
class EventType(Enum):
    NEW_MESSAGE = "newMessage"
    EDITED_MESSAGE = "editedMessage"
    DELETED_MESSAGE = "deletedMessage"
    PINNED_MESSAGE = "pinnedMessage"
    UNPINNED_MESSAGE = "unpinnedMessage"
    NEW_CHAT_MEMBERS = "newChatMembers"
    LEFT_CHAT_MEMBERS = "leftChatMembers"
    CHANGED_CHAT_INFO = "changedChatInfo"
    CALLBACK_QUERY = "callbackQuery"


class Event(object):
    def __init__(self, type_, data):
        super(Event, self).__init__()

        self.type = type_
        self.data = data

        if type_ == EventType.NEW_MESSAGE:
            if 'text' in data:
                self.text = data['text']
            self.from_chat = data['chat']['chatId']
            self.message_author = data['from']
        
    def __repr__(self):
        return "Event(type='{self.type}', data='{self.data}')".format(self=self)
