import asyncio
from pathlib import Path

from bs4 import BeautifulSoup
from quotexapi.http.mail import MailBrowser
from settings.settings import Settings

class QuotexPinGetter:
    def __init__(self, settings, attempts=5):
        self.mail_browser = MailBrowser(settings)
        self.quotex_email = settings.get('quotex_email')
        self.attempts = attempts

    async def parse_email_for_pin(self, email_bodies):
        for body in email_bodies:
            if any(substring in body for substring in
                   ["PIN", "Your authentication PIN-code:", "Your authentication PIN code:"]):
                dom = BeautifulSoup(body, "html.parser")
                return dom.find("b").get_text()
        return None

    async def get_pin(self):
        await self.mail_browser.connect()
        try:
            for attempt in range(self.attempts):
                raw_email = await self.mail_browser.get_latest_email_from_sender(self.quotex_email)
                if not raw_email: continue
                email_bodies = [body async for body in self.mail_browser.get_email_attachments(raw_email)]
                pin_code = await self.parse_email_for_pin(email_bodies)
                if pin_code: return pin_code
                await asyncio.sleep(1)
            return None
        finally:
            await self.mail_browser.disconnect()

async def main():
    settings = Settings(Path("settings/config.yml"))
    quotex_pin_getter = QuotexPinGetter(settings)
    pin_code = await quotex_pin_getter.get_pin()
    print(f"Found PIN code: {pin_code}")


if __name__ == "__main__":
    asyncio.run(main())