import io
import logging.config
from time import sleep
from gtts import gTTS

from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
    CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
    EditedMessageHandler, DeletedMessageHandler, StartCommandHandler

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = ""
VERSION = "0.0.0"
TOKEN = "XXX.XXXXXXXXXX.XXXXXXXXXX:XXXXXXXXX"
OWNER = "XXXXXXXXX"


def start_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Hello! Let's start!")


def help_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Some message help")


def test_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="User command: {}".format(event.data['text']))


def unknown_command_cb(bot, event):
    user = event.data['chat']['chatId']
    (command, command_body) = event.data["text"].partition(" ")[::2]
    bot.send_text(
        chat_id=user,
        text="Unknown command '{message}' with body '{command_body}' received from '{source}'.".format(
            source=user, message=command[1:], command_body=command_body
        )
    )


def private_command_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Private user command: {}".format(event.data['text']))


def new_chat_members_cb(bot, event):
    bot.send_text(
        chat_id=event.data['chat']['chatId'],
        text="Welcome to chat! {users}, read the chat rules!".format(
            users=", ".join([u['userId'] for u in event.data['newMembers']])
        )
    )


def left_chat_members_cb(bot, event):
    bot.send_text(
        chat_id=event.data['chat']['chatId'],
        text="Say goodbye to {users}".format(
            users=", ".join([u['userId'] for u in event.data['leftMembers']])
        )
    )


def pinned_message_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Message {} was pinned".format(event.data['msgId']))


def unpinned_message_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Message {} was unpinned".format(event.data['msgId']))


def edited_message_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Message {} was edited".format(event.data['msgId']))


def deleted_message_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Message {} was deleted".format(event.data['msgId']))


def message_with_bot_mention_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Message with bot mention was received")


def mention_cb(bot, event):
    bot.send_text(
        chat_id=event.data['chat']['chatId'],
        text="Users {users} was mentioned".format(
            users=", ".join([p['payload']['userId'] for p in event.data['parts']])
        )
    )


def reply_to_message_cb(bot, event):
    msg_id = event.data['msgId']
    bot.send_text(
        chat_id=event.data['chat']['chatId'],
        text="Reply to message: {}".format(msg_id),
        reply_msg_id=msg_id
    )


def regexp_only_dig_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Only numbers! yes!")


def file_cb(bot, event):
    bot.send_text(
        chat_id=event.data['chat']['chatId'],
        text="Files with {filed} fileId was received".format(
            filed=", ".join([p['payload']['fileId'] for p in event.data['parts']])
        )
    )


def image_cb(bot, event):
    bot.send_text(
        chat_id=event.data['chat']['chatId'],
        text="Images with {filed} fileId was received".format(
            filed=", ".join([p['payload']['fileId'] for p in event.data['parts']])
        )
    )


def video_cb(bot, event):
    bot.send_text(
        chat_id=event.data['chat']['chatId'],
        text="Video with {filed} fileId was received".format(
            filed=", ".join([p['payload']['fileId'] for p in event.data['parts']])
        )
    )


def audio_cb(bot, event):
    bot.send_text(
        chat_id=event.data['chat']['chatId'],
        text="Audio with {filed} fileId was received".format(
            filed=", ".join([p['payload']['fileId'] for p in event.data['parts']])
        )
    )


def sticker_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Your sticker is so funny!")


def url_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Link was received")


def forward_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Forward was received")


def reply_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Reply was received")


def message_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'], text="Message was received")


def pin_cb(bot, event):
    # Bot should by admin in chat for call this method
    command, command_body = event.data["text"].partition(" ")[::2]
    bot.pin_message(chat_id=event.data['chat']['chatId'], msg_id=command_body)


def unpin_cb(bot, event):
    # Bot should by admin in chat for call this method
    command, command_body = event.data["text"].partition(" ")[::2]
    bot.unpin_message(chat_id=event.data['chat']['chatId'], msg_id=command_body)


