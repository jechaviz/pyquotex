import re
from pathlib import Path
from bs4 import BeautifulSoup
from utils.imap_client import ImapClient
from settings.settings import Settings

class QuotexPinGetter:
  def __init__(self, settings):
    self.imap_client = ImapClient(settings)
    self.settings = settings

  def get_pin(self):
    try:
      self.imap_client.connect()
      self.imap_client.select_mailbox()
      sender_email = self.settings.get('qx_no_reply_email')
      email_uid, raw_email = self.imap_client.get_latest_email_from_sender(sender_email)
      if not raw_email: return None
      for html_part in self.imap_client.get_email_text_parts(raw_email):
        pin = self.extract_pin(html_part)
        if pin:
          # self.imap_client.delete_email(email_uid) # TODO: doesn't delete email, no errors thrown.
          return pin
      return None
    except Exception as e:
      print(f"Error occurred: {e}")
      return None
    finally:
      self.imap_client.disconnect()

  def is_pin_email(self, html):
    return any(str in html for str in ['PIN', 'Pin', 'pin'])

  def extract_pin2(self, html):
    if self.is_pin_email(html):
      pin_match = re.search(r'<b>(\d{4,6})</b>', html)
      return pin_match.group(1)
    return None

  def extract_pin(self, html):
    if self.is_pin_email(html):
      dom = BeautifulSoup(html, "html.parser")
      return dom.find("b").get_text()
    return None

def main():
    settings = Settings(Path("../../settings/config.yml"))
    qx_pin_getter = QuotexPinGetter(settings)
    pin_code = qx_pin_getter.get_pin()
    print(f'Found PIN code: {pin_code}' if pin_code else 'No PIN found.')

if __name__ == "__main__":
    main()