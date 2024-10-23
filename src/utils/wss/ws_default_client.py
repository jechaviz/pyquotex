import os
import platform
import ssl
import time
import asyncio
import logging
import urllib3
import certifi

from threading import Thread

import websocket
from websocket import WebSocketBadStatusException, WebSocketApp, WebSocketConnectionClosedException, WebSocketException

from src.api.session.qx_session_manager import QxSessionManager
from src.api.websocket.qx_ws_msg_handler import QxWsMsgHandler
from src.utils.settings import Settings
from src.utils.code_signature import CodeSignature
from src.utils.time.time_util import TimeUtil
from src.utils.wss.ws_state import WsState
from src.utils.wss.session_manager_i import SessionManagerI

from src.utils.api.api_parser import ApiParser
from src.utils.wss.ws_msg_handler_i import WsMsgHandlerI

urllib3.disable_warnings()
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['WEBSOCKET_CLIENT_CA_BUNDLE'] = certifi.where()

logger = logging.getLogger(__name__)

class DefaultWebsocketClient:
  # Opinionated Default WebSocket Client
  # Requires Implementation for SessionManagerI, and WsMsHandlerI according to the interface definition
  # Requires Settings feed with yml format with values api_name:wss:key-values
  # Requires ApiParser feed with yml with values actions:api_actions, var_defaults:api_var_defaults, constants.
  def __init__(self, settings, ws_api_section_name_in_settings_file: str,
               ws_state: WsState, session_manager: SessionManagerI,
               api_actions_config_file: str, ws_msg_handler: WsMsgHandlerI):
    CodeSignature.info(self)
    self.api_parser = ApiParser(api_actions_config_file)
    self.session_manager = session_manager
    self.api_name = ws_api_section_name_in_settings_file
    self.ws_msg_handler = ws_msg_handler
    self.settings = settings
    self.ws_state = ws_state
    self.ws_watch_state_changes_thread = None
    self.ws_reconnect = None
    self.session_data = {}
    self.ws_thread = None
    self.ws_task = None
    self.retry_count = 0
    self.ws_msg = None
    self.ws = WebSocketApp(
        url=self.config('url'),
        on_message=self.on_message,
        on_open=self.on_open,
        on_close=self.on_close,
        on_ping=self.on_ping,
        on_pong=self.on_pong,
        on_error=self.on_error,
        on_reconnect=self.on_reconnect)
    self.set_connected(False)
    websocket.enableTrace(self.config('enable_trace'))

  async def try_connection_handler(self, attempts=10):
    CodeSignature.info(self)
    if self.is_connected(): return True
    await self.connect()
    if self.is_connected(): return True
    error_msg = str(self.get_state('error_msg'))
    if error_msg != 'None':
      if 'getaddrinfo failed' in error_msg:
        print('Site not reachable, check internet.')
        exit(1)
      elif 'Handshake status 403 Forbidden' not in error_msg:
        print(error_msg)
    if attempts > 1:
      await asyncio.sleep(5)
      await self.try_connection_handler(attempts - 1)
    return False
  async def get_session_data(self, reconnect):
    CodeSignature.info(self)
    if reconnect:
      self.session_data = await self.session_manager.login(force=True)
    if not self.session_data.get('session_id'):
      self.session_data = await self.session_manager.login()
    return self.session_data

  async def connect(self, reconnect=False):
    CodeSignature.info(self)
    if self.is_connected() and not reconnect: return True
    await self.get_session_data(reconnect)
    if not self.session_data.get('session_id'): return False
    try:
      self.ws.header = self.session_data.get('headers')
      self.ws.cookie = self.session_data.get('cookies')
      self.run_forever()
    except WebSocketBadStatusException as e:
      # Handle specific exceptions for potential reconnection
      if self.config('retry.on'):
        await self.reconnect()
    except WebSocketConnectionClosedException as e:
      print('Websocket connection closed: ', e)
    except WebSocketException as e:
      print('Websocket error: ', e)
    except Exception as e:
      await self._on_close_handler(e)

  async def reconnect(self):
    CodeSignature.info(self)
    if self.config('retry.on') and self.retry_count < self.config('retry.max_attempts'):
      await asyncio.sleep(self.config('retry.wait'))
      await self.connect(reconnect=True)
      self.retry_count += 1

  def send(self, action_id, params):
    CodeSignature.info(self)
    if self.ws:
      try:
        requests = self.api_parser.action_requests(action_id, params)
        try:
          for request in requests:
            self.ws.send(request)
            time.sleep(0.1)
            self.set_state('request', request)
        except WebSocketException as e:
          self.on_error(self.ws, e)
      except WebSocketConnectionClosedException as e:
        self.on_error(self.ws, e)

  # Not flexible enough. Would need refactor if used for other wss apis.
  def on_message(self, ws, msg):
    CodeSignature.info(self)
    if not self.ws_msg_handler.is_connected(msg): return
    self.set_connected(True)
    self.retry_count = 0
    current_time = time.localtime()
    if current_time.tm_sec % self.config('msg_interval') == 0:
      self.send('on_interval', {})
    self.ws_msg = self.ws_msg_handler.set_msg(msg)
    self.ws_msg_handler.handle_msg(msg)

  async def disconnect(self):
    if self.ws:
      self.ws.close()
      self.ws = None
      self.ws_msg = None
      self.ws_thread.join()
      self.set_connected(False)
      self.ws_watch_state_changes_thread.join()

  async def _on_close_handler(self, e):
    CodeSignature.info(self)
    # on_close coroutine
    logger.info(f'Websocket connection failed: {e}. Attempting to reconnect...')
    self.ws = None
    if self.config('retry.on'):
      await self.reconnect()
    self.on_close(self.ws, 1006, 'Max reconnect attempts reached.')

  def run_forever(self):
    settings = {
      'ping_interval': self.config('ping.interval'),
      'ping_timeout': self.config('ping.timeout'),
      'ping_payload': self.config('ping.payload'),
      'origin': self.config('origin'),
      'host': self.config('host'),
      'sslopt': {
        'cert_reqs': ssl.CERT_NONE,
        'ca_certs': certifi.where(),
      }
    }
    if platform.system() == 'Linux':
      settings['sslopt']['ssl_version+'] = ssl.PROTOCOL_TLSv1_2
    self.ws_thread = Thread(target=self.ws.run_forever, kwargs=settings)
    self.ws_thread.daemon = True
    self.ws_thread.start()

  def is_ws_alive(self):
    CodeSignature.info(self)
    return self.ws_thread.is_alive()

  def is_connected(self):
    return self.get_state('connected')

  def on_open(self, ws):
    CodeSignature.info(self)
    self.set_connected(True)
    self.send('on_open', self.session_data)
    while not TimeUtil.wait(5, lambda: self.ws_msg, 0.1):
      pass
    if self.ws_msg:
      self.send('on_init', {})
    else:
      self.connect(False)
      self.set_state('error_msg', 'Timeout while waiting for initial response.')
      self.disconnect()

  def on_ping(self, ws, ping_msg):
    CodeSignature.info(self)
    self.send('ping', {})

  def on_pong(self, ws, pong_msg):
    CodeSignature.info(self)
    self.send('pong', {})

  def on_reconnect(self, ws):
    CodeSignature.info(self)
    pass

  def on_error(self, ws, error_msg):
    CodeSignature.info(self)
    self.set_state('error_msg', str(error_msg))

  def on_close(self, ws, close_status_code, close_msg):
    CodeSignature.info(self)
    self.set_connected(False)
    self.ws_msg = None

  def config(self, key):
    return self.settings.get(self.api_name + '.wss.' + key)

  def get_state(self, key):
    return self.ws_state.get_state(key)

  def set_state(self, key, value):
    self.ws_state.set_state(key, value)

  def set_connected(self, is_connected):
    self.set_state('connected', is_connected)

  def show_state(self):
    connection_created = self.get_state('connected')
    if connection_created:
      while connection_created:
        self.ws_state.print_state_change()
        time.sleep(1)

  def watch_state_changes(self):
    self.ws_watch_state_changes_thread = Thread(target=self.show_state())
    self.ws_watch_state_changes_thread.daemon = True
    self.ws_watch_state_changes_thread.start()

async def main():
  state = WsState()
  settings = Settings()
  ws = DefaultWebsocketClient(settings,
      ws_api_section_name_in_settings_file='qx',
      ws_state=state,
      session_manager=QxSessionManager(settings),
      api_actions_config_file=r'C:\git\py_qxtrader\src\api\websocket\qx_ws_api.yml',
      ws_msg_handler=QxWsMsgHandler(state))
  await ws.try_connection_handler()
  # ws.watch_state_changes()
  # await ws.disconnect()

# Integration test
if __name__ == '__main__':
  asyncio.run(main())