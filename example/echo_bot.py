from bot.bot import Bot
from bot.handler import MessageHandler

TOKEN = "" #your token here

bot = Bot(token=TOKEN)


def message_cb(bot, event):
    bot.send_text(chat_id=event.data['chat']['chatId'] text=event.data['text'])


bot.dispatcher.add_handler(MessageHandler(callback=message_cb))
bot.start_polling()
bot.idle()
