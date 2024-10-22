from playwright.async_api import Playwright
from playwright_stealth import stealth_async


class WebBrowser:
  def __init__(self, settings):
    self.user_data_dir = settings.get('app.paths.cache')
    self.args = [
      '--aggressive-cache-discard',
      '--disable-application-cache',
      '--disable-background-networking',
      '--disable-cache',
      '--disable-default-apps',
      '--disable-extensions',
      '--disable-features=LeakyPeeker',
      '--disable-gpu'
      '--disable-offline-load-stale-cache',
      '--disable-setuid-sandbox',
      '--disable-sync',
      '--disable-translate',
      '--disable-web-security',
      '--disk-cache-size=0',
      '--hide-scrollbars',
      '--ignore-certificate-errors',
      '--ignore-certificate-errors-spki-list',
      '--ignore-ssl-errors',
      '--metrics-recording-only',
      '--mute-audio',
      '--no-first-run',
      '--no-sandbox',
      '--safebrowsing-disable-auto-update',
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
        extra_http_headers={
          'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'}
      )
      self.page = self.context.pages[0]
    else:
      self.browser = await playwright.firefox.launch(headless=True)
      self.context = await self.browser.new_context()
      self.page = await self.context.new_page()
      await stealth_async(self.page)

  async def close_context(self):
    await self.context.close() if self.user_data_dir else await self.browser.close()
