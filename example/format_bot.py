from bot.bot import Bot
from bot.handler import MessageHandler
from bot.constant import ParseMode
from bot.types import Format

import logging.config

logging.config.fileConfig("logging.ini")

TOKEN = "" #your token here

bot = Bot(token=TOKEN, api_url_base="")

def message_cb(bot, event):
    bot.send_text(chat_id=event.from_chat, text="*_Hello_*", parse_mode="MarkdownV2")
    bot.send_text(chat_id=event.from_chat, text="<s>|</s> World! <s>|</s>", parse_mode="HTML")

    format_ = Format()
    format_.add("bold", 0, 2)
    format_.add("link", 3, 4, {"url": "http://www.mail.ru"})

    bot.send_text(chat_id=event.from_chat, text="bo best", format_=format_)


bot.dispatcher.add_handler(MessageHandler(callback=message_cb))
bot.start_polling()
bot.idle()
