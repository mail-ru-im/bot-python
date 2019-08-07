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


class Event(object):
    def __init__(self, type_, data):
        super(Event, self).__init__()

        self.type = type_
        self.data = data

    def __repr__(self):
        return "Event(type='{self.type}', data='{self.data}')".format(self=self)

