import asyncio
import json
from asyncio.log import logger

from src.api.session.qx_browser_login import QxBrowserLogin
from src.utils.settings import Settings
from src.utils.this_name import ThisName
from src.utils.web.http_client import HttpClient
from src.utils.wss.session_manager_i import SessionManagerI


class QxSessionManager(SessionManagerI):
  def __init__(self, settings):
    super().__init__(settings)

  async def login(self, force=False) -> dict:
    ThisName.print(self)
    self.session_data = await QxBrowserLogin(self.settings).get_session_data(force)
    return self.session_data

  # TODO: logout works?
  def logout(self):
    logout_response = HttpClient().post(
      url= self.settings.get('qx.urls.logout'),
      headers={'Referer':    self.settings.get('qx.urls.trade'),
               'cookie':     self.session_data['cookies'],
               'User-Agent': self.session_data['user_agent']}
    )
    print(logout_response)
    if logout_response: self.session_data.clear()
    return bool(logout_response)


async def main():
  qx_sm = QxSessionManager(Settings())
  session_data = await qx_sm.login()
  print(f'Logged: {session_data}' if session_data.get('session_id') else 'Not logged in')
  # is_logged_out = qx_sm.logout()
  # print(f'Logged out: {qx_sm.session_data}' if is_logged_out else 'Not logged out')

if __name__ == '__main__':
  asyncio.run(main())
