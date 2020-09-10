from bot.bot import Bot
from bot.handler import MessageHandler

import logging.config

logging.config.fileConfig("logging.ini")

TOKEN = "" #your token here

bot = Bot(token=TOKEN, api_url_base="", is_myteam=True)


def message_cb(bot, event):
    bot.send_text(chat_id=event.from_chat, text="Hello!")
    resp = bot.create_chat(name="Test chat")
    bot.send_text(chat_id=event.from_chat, text=resp.json()['sn'])
    bot.add_chat_members(chat_id=resp.json()['sn'], members=["user1@myteam.ru", "user2@myteam.ru", "user3@myteam.ru"])
    bot.send_text(chat_id=resp.json()['sn'], text="Hello! And Goodbye!")
    bot.delete_chat_members(chat_id=resp.json()['sn'], members=["user2@myteam.ru", "user3@myteam.ru"])
    bot.send_text(chat_id=event.from_chat, text="Bye!")    


bot.dispatcher.add_handler(MessageHandler(callback=message_cb))
bot.start_polling()
bot.idle()
