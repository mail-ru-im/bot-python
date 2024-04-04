import pytest
from bot.bot import Bot
from threading import Thread

import server

NAME = ""
VERSION = "0.0.0"
TOKEN = "XXX.XXXXXXXXXX.XXXXXXXXXX:XXXXXXXXX"
OWNER = "XXXXXXXXX"
TEST_CHAT = "XXXXX"
TEST_USER = "XXXXX"
API_URL = "http://localhost:8080"


bot = Bot(token=TOKEN, api_url_base=API_URL, is_myteam=True)


@pytest.fixture(scope='session', autouse=True)
def launch_server():
    thread = Thread(target=server.startServer)
    thread.daemon = True
    thread.start()


def test_EventsGet():
    response = bot.events_get(1, 0)
    if "description" in response.json():
        pytest.xfail(response.json()["description"])

    assert "events" in response.json()
    for event in response.json()["events"]:
        if "type" not in event or "payload" not in event:
            pytest.xfail("Bad format of response")


def test_SelfGet():
    response = bot.self_get()
    if "description" in response.json():
        pytest.xfail(response.json()["description"])

    if "ok" not in response.json() or response.json()["ok"] is False:
        pytest.xfail("Answer isn't ok")

    if (
        "firstName" not in response.json() or "nick" not in response.json() or
        "userId" not in response.json()
    ):
        pytest.xfail(response.json()["description"])


def test_chats_GetInfo_OK():
    response = bot.get_chat_info(TEST_CHAT)
    assert response

    if "description" in response.json():
        pytest.xfail(response.json()["description"])

    if "ok" not in response.json() or response.json()["ok"] is False:
        pytest.xfail("Answer isn't ok")

    if (
        "about" not in response.json() or "language" not in response.json() or
        "firstName" not in response.json() or "lastName" not in response.json()
    ):
        pytest.xfail("Bad format of response 'getInfo'")


def test_chats_GetInfo_ERROR():
    pass  # response = bot.get_chat_info("111")


def test_plug_error():
    pytest.xfail("Plug")


def test_plug_ok():
    pass
