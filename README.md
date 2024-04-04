<img src="logo_bot.png" width="100" height="100">

# VK Teams Bot API for Python
[![Python package](https://github.com/mail-ru-im/bot-python/actions/workflows/python-package.yml/badge.svg)](https://github.com/mail-ru-im/bot-python/actions/workflows/python-package.yml)
[![codecov](https://codecov.io/github/mail-ru-im/bot-python/graph/badge.svg?token=ObUFRWSyGv)](https://codecov.io/github/mail-ru-im/bot-python)
[![go.dev reference](https://img.shields.io/badge/go.dev-reference-007d9c?logo=go&logoColor=white&style=flat)](https://pkg.go.dev/github.com/mail-ru-im/bot-golang)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

### [<img src="logo_msg.png" width="16"> VK Teams API Specification](https://teams.vk.com/botapi/)

## Getting started

* Create your own bot by sending the _/newbot_ command to _Metabot_ and follow the instructions.
    >Note: a bot can only reply after the user has added it to his contact list, or if the user was the first to start a dialogue.
* You can configure the domain that hosts your VK Teams server. When instantiating the Bot class, add the address of your domain.
* An example of how to use the framework can be seen in _example/test_bot.py_

## Installing
Install using pip:
```bash
pip install --upgrade mailru-im-bot
```

Install from sources:
```bash
git clone https://github.com/mail-ru-im/bot-python.git
cd bot-python
python setup.py install
```