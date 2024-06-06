import json
from quotexapi.ws.channels.base import Base

class Ssid(Base):
    name = "ssid"
    def __call__(self, ssid):
        payload = {
            "session": ssid,
            "isDemo": self.api.account_type,
            "tournamentId": 0
        }
        data = f'42["authorization",{json.dumps(payload)}]'
        self.send_websocket_request(data)