def main():
    # Creating a new bot instance.
    bot = Bot(token=TOKEN, name=NAME, version=VERSION)

    # Registering handlers #
    # -------------------- #
    # Handler for start command
    bot.dispatcher.add_handler(StartCommandHandler(callback=start_cb))

    # Handler for help command
    bot.dispatcher.add_handler(HelpCommandHandler(callback=help_cb))

    # Any other user command handler
    bot.dispatcher.add_handler(CommandHandler(command="test", callback=test_cb))

    # Handler for feedback command
    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER))

    # Handler for unknown commands
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=unknown_command_cb))

    # Handler for private command with filter by user
    bot.dispatcher.add_handler(CommandHandler(
        command="restart",
        filters=Filter.sender(user_id=OWNER),
        callback=private_command_cb
    ))

    # Handler for add user to chat
    bot.dispatcher.add_handler(NewChatMembersHandler(callback=new_chat_members_cb))

    # Handler for left user from chat
    bot.dispatcher.add_handler(LeftChatMembersHandler(callback=left_chat_members_cb))

    # Handler for pinned message
    bot.dispatcher.add_handler(PinnedMessageHandler(callback=pinned_message_cb))

    # Handler for unpinned message
    bot.dispatcher.add_handler(UnPinnedMessageHandler(callback=unpinned_message_cb))

    # Handler for edited message
    bot.dispatcher.add_handler(EditedMessageHandler(callback=edited_message_cb))

    # Handler for deleted message
    bot.dispatcher.add_handler(DeletedMessageHandler(callback=deleted_message_cb))

    # Handler for message with bot mention
    bot.dispatcher.add_handler(MessageHandler(
        filters=Filter.message & Filter.mention(user_id=bot.uin),
        callback=message_with_bot_mention_cb
    ))

    # Handler for mention something else
    bot.dispatcher.add_handler(MessageHandler(
        filters=Filter.mention() & ~Filter.mention(user_id=bot.uin),
        callback=mention_cb
    ))

    # Handler for simple text message without media content
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.text, callback=message_cb))

    # Handler with regexp filter
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.regexp("^\d*$"), callback=regexp_only_dig_cb))

    # Handler for no media file. For example, text file
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.data, callback=file_cb))

    # Handlers for other file types
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.image, callback=image_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.video, callback=video_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.audio, callback=audio_cb))

    # Handler for sticker
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.sticker, callback=sticker_cb))

    # Handler for url
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.url & ~Filter.sticker, callback=url_cb))

    # Handlers for forward and reply getting
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.forward, callback=forward_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=Filter.reply, callback=reply_cb))

    # Send command like this:
    # /pin 6752793278973351456
    # 6752793278973351456 - msgId
    # Handler for pin command
    bot.dispatcher.add_handler(CommandHandler(command="pin", callback=pin_cb))

    # Send command like this:
    # /unpin 6752793278973351456
    # 6752793278973351456 - msgId
    # Handler for unpin command
    bot.dispatcher.add_handler(CommandHandler(command="unpin", callback=unpin_cb))

    # Starting a polling thread watching for new events from server. This is a non-blocking call
    # ---------------------------------------------------------------------------------------- #
    bot.start_polling()

    # Call bot methods
    # -------------- #
    # Get info about bot
    bot.self_get()

    # Send message
    response = bot.send_text(chat_id=OWNER, text="Hello")
    msg_id = response.json()['msgId']

    # Reply
    bot.send_text(chat_id=OWNER, text="Reply to 'Hello'", reply_msg_id=msg_id)

    # Forward
    bot.send_text(chat_id=OWNER, text="Forward 'Hello'", forward_msg_id=msg_id, forward_chat_id=OWNER)

    # Send binary file
    with io.StringIO() as file:
        file.write('x'*100)
        file.name = "file.txt"
        file.seek(0)
        response = bot.send_file(chat_id=OWNER, file=file.read(), caption="binary file caption")
        file_id = response.json()['fileId']

    # Send file by file_id
    bot.send_file(chat_id=OWNER, file_id=file_id, caption="file_id file caption")

    # Send file by file_id as reply to message
    bot.send_file(chat_id=OWNER, file_id=file_id, caption="file_id file caption", reply_msg_id=msg_id)

    # Forward file by file_id
    bot.send_file(
        chat_id=OWNER,
        file_id=file_id,
        caption="file_id file caption",
        forward_msg_id=msg_id,
        forward_chat_id=OWNER
    )

    # Send voice file
    with io.BytesIO() as file:
        gTTS('Hello everybody!').write_to_fp(file)
        file.name = "hello_voice.mp3"
        file.seek(0)
        response = bot.send_voice(chat_id=OWNER, file=file.read())
        hello_voice_file_id = response.json()['fileId']

    # Send voice by file_id
    bot.send_voice(chat_id=OWNER, file_id=hello_voice_file_id)

    # Edit text
    msg_id = bot.send_text(chat_id=OWNER, text="Message to be edited").json()['msgId']
    bot.edit_text(chat_id=OWNER, msg_id=msg_id, text="edited text")

    # Delete message
    msg_id = bot.send_text(chat_id=OWNER, text="Message to be deleted").json()['msgId']
    bot.delete_messages(chat_id=OWNER, msg_id=msg_id)

    # Send typing action
    bot.send_actions(chat_id=OWNER, actions=["typing"])
    sleep(1)
    # Stop typing
    bot.send_actions(chat_id=OWNER, actions=[])

    # Get info about chat
    bot.get_chat_info(chat_id=OWNER)

    # Get file info
    bot.get_file_info(file_id=file_id)

    bot.idle()


if __name__ == "__main__":
    main()
