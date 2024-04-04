import json

from .constant import StyleType


class JsonSerializable(object):

    def to_json(self):
        raise NotImplementedError


class Dictionaryable(object):

    def to_dic(self):
        raise NotImplementedError


class JsonDeserializable(object):

    @classmethod
    def de_json(cls, json_string):
        raise NotImplementedError


class KeyboardButton(Dictionaryable, JsonSerializable):

    def __init__(self, text: str, style: str = 'primary', callbackData: str = None, url: str = None):
        self.text = text
        self.callbackData = callbackData
        self.style = style
        self.url = url

    def to_json(self):
        return json.dumps(self.to_dic())

    def to_dic(self):
        json_dic = {'text': self.text}
        if self.callbackData:
            json_dic['callbackData'] = self.callbackData
        if self.style:
            json_dic['style'] = self.style
        if self.url:
            json_dic['url'] = self.url
        return json_dic


class InlineKeyboardMarkup(Dictionaryable, JsonSerializable):

    def __init__(self, buttons_in_row=8):
        self.buttons_in_row = buttons_in_row
        self.keyboard = []

    def add(self, *args):
        i = 1
        row = []
        for button in args:
            row.append(button.to_dic())
            if i % self.buttons_in_row == 0:
                self.keyboard.append(row)
                row = []
            i += 1
        self.keyboard.append(row) if len(row) > 0 else None

    def row(self, *args):
        btn_array = []
        for button in args:
            btn_array.append(button.to_dic())
        self.keyboard.append(btn_array)
        return self

    def to_json(self):
        return json.dumps(self.keyboard)

    def to_dic(self):
        return self.keyboard


class Style(Dictionaryable, JsonSerializable):

    def __init__(self):
        self.ranges = []

    def add(self, offset, length, args=None):
        range_ = {"offset": offset, "length": length}
        if args is not None:
            self.ranges.append({**range_, **args})
        else:
            self.ranges.append(range_)

    def to_dic(self):
        return self.ranges

    def to_json(self):
        return json.dumps(self.ranges)


class Format(Dictionaryable, JsonSerializable):

    def __init__(self):
        self.styles = {}

    def add(self, style, offset, length, args=None):
        StyleType(style)
        if style in self.styles.keys():
            self.styles[style].add(offset, length, args)
        else:
            newStyle = Style()
            newStyle.add(offset, length, args)
            self.styles[style] = newStyle

    def to_dic(self):
        return self.styles

    def to_json(self):
        result = {}
        for key in self.styles.keys():
            result[key] = self.styles[key].to_dic()
        return json.dumps(result)
