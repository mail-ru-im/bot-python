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
            self.msgId = data.get('msgId')
            self.text = data.get('text')
            self.format = data.get('format')
            self.from_chat = data['chat']['chatId']
            self.chat_type = data['chat']['type']
            self.message_author = data.get('from', {})

        elif type_ == EventType.CALLBACK_QUERY:
            self.msgId = data['message'].get('msgId')
            self.callback_query = data['callbackData']
            self.from_chat = data['message']['chat']['chatId']
            self.chat_type = data['message']['chat']['type']
            self.message_author = data['queryId'].split(':')[1]
            self.queryId = data['queryId']
        
    def __repr__(self):
        return "Event(type='{self.type}', data='{self.data}')".format(self=self)
