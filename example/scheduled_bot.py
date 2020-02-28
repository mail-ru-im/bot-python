import schedule
import time
from bot.bot import Bot

TOKEN = "" #your toke here
bot = Bot(token=TOKEN)

chats_to_send_notifications = [
    "chat_to_recieve_messages",  # nick of a public group chat
    "AoLFuNFynm67V2xGFX000",  # stamp of private group chat
    "some_nick",  # nick of a person
    "68250238000@chat.agent"  # default chat id
]
text_to_send = "Let's go home!"


def send_alert():
    for chat in chats_to_send_notifications:

        bot.send_text(chat_id=chat, text=text_to_send)


schedule.every().day.at("19:00").do(send_alert)
while True:
    schedule.run_pending()
    time.sleep(1)
