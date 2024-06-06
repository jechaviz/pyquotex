import json
from quotexapi.ws.channels.base import Base

class SellOption(Base):
    name = 'sell_option'
    def __call__(self, options_ids):
        data = [{"ticket": id} for id in (options_ids if isinstance(options_ids, list) else [options_ids])]
        self.send_websocket_request(f'42["orders/cancel", {json.dumps(data)}]')
