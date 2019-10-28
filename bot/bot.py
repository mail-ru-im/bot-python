import cgi
import logging
import os
import re
from signal import signal, SIGINT, SIGTERM, SIGABRT
from threading import Thread, Lock
from time import sleep

import requests
from cached_property import cached_property
from expiringdict import ExpiringDict
from requests import Request
from requests.adapters import HTTPAdapter

import bot
from bot.dispatcher import Dispatcher, StopDispatching
from bot.event import Event, EventType
from bot.filter import Filter
from bot.handler import MessageHandler
from bot.util import signal_name_by_code

try:
    from urllib import parse as urlparse
except ImportError:
    # noinspection PyUnresolvedReferences
    import urlparse


class Bot(object):
    def __init__(self, token, api_url_base=None, name=None, version=None, timeout_s=20, poll_time_s=60):
        super(Bot, self).__init__()

        self.log = logging.getLogger(__name__)

        self.token = token
        self.api_base_url = "https://api.icq.net/bot/v1" if api_url_base is None else api_url_base
        self.name = name
        self.version = version
        self.timeout_s = timeout_s
        self.poll_time_s = poll_time_s
        self.last_event_id = 0

        self.dispatcher = Dispatcher(self)
        self.running = False

        self._uin = token.split(":")[-1]

        self.__lock = Lock()
        self.__polling_thread = None

        self.__sent_im_cache = ExpiringDict(max_len=2 ** 10, max_age_seconds=60)
        self.dispatcher.add_handler(SkipDuplicateMessageHandler(self.__sent_im_cache))

    @property
    def uin(self):
        return self._uin

    @cached_property
    def user_agent(self):
        return "{name}/{version} (uin={uin}) bot-python/{library_version}".format(
            name=self.name,
            version=self.version,
            uin="" if self.uin is None else self.uin,
            library_version=bot.__version__
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
                for event in response.json()["events"]:
                    self.dispatcher.dispatch(Event(type_=EventType(event["type"]), data=event["payload"]))
            except Exception:
                self.log.exception("Exception while polling!")

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
    def _signal_handler(self, sig, stack_frame):
        if self.running:
            self.log.debug("Stopping bot by signal '{name} ({code})'. Repeat for force exit.".format(
                name=signal_name_by_code(sig), code=sig
            ))
            self.stop()
        else:
            self.log.warning("Force exiting.")
            # It's fine here, this is standard way to force exit.
            # noinspection PyProtectedMember
            os._exit(1)

    def idle(self):
        for sig in (SIGINT, SIGTERM, SIGABRT):
            signal(sig, self._signal_handler)

        while self.running:
            sleep(1)

    def events_get(self, poll_time_s=None, last_event_id=None):
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

        if response.json()['events']:
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

    def send_text(self, chat_id, text, reply_msg_id=None, forward_chat_id=None, forward_msg_id=None):
        return self.http_session.get(
            url="{}/messages/sendText".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "text": text,
                "replyMsgId": reply_msg_id,
                "forwardChatId": forward_chat_id,
                "forwardMsgId": forward_msg_id
            },
            timeout=self.timeout_s
        )

    def send_file(self, chat_id, file_id=None, file=None, caption=None, reply_msg_id=None, forward_chat_id=None,
                  forward_msg_id=None):
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
                "forwardMsgId": forward_msg_id
            }
        )
        if file:
            request.method = "POST"
            request.files = {"file": file}

        return self.http_session.send(request.prepare(), timeout=self.timeout_s)

    def send_voice(self, chat_id, file_id=None, file=None, reply_msg_id=None, forward_chat_id=None,
                   forward_msg_id=None):
        request = Request(
            method="GET",
            url="{}/messages/sendVoice".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "fileId": file_id,
                "replyMsgId": reply_msg_id,
                "forwardChatId": forward_chat_id,
                "forwardMsgId": forward_msg_id
            }
        )

        if file:
            request.method = "POST"
            request.files = {"file": file}

        return self.http_session.send(request.prepare(), timeout=self.timeout_s)

    def edit_text(self, chat_id, msg_id, text):
        return self.http_session.get(
            url="{}/messages/editText".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "msgId": msg_id,
                "text": text
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

    def send_actions(self, chat_id, actions):
        return self.http_session.get(
            url="{}/chats/sendActions".format(self.api_base_url),
            params={
                "token": self.token,
                "chatId": chat_id,
                "actions": actions
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
