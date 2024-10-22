import asyncio

from src.api.session.qx_session_manager import QxSessionManager
from src.api.websocket.qx_ws_msg_handler import QxWsMsgHandler
from src.utils.settings import Settings
from src.utils.wss.ws_default_client import DefaultWebsocketClient
from src.utils.wss.ws_state import WsState

class QxWsClient(DefaultWebsocketClient):
  def __init__(self, settings):
    state = WsState()
    super().__init__(
      settings,
      ws_api_section_name_in_settings_file='qx',
      ws_state=state,
      session_manager=QxSessionManager(settings),
      api_actions_config_file='qx_ws_api.yml',
      ws_msg_handler=QxWsMsgHandler(state))

async def main():
  ws = QxWsClient(Settings())
  await ws.try_connection_handler()
  # ws.watch_state_changes()
  # await ws.disconnect()

if __name__ == '__main__':
  asyncio.run(main())
