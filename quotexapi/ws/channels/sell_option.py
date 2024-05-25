import json
from quotexapi.ws.channels.base import Base

class SellOption(Base):
    name = 'sell_option'
    def __call__(self, options_ids):
        if type(options_ids) != list:
            payload = {'ticket': options_ids}
            self.send_websocket_request(f"42['orders/cancel',{json.dumps(payload)}]")
        else:
            for ids in options_ids:
                payload = {'ticket': ids}
                self.send_websocket_request(f"42['orders/cancel',{json.dumps(payload)}]")
