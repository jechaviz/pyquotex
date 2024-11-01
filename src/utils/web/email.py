import email
from email.header import decode_header
from email.utils import parseaddr, getaddresses


class Email:
  """Class to represent an email with lazy loading of various parts."""

  def __init__(self, raw_email):
    self.raw_email = raw_email
    self.msg = email.message_from_bytes(raw_email)

  @property
  def subject(self):
    subject, encoding = decode_header(self.msg['Subject'])[0]
    return subject.decode(encoding if encoding else 'utf-8') if isinstance(subject, bytes) else subject

  @property
  def from_(self):
    return parseaddr(self.msg['From'])[1]

  @property
  def to(self):
    return [parseaddr(addr)[1] for addr in getaddresses(self.msg.get_all('To', []))]

  @property
  def cc(self):
    return [parseaddr(addr)[1] for addr in getaddresses(self.msg.get_all('Cc', []))]

  @property
  def body(self):
    parts = []
    for part in self.msg.walk():
      if part.get_content_maintype() == 'multipart':
        continue
      if part.get_content_type() == 'text/plain':
        parts.append(part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8'))
    return "\n".join(parts)

  @property
  def attachments(self):
    attachments = []
    for part in self.msg.walk():
      if part.get('Content-Disposition') and 'attachment' in part.get('Content-Disposition'):
        attachments.append({
          "filename": part.get_filename(),
          "content": part.get_payload(decode=True)
        })
    return attachments