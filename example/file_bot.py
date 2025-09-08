from bot.bot import Bot
from bot.handler import MessageHandler
import os

TOKEN = os.getenv("VK_TOKEN")
URL = os.getenv("VK_URL")

bot = Bot(token=TOKEN, api_url_base=URL)


def message_cb(bot: Bot, event):
    # Send text data
    bot.send_file(chat_id=event.from_chat,file_content="Some Text", filename="Text.txt")
    # Send text with no name
    bot.send_file(chat_id=event.from_chat,file_content="Some Text")
    # Send binary data from File
    with open('logo_bot.png', 'rb') as bf:
        bot.send_file(chat_id=event.from_chat,file_content=bf)
    # Send binary data from bytes
    with open('logo_bot.png', 'rb') as bf:
        bot.send_file(chat_id=event.from_chat,file_content=bf.read(), filename="My File.png")



bot.dispatcher.add_handler(MessageHandler(callback=message_cb))
bot.start_polling()
bot.idle()
