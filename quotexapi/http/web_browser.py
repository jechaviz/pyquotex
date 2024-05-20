from ..utils.playwright_install import install
from playwright.async_api import Playwright, async_playwright, expect
from playwright_stealth import stealth_async
class WebBrowser:
    def __init__(self, settings):
        self.user_data_dir = settings.get('user_data_dir')
        self.args = [
            '--disable-web-security',
            '--no-sandbox',
            '--disable-web-security',
            '--aggressive-cache-discard',
            '--disable-cache',
            '--disable-application-cache',
            '--disable-offline-load-stale-cache',
            '--disk-cache-size=0',
            '--disable-background-networking',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--metrics-recording-only',
            '--mute-audio',
            '--no-first-run',
            '--safebrowsing-disable-auto-update',
            '--ignore-certificate-errors',
            '--ignore-ssl-errors',
            '--ignore-certificate-errors-spki-list',
            '--disable-features=LeakyPeeker',
            '--disable-setuid-sandbox',
            '--disable-gpu'
        ]
        self.browser = None
        self.context = None
        self.page = None

    async def setup(self, playwright: Playwright):
      # install(playwright.firefox, with_deps=True)
        if self.user_data_dir:
            self.browser = playwright.firefox
            self.context = await self.browser.launch_persistent_context(
                self.user_data_dir,
                headless=True,
                extra_http_headers={'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'}
            )
            self.page = self.context.pages[0]
        else:
            self.browser = await playwright.firefox.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await stealth_async(self.page)

    async def close_context(self):
        await self.context.close() if self.user_data_dir else await self.browser.close()


