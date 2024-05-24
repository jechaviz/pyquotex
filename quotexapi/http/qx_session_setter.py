import os
import re
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from .qx_pin_getter import QuotexPinGetter
from .web_browser import WebBrowser


class QxSessionSetter:
    def __init__(self, api):
        self.settings = None
        self.browser = None
        self.qx_pass = None
        self.base_url = None
        self.qx_email = None
        self.https_base_url = None
        self.api = api

    def load_settings(self, settings):
        self.settings = settings
        self.base_url = settings.get('base_url')
        self.https_base_url = f'https://{self.base_url}'
        self.qx_email = settings.get('qx_email')
        self.qx_pass = settings.get('qx_pass')
        self.browser = WebBrowser(settings)

    async def go_to_sign_in_page(self):
        await self.browser.page.goto(f'{self.https_base_url}/en/sign-in')

    async def sign_in(self):
        if self.browser.page.url != f'{self.https_base_url}/en/trade':
            await self._fill_sign_in_form()
            await self._submit_sign_in_form()

    async def _fill_sign_in_form(self):
        await self._fill_field_by_role('textbox', 'Email', self.qx_email)
        await self._fill_field_by_role('textbox', 'Password', self.qx_pass)

    async def _submit_sign_in_form(self):
        await self.browser.page.get_by_role('button', name='Sign In').click()
        async with self.browser.page.expect_navigation():
            await self.browser.page.wait_for_timeout(5000)
            await self._handle_pin_required()

    async def _fill_field_by_role(self, role, name, value):
        await self.browser.page.get_by_role(role, name=name).fill(value)
        await self.browser.page.get_by_role(role, name=name).press('Enter')

    async def _fill_field_by_placeholder(self, placeholder, value):
        await self.browser.page.get_by_placeholder(placeholder).fill(value)
        await self.browser.page.get_by_placeholder(placeholder).press('Enter')

    async def _handle_pin_required(self):
        soup = BeautifulSoup(await self.browser.page.content(), 'html.parser')
        pin_required_text = "Please enter the PIN-code we've just sent to your email"
        if pin_required_text in soup.get_text():
            pin_code = QuotexPinGetter(self.settings).get_pin()
            code = pin_code if pin_code else input(pin_required_text)
            await self._enter_pin_code(code)

    async def _enter_pin_code(self, code):
        await self._fill_field_by_placeholder('Enter 6-digit code...', code)
        await self.browser.page.get_by_role('button', name='Sign in').click()

    async def get_user_agent(self):
        user_agent = await self.browser.page.evaluate('() => navigator.userAgent;')
        self.api.session_data['user_agent'] = user_agent

    async def get_cookies(self):
        cookies = await self.browser.context.cookies()
        cookiejar = requests.utils.cookiejar_from_dict({c['name']: c['value'] for c in cookies})
        cookies_string = '_ga=GA1.1.1907095278.1691245340; referer=https%3A%2F%2Fquotexbrokerlogin.com%2F; lang=en; '
        cookies_string += '; '.join([f'{c.name}={c.value}' for c in cookiejar])
        self.api.session_data['cookies'] = cookies_string

    async def get_token(self, script):
        settings = script.get_text().strip().replace(';', '')
        match = re.sub('window.settings = ', '', settings)
        token = json.loads(match).get('token')
        self.api.session_data['token'] = token

    async def set_session_file(self):
        session_file = Path(os.path.join(self.settings.get('resource_path'), 'session.json'))
        session_file.parent.mkdir(exist_ok=True, parents=True)
        session_file.write_text(json.dumps(self.api.session_data, indent=2))

    async def get_session_data(self):
        await self.browser.page.wait_for_timeout(10000)
        html = await self.browser.page.content()
        dom = BeautifulSoup(html, 'html.parser')
        script = dom.find_all('script', {'type': 'text/javascript'})
        if script:
            await self.get_token(script[1])
            await self.get_user_agent()
            await self.get_cookies()
            await self.set_session_file()

    async def set_session(self):
        async with async_playwright() as playwright:
            await self.browser.setup(playwright)
            await self.go_to_sign_in_page()
            await self.sign_in()
            await self.get_session_data()
            await self.browser.close_context()