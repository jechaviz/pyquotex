import imaplib
import email

class ImapClient:
  def __init__(self, settings):
    self.server = settings.get('imap_server')
    self.email = settings.get('imap_email')
    self.password = settings.get('imap_pass')
    self.port = settings.get('imap_port')
    self.connection = None

  def connect(self):
    if self.connection: return
    self.connection = imaplib.IMAP4_SSL(self.server, self.port)
    self.connection.login(self.email, self.password)

  def disconnect(self):
    if self.connection:
      self.connection.logout()

  def select_mailbox(self, mailbox="inbox"):
    self.connection.select(mailbox)

  def get_latest_email_from_sender(self, sender_email):
    try:
      self.select_mailbox()
      status, email_ids = self.connection.search(None, f'(FROM "{sender_email}")')
      if not email_ids[0]: return None, None
      email_id_list = email_ids[0].split()
      status, email_data = self.connection.fetch(email_id_list[-1], "(RFC822)")
      if status == 'OK':
        email_uid = email_id_list[-1].decode()  # Convert bytes to string
        return email_uid, email_data[0][1]
      else:
        return None, None
    except Exception as e:
        print(f"Error retrieving email from {sender_email}: {e}")
        return None, None

  def get_email_text_parts(self, raw_email):
    msg = email.message_from_bytes(raw_email)
    attachments = []
    for part in msg.walk():
      if part.get_content_maintype() == 'multipart':
        continue
      content_disposition = str(part.get("Content-Disposition"))
      if "attachment" in content_disposition:
        attachments.append(part)
      else:
        yield part.get_payload(decode=True).decode()
    for attachment in attachments:
      yield attachment.get_payload(decode=True).decode()

  def delete_email(self, email_uid):
    try:
      self.connect()
      self.connection.uid('STORE', email_uid, '+FLAGS', '(\\Deleted)')
      self.connection.expunge()
    except Exception as e:
      print(f"Error deleting email with UID {email_uid}: {e}")