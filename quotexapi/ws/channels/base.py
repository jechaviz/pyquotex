class Base(object):
    def __init__(self, api):
        self.api = api

    def send_websocket_request(self, data):
        return self.api.send_request(data)
