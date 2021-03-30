from bot.bot import Bot


TOKEN = ""  # your token here

test_bot = Bot(token=TOKEN)


@test_bot.message_handler()
def message_cb(bot, event):
    bot.send_text(chat_id=event.from_chat, text=event.text)


@test_bot.button_handler()
def message_cb(bot, event):
    bot.send_text(event.data['message']['chat']['chatId'], text='Test')


test_bot.start_polling()
test_bot.idle()
