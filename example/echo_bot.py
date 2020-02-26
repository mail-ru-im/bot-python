from bot.bot import Bot
from bot.handler import MessageHandler

TOKEN = "" #your toke here
bot = Bot(token=TOKEN)
bot.start_polling()


def message_cb(bot, event):
    print(event)
    bot.send_text(chat_id=event.from_chat, text=event.text)


bot.dispatcher.add_handler(MessageHandler(callback=message_cb))
