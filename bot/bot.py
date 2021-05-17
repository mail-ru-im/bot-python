import cgi
import logging
import sys
import re
from signal import signal, SIGINT, SIGTERM, SIGABRT
from threading import Thread, Lock
from time import sleep
import types
import json

import requests
from cached_property import cached_property
from expiringdict import ExpiringDict
from requests import Request
from requests.adapters import HTTPAdapter

from . import __version__ as version
from .dispatcher import Dispatcher
from .event import Event
from .handler import *
from .util import signal_name_by_code
from .myteam import add_chat_members, create_chat
from .types import InlineKeyboardMarkup, Format
from .constant import ParseMode


def keyboard_to_json(keyboard_markup):
    if isinstance(keyboard_markup, InlineKeyboardMarkup):
        return keyboard_markup.to_json()
    elif isinstance(keyboard_markup, list):
        return json.dumps(keyboard_markup)
    else:
        return keyboard_markup

def format_to_json(format_):
    if isinstance(format_, Format):
        return format_.to_json()
    elif isinstance(format_, list):
        return json.dumps(format_)
    else:
        return format_

class Bot(object):
    def __init__(self, token: str, api_url_base: str = None, name: str = None, version: str = None,
                 timeout_s: int = 20, poll_time_s: int = 60, is_myteam: bool = False):
        super(Bot, self).__init__()

        self.log = logging.getLogger(__name__)

        self.token = token
        self.api_base_url = "https://api.icq.net/bot/v1" if api_url_base is None else api_url_base
        self.name = name
        self.version = version
        self.timeout_s = timeout_s
        self.poll_time_s = poll_time_s
        self.last_event_id = 0
        self.is_myteam = is_myteam

        self.dispatcher = Dispatcher(self)
        self.running = False

        self._uin = token.split(":")[-1]

        self.__lock = Lock()
        self.__polling_thread = None
        self.__sent_im_cache = ExpiringDict(max_len=2 ** 10, max_age_seconds=60)
        self.dispatcher.add_handler(SkipDuplicateMessageHandler(self.__sent_im_cache))

        if self.is_myteam:
            self.add_chat_members = types.MethodType(add_chat_members, self)
            self.create_chat = types.MethodType(create_chat, self)

    @property
    def uin(self):
        return self._uin

    @cached_property
    def user_agent(self):

        return "{name}/{version} (uin={uin}) bot-python/{library_version}".format(
            name=self.name if self.name is not None else requests.get(url="{}/self/get".format(self.api_base_url),
                                                                      params={"token": self.token}
                                                                      ).json().get('nick'),
            # name=self.name,
            version=self.version if self.version is not None else 'base',
            uin="" if self.uin is None else self.uin,
            library_version=version
        )

    @cached_property
    def http_session(self):
        session = requests.Session()

        for scheme in ("http://", "https://"):
            session.mount(scheme, BotLoggingHTTPAdapter(bot=self))

        return session

    def _start_polling(self):
        while self.running:
            # Exceptions should not stop polling thread.
            # noinspection PyBroadException
            try:
                response = self.events_get()

                if response:
                    if "description" in response.json() and response.json()["description"] == 'Invalid token':
                        raise InvalidToken(response.json())

                for event in response.json()["events"]:
                    self.dispatcher.dispatch(Event(type_=EventType(event["type"]), data=event["payload"]))
            except InvalidToken as e:
                self.log.exception("InvalidToken: {e}".format(e=e))
                sleep(5)
            except Exception as e:
                self.log.exception("Exception while polling: {e}".format(e=e))

    def start_polling(self):
        with self.__lock:
            if not self.running:
                self.log.info("Starting polling.")

                self.running = True

                self.__polling_thread = Thread(target=self._start_polling)
                self.__polling_thread.start()

    def stop(self):
        with self.__lock:
            if self.running:
                self.log.info("Stopping bot.")

                self.running = False

                self.__polling_thread.join()

    # noinspection PyUnusedLocal
    def _signal_handler(self, sig: int):
        if self.running:
            self.log.debug("Stopping bot by signal '{name} ({code})'. Repeat for force exit.".format(
                name=signal_name_by_code(sig), code=sig
            ))
            self.stop()
        else:
            self.log.warning("Force exiting.")
            # It's fine here, this is standard way to force exit.
            # noinspection PyProtectedMember
            sys.exit(1)

    def idle(self):
        for sig in (SIGINT, SIGTERM, SIGABRT):
            signal(sig, self._signal_handler)

        while self.running:
            sleep(1)

    def events_get(self, poll_time_s: int = None, last_event_id: int = None):
        poll_time_s = self.poll_time_s if poll_time_s is None else poll_time_s
        last_event_id = self.last_event_id if last_event_id is None else last_event_id

        response = self.http_session.get(
            url="{}/events/get".format(self.api_base_url),
            params={
                "token": self.token,
                "pollTime": poll_time_s,
                "lastEventId": last_event_id
            },
            timeout=poll_time_s + self.timeout_s
        )

        if 'events' in response.json() and response.json()['events']:
            self.last_event_id = max(response.json()['events'], key=lambda e: e['eventId'])['eventId']

        return response

    def self_get(self):
        return self.http_session.get(
            url="{}/self/get".format(self.api_base_url),
            params={
                "token": self.token
            },
            timeout=self.timeout_s
        )

    def default_handler(self):
        def decorate(handler):
            self.dispatcher.add_handler(handler=DefaultHandler(callback=handler))
            return handler

        return decorate

    def new_member_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=NewChatMembersHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def member_left_chat_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=LeftChatMembersHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def pin_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=PinnedMessageHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def unpin_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=UnPinnedMessageHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def message_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=MessageHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def edit_msg_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=EditedMessageHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def delete_msg_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=DeletedMessageHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def command_handler(self, command=None, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=CommandHandler(callback=handler, command=command, filters=filters))
            return handler

        return decorate

    def help_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=HelpCommandHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def start_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=StartCommandHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def unknown_cmd_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=UnknownCommandHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def button_handler(self, filters=None):
        def decorate(handler):
            self.dispatcher.add_handler(handler=BotButtonCommandHandler(callback=handler, filters=filters))
            return handler

        return decorate

    def send_text(self, chat_id: str, text: str, reply_msg_id=None, forward_chat_id=None, forward_msg_id=None,
                  inline_keyboard_markup=None, parse_mode=None, format_=None):
        if parse_mode and format_:
            raise Exception("Cannot use format and parseMode fields at one time")
        if parse_mode:
            ParseMode(parse_mode)
        return self.http_session.get(
            url="{}/messages/sendText".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "text": text,
                "replyMsgId": reply_msg_id,
                "forwardChatId": forward_chat_id,
                "forwardMsgId": forward_msg_id,
                "inlineKeyboardMarkup": keyboard_to_json(inline_keyboard_markup),
                "parseMode": parse_mode,
                "format": format_to_json(format_)
            },
            timeout=self.timeout_s
        )

    def send_file(self, chat_id, file_id=None, file=None, caption=None, reply_msg_id=None, forward_chat_id=None,
                  forward_msg_id=None, inline_keyboard_markup=None, parse_mode=None, format_=None):
        if parse_mode and format_:
            raise Exception("Cannot use format and parseMode fields at one time")
        if parse_mode:
            ParseMode(parse_mode)
        request = Request(
            method="GET",
            url="{}/messages/sendFile".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "fileId": file_id,
                "caption": caption,
                "replyMsgId": reply_msg_id,
                "forwardChatId": forward_chat_id,
                "forwardMsgId": forward_msg_id,
                "inlineKeyboardMarkup": keyboard_to_json(inline_keyboard_markup),
                "parseMode": parse_mode,
                "format": format_to_json(format_)
            }
        )
        if file:
            request.method = "POST"
            request.files = {"file": file}

        return self.http_session.send(request.prepare(), timeout=self.timeout_s)

    def send_voice(self, chat_id, file_id=None, file=None, reply_msg_id=None, forward_chat_id=None,
                   forward_msg_id=None, inline_keyboard_markup=None):
        request = Request(
            method="GET",
            url="{}/messages/sendVoice".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "fileId": file_id,
                "replyMsgId": reply_msg_id,
                "forwardChatId": forward_chat_id,
                "forwardMsgId": forward_msg_id,
                "inlineKeyboardMarkup": keyboard_to_json(inline_keyboard_markup)
            }
        )

        if file:
            request.method = "POST"
            request.files = {"file": file}

        return self.http_session.send(request.prepare(), timeout=self.timeout_s)

    def edit_text(self, chat_id, msg_id, text, inline_keyboard_markup=None, parse_mode=None, format_=None):
        if parse_mode and format_:
            raise Exception("Cannot use format and parseMode fields at one time")
        if parse_mode:
            ParseMode(parse_mode)
        return self.http_session.get(
            url="{}/messages/editText".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "msgId": msg_id,
                "text": text,
                "inlineKeyboardMarkup": keyboard_to_json(inline_keyboard_markup),
                "parseMode": parse_mode,
                "format": format_to_json(format_)
            },
            timeout=self.timeout_s
        )

    def delete_messages(self, chat_id, msg_id):
        return self.http_session.get(
            url="{}/messages/deleteMessages".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "msgId": msg_id
            },
            timeout=self.timeout_s
        )

    def answer_callback_query(self, query_id, text, show_alert=False, url=None):
        return self.http_session.get(
            url="{}/messages/answerCallbackQuery".format(self.api_base_url),
            params={
                "token": self.token,
                "queryId": query_id,
                "text": text,
                "showAlert": 'true' if show_alert else 'false',
                "url": url
            }
        )

    def send_actions(self, chat_id, actions):
        return self.http_session.get(
            url="{}/chats/sendActions".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "actions": actions if len(actions) else ''
            },
            timeout=self.timeout_s
        )

    def get_chat_info(self, chat_id):
        return self.http_session.get(
            url="{}/chats/getInfo".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id
            },
            timeout=self.timeout_s
        )

    def get_chat_admins(self, chat_id):
        return self.http_session.get(
            url="{}/chats/getAdmins".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id
            },
            timeout=self.timeout_s
        )

    def get_chat_members(self, chat_id, cursor=None):
        return self.http_session.get(
            url="{}/chats/getMembers".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "cursor": cursor
            },
            timeout=self.timeout_s
        )

    def get_chat_blocked_users(self, chat_id):
        return self.http_session.get(
            url="{}/chats/getBlockedUsers".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id
            },
            timeout=self.timeout_s
        )

    def get_chat_pending_users(self, chat_id):
        return self.http_session.get(
            url="{}/chats/getPendingUsers".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id
            },
            timeout=self.timeout_s
        )

    def chat_block_user(self, chat_id, user_id, del_last_messages=False):
        return self.http_session.get(
            url="{}/chats/blockUser".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "userId": user_id,
                "delLastMessages": str(del_last_messages).lower()
            },
            timeout=self.timeout_s
        )

    def chat_unblock_user(self, chat_id, user_id):
        return self.http_session.get(
            url="{}/chats/unblockUser".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "userId": user_id
            },
            timeout=self.timeout_s
        )

    def chat_resolve_pending(self, chat_id, approve=True, user_id="", everyone=False):
        return self.http_session.get(
            url="{}/chats/resolvePending".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "approve": str(approve).lower(),
                "userId": user_id,
                "everyone": str(everyone).lower()
            },
            timeout=self.timeout_s
        )

    def set_chat_title(self, chat_id, title):
        return self.http_session.get(
            url="{}/chats/setTitle".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "title": title
            },
            timeout=self.timeout_s
        )

    def set_chat_about(self, chat_id, about):
        return self.http_session.get(
            url="{}/chats/setAbout".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "about": about
            },
            timeout=self.timeout_s
        )

    def set_chat_rules(self, chat_id, rules):
        return self.http_session.get(
            url="{}/chats/setRules".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "rules": rules
            },
            timeout=self.timeout_s
        )

    def get_file_info(self, file_id):
        return self.http_session.get(
            url="{}/files/getInfo".format(self.api_base_url),
            params={
                "token": self.token,
                "fileId": file_id
            },
            timeout=self.timeout_s
        )

    def pin_message(self, chat_id, msg_id):
        return self.http_session.get(
            url="{}/chats/pinMessage".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "msgId": msg_id
            },
            timeout=self.timeout_s
        )

    def unpin_message(self, chat_id, msg_id):
        return self.http_session.get(
            url="{}/chats/unpinMessage".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "msgId": msg_id
            },
            timeout=self.timeout_s
        )

    def delete_chat_members(self, chat_id, members):
        return self.http_session.get(
            url="{}/chats/members/delete".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "members": json.dumps([{"sn": m} for m in members])
            }
        )


