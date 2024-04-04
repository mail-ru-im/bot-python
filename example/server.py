# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse


hostName = "localhost"
serverPort = 8080


class MyServer(BaseHTTPRequestHandler):

    def do_GET(self):
        self._do()

    def do_POST(self):
        self._do()

    def do_DELETE(self):
        self._do()

    def do_HEAD(self):
        self._do()

    def _do(self):
        o = urlparse.urlparse(self.path)
        query_params = urlparse.parse_qs(o.query)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        if 'token' not in query_params:
            self.tokenError()

        if o.path == '/self/get':  # добавить проверку параметров в куери парамсах
            self.wfile.write(bytes(self._SelfGet(), 'utf-8'))
        elif o.path == '/events/get':
            self.wfile.write(bytes(self._EventsGet(), 'utf-8'))
        elif o.path == '/chats/getInfo':
            self.wfile.write(bytes(self._GetInfo(), 'utf-8'))
        else:
            self.defaultOk()

    def _SelfGet(self):
        return "{\
            \"firstName\": \"test_bot\",\
            \"nick\": \"test_bot\",\
            \"userId\": \"100000\",\
            \"ok\": true\
        }"

    def _EventsGet(self):
        return "{\
            \"ok\": true,\
            \"events\": [\
                {\
                    \"eventId\": 1,\
                    \"type\": \"newMessage\",\
                    \"payload\": {\
                        \"msgId\": \"57883346846815030\",\
                        \"chat\": {\
                            \"chatId\": \"681869378@chat.agent\",\
                            \"type\": \"channel\",\
                            \"title\": \"The best channel\"\
                        },\
                        \"from\": {\
                            \"userId\": \"1234567890\",\
                            \"firstName\": \"Name\",\
                            \"lastName\": \"SurName\"\
                        },\
                        \"timestamp\": 1546290000,\
                        \"text\": \"Hello!\",\
                        \"parts\": [\
                            {\
                                \"type\": \"sticker\",\
                                \"payload\": {\
                                    \"fileId\": \"2IWuJzaNWCJZxJWCvZhDYuJ5XDsr7hU\"\
                                }\
                            }\
                        ]\
                    }\
                },\
                {\
                    \"eventId\": 2,\
                    \"type\": \"editedMessage\",\
                    \"payload\": {\
                        \"msgId\": \"57883346846815030\",\
                        \"chat\": {\
                            \"chatId\": \"681869378@chat.agent\",\
                            \"type\": \"channel\",\
                            \"title\": \"The best channel\"\
                        },\
                        \"from\": {\
                            \"userId\": \"1234567890\",\
                            \"firstName\": \"Name\",\
                            \"lastName\": \"SurName\"\
                        },\
                        \"timestamp\": 1546290000,\
                        \"text\": \"Hello!\",\
                        \"editedTimestamp\": 1546290099\
                    }\
                }\
            ]\
        }"

    def _GetInfo(self):
        return "{\
            \"about\": \"some text\",\
            \"firstName\": \"first\",\
            \"language\": \"en\",\
            \"lastName\": \"last\",\
            \"type\": \"private\",\
            \"ok\": true\
        }"

    def tokenError(self):
        self.wfile.write(bytes("{\"ok\": false, \"description\": \"Invalid token\"}", "utf-8"))

    def badRequest(self):
        self.wfile.write(bytes("{\"ok\": false, \"description\": \"bad request\"}", "utf-8"))

    def defaultOk(self):
        self.wfile.write(bytes("{\"ok\": true, \"description\": \"ok\"}", "utf-8"))


def startServer():
    webServer = HTTPServer((hostName, serverPort), MyServer)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()


if __name__ == "__main__":
    startServer()
