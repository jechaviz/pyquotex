import os
import json
import time
import asyncio
import logging
import websocket
from .. import global_value

logger = logging.getLogger(__name__)


class WebsocketClient():
    """Class to work with Quotex API websocket."""
    def __init__(self, api):
        self.api = api
        self.headers = {'User-Agent': self.api.session_data.get('user_agent')}
        websocket.enableTrace(self.api.trace_ws)
        self.ws = websocket.WebSocketApp(
            f'wss://ws2.{self.api.ws_host}/socket.io/?EIO=3&transport=websocket',
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
            on_ping=self.on_ping,
            on_pong=self.on_pong,
            header=self.headers,
            cookie=self.api.session_data.get('cookies'),
        )

    def keep_alive(self):
        self.ws.run_forever(ping_interval=10, ping_timeout=10)

    def on_message(self, ws, message):
        global_value.ssl_Mutual_exclusion = True
        current_time = time.localtime()
        if current_time.tm_sec in [0, 20, 40]:
            self.ws.send("42['tick']")
        self.handle_authorization(message)
        self.handle_message(message)
        global_value.ssl_Mutual_exclusion = False

    def handle_message(self, message):
        try:
            message = message[1:].decode()
            logger.debug(message)
            message = json.loads(message)
            self.set_instruments(message)
            self.api.api_data = message
            self.process_message(message)
        except:
            pass
        self.handle_disconnection(message)
        self.handle_temporary_status(message)

    def set_instruments(self, message):
        if 'call' in str(message) or 'put' in str(message):
            self.api.instruments = message

    def process_message(self, message):
        self.handle_instruments(message)
        self.handle_signals(message)
        self.handle_balance(message)
        self.handle_candles(message)
        self.handle_buy(message)
        self.handle_sold_options(message)
        self.handle_deals(message)
        self.handle_training_balance_edit(message)
        self.handle_websocket_error(message)
        self.handle_remaining(message)

    def handle_authorization(self, message):
        if 'authorization/reject' in str(message):
            self.handle_rejected_authorization(message)
        elif 's_authorization' in str(message):
            global_value.check_accepted_connection = 1
        return bool(global_value.check_accepted_connection)

    def handle_rejected_authorization(self, message):
        session_file = os.path.join(self.api.resource_path, 'session.json')
        if os.path.isfile(session_file):
            os.remove(session_file)
        global_value.SSID = None
        global_value.check_rejected_connection = 1

    def handle_instruments(self, message):
        if 'instruments/list' in str(message):
            global_value.started_listen_instruments = True

    def handle_signals(self, message):
        if message.get('signals'):
            time_in = message.get('time')
            for i in message['signals']:
                try:
                    self.api.signal_data[i[0]] = {}
                    self.api.signal_data[i[0]][i[2]] = {}
                    self.api.signal_data[i[0]][i[2]]['dir'] = i[1][0]['signal']
                    self.api.signal_data[i[0]][i[2]]['duration'] = i[1][0]['timeFrame']
                except:
                    self.api.signal_data[i[0]] = {}
                    self.api.signal_data[i[0]][time_in] = {}
                    self.api.signal_data[i[0]][time_in]['dir'] = i[1][0][1]
                    self.api.signal_data[i[0]][time_in]['duration'] = i[1][0][0]

    def handle_balance(self, message):
        if message.get('liveBalance') or message.get('demoBalance'):
            self.api.account_balance = message

    def handle_candles(self, message):
        if message.get('index'):
            self.api.candles._list = message

    def handle_buy(self, message):
        if message.get('id'):
            self.api.buy_successful = message
            self.api.buy_id = message['id']
            self.api.timesync.server_timestamp = message['closeTimestamp']

    def handle_sold_options(self, message):
        if message.get('ticket'):
            self.api.sold_options_respond = message

    def handle_deals(self, message):
        if message.get('deals'):
            for deal in message['deals']:
                self.api.profit_in_operation = deal['profit']
                deal['win'] = True if message['profit'] > 0 else False
                deal['game_state'] = 1
                self.api.listinfodata.set(deal['win'], deal['game_state'], deal['id'])

    def handle_training_balance_edit(self, message):
        if message.get('isDemo') and message.get('balance'):
            self.api.training_balance_edit_request = message

    def handle_websocket_error(self, message):
        if message.get('error'):
            global_value.websocket_error_reason = message.get('error')
            global_value.check_websocket_if_error = True
            if global_value.websocket_error_reason == 'not_money':
                self.api.account_balance = {'liveBalance': 0}

    def handle_disconnection(self, message):
        if str(message) == '41':
            print('Disconnection event triggered by the platform, causing automatic reconnection.')
            global_value.check_websocket_if_connect = 0
            asyncio.run(self.api.reconnect())

    def handle_temporary_status(self, message):
        if '51-' in str(message):
            self.api._temp_status = str(message)
        elif self.api._temp_status == """451-['settings/list',{'_placeholder':true,'num':0}]""":
            self.api.settings_list = message
            self.api._temp_status = ''
        elif self.api._temp_status == """451-['history/list/v2',{'_placeholder':true,'num':0}]""":
            self.api.candles._list = message['candles']
            self.api.candle_v2_data[message['asset']] = message
            self.api.candle_v2_data[message['asset']]['candles'] = [{'t': d[0],'o': d[1],'c': d[2],'h': d[3], 'l': d[4]} 
                                                                    for d in message['candles']]
        elif len(message[0]) == 4:
            result = {'time': message[0][1],'price': message[0][2]}
            self.api.realtime_price[message[0][0]].append(result)
        elif len(message[0]) == 2:
            result = {'sentiment': {'sell': 100 - int(message[0][1]),'buy': int(message[0][1])}}
            self.api.realtime_sentiment[message[0][0]] = result

    def on_error(self, ws, error):
        logger.error(error)
        global_value.websocket_error_reason = str(error)
        global_value.check_websocket_if_error = True

    def on_open(self, ws):
        logger.info('Websocket client connected.')
        global_value.check_websocket_if_connect = 1
        self.send_initial_messages()

    def send_initial_messages(self):
        self.ws.send("42['tick']")
        self.ws.send("42['indicator/list']")
        self.ws.send("42['drawing/load']")
        self.ws.send("42['pending/list']")
        # self.ws.send("42['instruments/update',{'asset':'EURUSD','period':60}]")
        self.ws.send("42['chart_notification/get']")
        # self.ws.send("42['depth/follow','EURUSD']")
        self.ws.send("42['tick']")

    def on_close(self, ws, close_status_code, close_msg):
        logger.info('Websocket client disconnected.')
        global_value.check_websocket_if_connect = 0

    def on_ping(self, ws, ping_msg):
        pass

    def on_pong(self, ws, pong_msg):
        self.ws.send('2')

    def handle_remaining(self, message):
        if not message.get('list') == []:
            self.api.api_data = message
