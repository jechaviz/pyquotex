import email
import imaplib
import time
from datetime import datetime

from src.utils.settings import Settings
from src.utils.web.email_obj import EmailObj


class ImapClient:
  def __init__(self, settings):
    self.server = settings.get('imap.server')
    self.email = settings.get('imap.email')
    self.password = settings.get('imap.pass')
    self.port = settings.get('imap.port')
    self.connection = None

  def connect(self):
    if not self.connection:
      self.connection = imaplib.IMAP4_SSL(self.server, self.port)
      self.connection.login(self.email, self.password)

  def disconnect(self):
    if self.connection:
      self.connection.logout()
      self.connection = None

  def _execute_imap_command(self, command, *args):
    '''Execute IMAP command safely and handle errors.'''
    try:
      return command(*args)
    except Exception as e:
      print(f'IMAP error: {e}')
      return None, None

  def select_mailbox(self, mailbox='inbox'):
    self._execute_imap_command(self.connection.select, mailbox)

  def _decode_email_text(self, part):
    content = part.get_payload(decode=True)
    return content.decode() if content else ''

  def get_email_text_parts(self, raw_email):
    msg = email.message_from_bytes(raw_email)
    for part in msg.walk():
      if part.get_content_maintype() != 'multipart' and 'attachment' not in str(part.get('Content-Disposition')):
        yield self._decode_email_text(part)

  def delete_email(self, email_uid):
    self.connect()
    status, _ = self._execute_imap_command(self.connection.uid, 'STORE', email_uid, '+FLAGS', '\\Deleted')
    if status == 'OK':
      self.connection.expunge()

  def _imap_search_criteria(self, filters):
    criteria_map = {
      'from': lambda v: f"FROM '{v}'",
      'to': lambda v: f"TO '{v}'",
      'after': lambda v: f'SINCE {datetime.strptime(v, '%Y-%m-%d').strftime('%d-%b-%Y')}',
      'before': lambda v: f'BEFORE {datetime.strptime(v, '%Y-%m-%d').strftime('%d-%b-%Y')}',
      'has': lambda v: 'HASATTACHMENT' if v == 'attachment' else '',
      'subject': lambda v: f'SUBJECT "{v}"',
      'contains': lambda v: f'BODY "{v}"',
    }

    criteria = [formatter(filters[key]) for key, formatter in criteria_map.items() if
                key in filters and filters[key]]

    match = filters.get('met', 'all').upper()
    return 'OR ' + ' '.join(criteria) if match == 'ANY' else ' '.join(criteria)

  def _slice_emails(self, email_ids, slice_):
    try:
      start, stop = slice_.start, slice_.stop
      return email_ids[start:stop]
    except Exception as e:
      print(f'Error applying slice: {e}')
      return email_ids

  def get_emails(self, filters, slice_=slice(None)):
    self.connect()
    self.select_mailbox()

    search_criteria = self._imap_search_criteria(filters) or 'ALL'
    status, email_ids = self.connection.search(None, search_criteria)
    if status != 'OK' or not email_ids[0]:
      print('No emails found.')
      return []

    email_id_list = email_ids[0].split()[::-1]
    sliced_email_ids = self._slice_emails(email_id_list, slice_)

    emails = []
    for email_id in sliced_email_ids:
      status, msg_data = self.connection.fetch(email_id, '(RFC822)')
      if status == 'OK' and msg_data:
        raw_email = msg_data[0][1]
        emails.append(EmailObj(email_id.decode(), raw_email))

    return emails

  def get_latest_email_from(self, filters, sender_email, check_interval=5, timeout=60):
    end_time = time.time() + timeout
    while time.time() < end_time:
      emails = self.get_emails(filters, slice_=slice(None, 10))
      for email_ in emails:
        if email_.from_ == sender_email:
          return email_
      time.sleep(check_interval)
    return None

def main():
  imap_client = ImapClient(Settings())
  imap_client.connect()
  filters = {
    'contains': 'PIN'
  }

  # Get the latest 10 emails matching the criteria
  emails = imap_client.get_emails(filters, slice_=slice(None, 10))
  for email in emails:
    if email.from_ == 'noreply@qxbroker.com':
      print(
        f'ID: {email.uid}, Subject: {email.subject}, body: {email.body[:10] + '...'}, from: {email.from_}, to: {email.to}')

  imap_client.disconnect()


if __name__ == '__main__':
  main()
