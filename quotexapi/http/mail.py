import imaplib
import email

class MailBrowser:
    def __init__(self, settings):
        self.email_address = settings.get('email')
        self.email_pass = settings.get('email_pass')
        self.email_server = settings.get('imap_server')
        self.imap_connection = None

    async def connect(self):
        self.imap_connection = imaplib.IMAP4_SSL(self.email_server)
        await self.imap_connection.login(self.email_address, self.email_pass)
        await self.imap_connection.select("inbox")

    async def disconnect(self):
        if self.imap_connection:
            await self.imap_connection.logout()

    async def get_latest_email_from_sender(self, sender):
        status, email_ids = await self.imap_connection.search(None, f'(FROM "{sender}")')
        if not email_ids:
            return None

        email_id_list = email_ids[0].split()
        status, email_data = await self.imap_connection.fetch(email_id_list[-1], "(RFC822)")
        return email_data[0][1]

    async def get_email_attachments(self, raw_email):
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
            yield attachment