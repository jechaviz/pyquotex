import re
from bs4 import BeautifulSoup
from src.utils.web.imap_client import ImapClient
from src.utils.settings import Settings
from paprika import singleton

@singleton
class QxMailPinGetter:
  def __init__(self, settings):
    self.imap_client = ImapClient(settings)
    self.settings = settings

  def get_pin(self):
    try:
      self.imap_client.connect()
      self.imap_client.select_mailbox()
      sender_email = self.settings.get('qx.emails.no_reply')
      email_uid, raw_email = self.imap_client.get_latest_email_from_sender(sender_email)
      if not raw_email: return None
      for html_part in self.imap_client.get_email_text_parts(raw_email):
        pin = self.extract_pin(html_part)
        if pin:
          self.imap_client.delete_email(email_uid)
          return pin
      return None
    except Exception as e:
      print(f'Error occurred: {e}')
      return None
    finally:
      self.imap_client.disconnect()

  @staticmethod
  def _is_pin_email(html):
    return any(text in html for text in ['PIN', 'Pin', 'pin'])

  def extract_pin2(self, html):
    if self._is_pin_email(html):
      pin_match = re.search(r'<b>(\d{4,6})</b>', html)
      return pin_match.group(1)
    return None

  def extract_pin(self, html):
    if self._is_pin_email(html):
      dom = BeautifulSoup(html, 'html.parser')
      return dom.find('b').get_text()
    return None

def main():
    qx_pin_getter = QxMailPinGetter(Settings())
    pin_code = qx_pin_getter.get_pin()
    print(f'Found PIN code: {pin_code}' if pin_code else 'No PIN found.')

if __name__ == '__main__':
    main()