class LoggingHTTPAdapter(HTTPAdapter):
    _LOG_MIME_TYPE_REGEXP = re.compile(
        r"^(?:text(?:/.+)?|application/(?:json|javascript|xml|x-www-form-urlencoded))$", re.IGNORECASE
    )

    @staticmethod
    def _is_loggable(headers):
        return LoggingHTTPAdapter._LOG_MIME_TYPE_REGEXP.search(cgi.parse_header(headers.get("Content-Type", ""))[0])

    @staticmethod
    def _headers_to_string(headers):
        return "\n".join((u"{key}: {value}".format(key=key, value=value) for (key, value) in headers.items()))

    @staticmethod
    def _body_to_string(body):
        return body.decode("utf-8") if isinstance(body, bytes) else body

    def __init__(self, *args, **kwargs):
        super(LoggingHTTPAdapter, self).__init__(*args, **kwargs)

        self.log = logging.getLogger(__name__)

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug(u"{method} {url}\n{headers}{body}".format(
                method=request.method,
                url=request.url,
                headers=LoggingHTTPAdapter._headers_to_string(request.headers),
                body="\n\n" + (
                    LoggingHTTPAdapter._body_to_string(request.body) if
                    LoggingHTTPAdapter._is_loggable(request.headers) else "[binary data]"
                ) if request.body is not None else ""
            ))

        response = super(LoggingHTTPAdapter, self).send(request, stream, timeout, verify, cert, proxies)

        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug(u"{status_code} {reason}\n{headers}{body}".format(
                status_code=response.status_code,
                reason=response.reason,
                headers=LoggingHTTPAdapter._headers_to_string(response.headers),
                body="\n\n" + (
                    response.text if LoggingHTTPAdapter._is_loggable(response.headers) else "[binary data]"
                ) if response.content is not None else ""
            ))

        return response


class BotLoggingHTTPAdapter(LoggingHTTPAdapter):
    def __init__(self, bot, *args, **kwargs):
        super(BotLoggingHTTPAdapter, self).__init__(*args, **kwargs)

        self.bot = bot

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        request.headers["User-Agent"] = self.bot.user_agent
        return super(BotLoggingHTTPAdapter, self).send(request, stream, timeout, verify, cert, proxies)


class FileNotFoundException(Exception):
    pass


class SkipDuplicateMessageHandler(MessageHandler):
    def __init__(self, cache):
        super(SkipDuplicateMessageHandler, self).__init__(filters=Filter.message)

        self.cache = cache

    def check(self, event, dispatcher):
        if super(SkipDuplicateMessageHandler, self).check(event=event, dispatcher=dispatcher):
            if self.cache.get(event.data["msgId"]) == event.data["text"]:
                raise StopDispatching


class InvalidToken(Exception):
    pass
