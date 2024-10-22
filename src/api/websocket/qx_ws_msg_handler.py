import json

from src.utils.wss.ws_msg_handler_i import WsMsgHandlerI
from src.utils.wss.ws_state import WsState


class QxWsMsgHandler(WsMsgHandlerI):
  # Quotex Websocket Message Handler
  def __init__(self, ws_state: WsState):
    super().__init__(ws_state)

  def set_msg(self, msg):
    self.msg = json.loads(msg[1:].decode())
    self.set_state('msg', self.msg)
    return self.msg

  def set_state(self, key, value):
    self.ws_state.set_state(key, value)

  # used by ws_client
  def is_connected(self, msg):
    if 's_authorization' in str(msg):
      self.set_state('connected', True)
      return True
    if 'authorization/reject' in str(msg):
      self.set_state('error_msg', 'auth_rejected')
    if str(msg) == '41':
      self.set_state('error_msg', 'server_request_reconnection')
    if msg.get('error') and msg.get('error') != 'not_money':
      self.set_state('error_msg', msg.get('error'))
    self.set_state('connected', False)
    return False

  def handle_msg(self, msg):
    try:
      self.set_instruments(msg)
      self.process_msg(msg)
      self.handle_temporary_status(msg)
    except:
      pass

  def set_instruments(self, msg):
    if 'call' in str(msg) or 'put' in str(msg):
      self.api['instruments'] = msg

  def process_msg(self, msg):
    self.handle_instruments(msg)
    self.handle_signals(msg)
    self.handle_balance(msg)
    self.handle_buy(msg)
    self.handle_sold_options(msg)
    self.handle_deals(msg)
    self.handle_candles(msg)
    self.handle_training_balance_edit(msg)
    self.handle_no_money_error(msg)
    self.handle_remaining(msg)

  def handle_instruments(self, msg):
    if 'instruments/list' in str(msg):
      self.set_state('listening_instruments', True)

  def handle_signals(self, msg):
    if msg.get('signals'):
      time_in = msg.get('time')
      for i in msg['signals']:
        self.api['signal'][i[0]] = {}
        try:
          self.api['signal'][i[0]][i[2]] = {}
          self.api['signal'][i[0]][i[2]]['dir'] = i[1][0]['signal']
          self.api['signal'][i[0]][i[2]]['duration'] = i[1][0]['timeFrame']
        except:
          self.api['signal'][i[0]][time_in] = {}
          self.api['signal'][i[0]][time_in]['dir'] = i[1][0][1]
          self.api['signal_data'][i[0]][time_in]['duration'] = i[1][0][0]

  def handle_balance(self, msg):
    if msg.get('liveBalance') or msg.get('demoBalance'):
      self.api['account_balance'] = msg

  def handle_candles(self, msg):
    if msg.get('index'):
      self.api['candles']['list'] = msg

  def handle_buy(self, msg):
    if msg.get('id'):
      self.api['buy'] = msg
      self.api['buy']['id'] = msg['id']
      self.api['buy']['server_timestamp'] = msg['closeTimestamp']

  def handle_sold_options(self, msg):
    if msg.get('ticket'):
      self.api['sold_options_respond'] = msg

  def handle_deals(self, msg):
    if msg.get('deals'):
      for deal in msg['deals']:
        self.api['deal'][f"{deal['id']}"]['profit'] = deal['profit']

  def handle_training_balance_edit(self, msg):
    if msg.get('isDemo') and msg.get('balance'):
      self.api['demo_balance_status'] = msg

  def handle_no_money_error(self, msg):
    if msg.get('error') == 'not_money':
        self.api['account_balance'] = {'liveBalance': 0}

  def handle_temporary_status(self, msg):
    if '51-' in str(msg):
      self.api['_temp_status'] = str(msg)
    elif self.api['_temp_status'] == """451-['settings/list',{'_placeholder':true,'num':0}]""":
      self.api['settings_list'] = msg
      self.api['_temp_status'] = ''
    elif self.api['_temp_status'] == """451-['history/list/v2',{'_placeholder':true,'num':0}]""":
      self.api['candles']['list'] = msg['candles']
      self.api['candle_v2_data'][msg['asset']] = msg
      self.api['candle_v2_data'][msg['asset']]['candles'] = \
        [{'t': d[0], 'o': d[1], 'c': d[2], 'h': d[3], 'l': d[4]} for d in msg['candles']]
    elif len(msg[0]) == 4:
      time_price = {'time': msg[0][1], 'price': msg[0][2]}
      self.api['realtime_price'][msg[0][0]].append(time_price)
    elif len(msg[0]) == 2:
      sentiment = {'sentiment': {'sell': 100 - int(msg[0][1]), 'buy': int(msg[0][1])}}
      self.api['realtime_sentiment'][msg[0][0]] = sentiment

  def handle_remaining(self, msg):
    if not msg.get('list'):
      pass
