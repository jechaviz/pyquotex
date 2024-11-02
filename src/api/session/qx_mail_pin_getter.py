import re
from datetime import datetime

from bs4 import BeautifulSoup
from snoop import snoop

from src.utils.tree_log import tree
from src.utils.web.imap_client import ImapClient
from src.utils.settings import Settings
from paprika import singleton

@singleton
class QxMailPinGetter:
  def __init__(self, settings):
    self.imap_client = ImapClient(settings)
    self.settings = settings

  def get_pin(self):
    tree.info(self)
    try:
      self.imap_client.connect()
      self.imap_client.select_mailbox()
      sender_email = self.settings.get('qx.emails.no_reply')
      filters = {
        'contains': 'PIN',
        'after': datetime.now().strftime('%Y-%m-%d'),
      }
      email = self.imap_client.get_latest_email_from(filters, sender_email)
      if email:
        pin = self.extract_pin(email.body)
        if pin:
          self.imap_client.delete_email(email.uid)
          return pin
      return None

    except Exception as e:
      if 'authentication failed' in str(e):
        print('IMAP authentication failed. Check email and password, or IMAP Access status enabled.')
      else:
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
    tree.info(self)
    if self._is_pin_email(html):
      dom = BeautifulSoup(html, 'html.parser')
      pin = dom.find('b').get_text()
      tree.info('PIN: ', pin)
      return pin
    return None

def main():
    qx_pin_getter = QxMailPinGetter(Settings())
    pin_code = qx_pin_getter.get_pin()
    print(f'Found PIN code: {pin_code}' if pin_code else 'No PIN found.')

if __name__ == '__main__':
    main()