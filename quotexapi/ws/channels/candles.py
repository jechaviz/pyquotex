import json
from quotexapi.ws.channels.base import Base

class GetCandles(Base):
    name = 'candles'
    def __call__(self, asset_id, offset, period, index):
        payload = {
            'id': asset_id,
            'index': index,
            'time': period,
            'offset': offset,
        }
        data = f"42['history/load/line',{json.dumps(payload)}]"
        self.send_websocket_request(data)
