import asyncio
import re
import json
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from src.api.session.qx_mail_pin_getter import QxMailPinGetter
from src.utils.settings import Settings
from src.utils.code_signature import CodeSignature
from src.utils.web.web_browser import WebBrowser
from paprika import singleton
from asyncio.log import logger

@singleton
class QxBrowserLogin:
  def __init__(self, settings):
    CodeSignature.print(self)
    self.settings = settings
    self.browser = WebBrowser(settings)
    self.session_data = {}
    self.saved_session_data = {}
    self.dom: BeautifulSoup | None = None
    self.html = None

  def load_saved_session(self):
    CodeSignature.info(self)
    session_file = self.settings.get('app.paths.session')
    try:
      with open(session_file, 'r') as f:
        self.saved_session_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
      logger.debug(f'Error loading session data: {e}')
    return self.saved_session_data

  def config(self, key):
    value = self.settings.get('qx.' + key)
    return value

  async def go_to_sign_in_page(self):
    await self.browser.page.goto(self.config('urls.login'))
    await self.get_dom()

  def got_logged_in(self):
    return self.browser.page.url == self.config('urls.logged')

  async def sign_in(self):
   await self._fill_sign_in_form()
   await self._submit_sign_in_form()
   await self.browser.page.wait_for_timeout(10000)
   await self.get_dom()

  async def _fill_sign_in_form(self):
    await self._fill_field_by_role('textbox', self.config('locators.user'), self.config('account.user'))
    await self._fill_field_by_role('textbox', self.config('locators.pass'), self.config('account.pass'))

  async def _submit_sign_in_form(self):
    await self.browser.page.get_by_role('button', name=self.config('locators.submit_login')).click()
    async with self.browser.page.expect_navigation():
      await self.browser.page.wait_for_timeout(5000)
      await self.handle_pin_required()

  async def _fill_field_by_role(self, role, name, value):
    await self.browser.page.get_by_role(role, name=name).fill(value)
    await self.browser.page.get_by_role(role, name=name).press('Enter')

  async def _fill_field_by_placeholder(self, placeholder, value):
    await self.browser.page.get_by_placeholder(placeholder).fill(value)
    await self.browser.page.get_by_placeholder(placeholder).press('Enter')

  async def handle_pin_required(self):
    soup = BeautifulSoup(await self.browser.page.content(), 'html.parser')
    pin_sent = self.config('locators.pin_sent')
    if pin_sent in soup.get_text():
      pin_code = QxMailPinGetter(self.settings).get_pin()
      code = pin_code if pin_code else input(pin_sent)
      await self._enter_pin_code(code)

  async def _enter_pin_code(self, code):
    await self._fill_field_by_placeholder(self.config('locators.pin'), code)
    await self.browser.page.get_by_role('button', name=self.config('locators.submit_pin')).click()

  def set_session_id(self):
    try:
      token_match = re.search(r'\"token"\s*:\s*"(.+?)"', self.html)
      self.session_data['session_id'] = token_match.group(1)
    except:
      pass

  async def set_cookies(self):
    cookies = await self.browser.context.cookies()
    cookiejar = requests.utils.cookiejar_from_dict({c['name']: c['value'] for c in cookies})
    cookies_string = '_ga=GA1.1.1907095278.1691245340; referer=https%3A%2F%2Fquotexbrokerlogin.com%2F; lang=en; '
    cookies_string += '; '.join([f'{c.name}={c.value}' for c in cookiejar])
    self.session_data['cookies'] = cookies_string

  async def set_user_agent(self):
    self.session_data['user_agent'] = await self.browser.page.evaluate('() => navigator.userAgent;')

  async def save_session_file(self):
    session_file = self.settings.get('app.paths.session')
    session_file.parent.mkdir(exist_ok=True, parents=True)
    with session_file.open('w') as f:
      json.dump(self.session_data, f, indent=2)

  async def get_dom(self, reload=False):
    self.html = await self.browser.page.content()
    self.dom = BeautifulSoup(self.html, 'html.parser')

  async def set_session_data(self):
    self.set_session_id()
    if self.session_data.get('session_id'):
      await self.set_cookies()
      await self.set_user_agent()
    else:
      raise Exception('Error getting session id')

  async def get_session_data(self, force_login=False):
    CodeSignature.print(self)
    if not self.saved_session_data:
      self.load_saved_session()
    if self.saved_session_data and not force_login:
      return self.saved_session_data
    async with async_playwright() as playwright:
      try:
        await self.browser.setup(playwright)
        await self.go_to_sign_in_page()
        if self.got_logged_in():
          self.set_session_id()
          if self.session_data['session_id'] == self.saved_session_data['session_id']:
            return self.session_data
        else:
          await self.sign_in()
        await self.set_session_data()
        await self.save_session_file()
        await self.browser.close_context()
      except PlaywrightTimeoutError as e:
        print(f'Probably bad internet connection: {e}')
      except Exception as e:
        print(f'Error in QxLogin: {e}')
    return self.session_data

async def main():
  qx_browser_login = QxBrowserLogin(Settings())
  session_data = await qx_browser_login.get_session_data(force_login=True)
  print(session_data)

if __name__ == "__main__":
  asyncio.run(main())