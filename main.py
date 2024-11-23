import asyncio
from src.api.websocket.qx_ws_client import QxWsClient
from src.utils.settings import Settings

async def main():
  ws = QxWsClient(Settings())
  await ws.try_connection_handler()
  # ws.watch_state_changes()
  # await ws.disconnect()

if __name__ == '__main__':
  asyncio.run(main())
