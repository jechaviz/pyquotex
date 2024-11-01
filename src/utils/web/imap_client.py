import email
import imaplib
import time
from datetime import datetime
from snoop import snoop
from src.utils.settings import Settings
from src.utils.web.email import Email


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
        """Execute IMAP command safely and handle errors."""
        try:
            return command(*args)
        except Exception as e:
            print(f"IMAP error: {e}")
            return None, None

    def select_mailbox(self, mailbox='inbox'):
        self._execute_imap_command(self.connection.select, mailbox)

    def get_latest_email_from_sender(self, sender_email, check_interval=5, timeout=60):
        self.connect()
        self.select_mailbox()

        # Prepare filters to get emails from the specified sender, with today's date as 'after' filter
        filters = {
            "from": sender_email,
            "after": datetime.now().strftime('%Y-%m-%d'),
            "met": "all"
        }

        end_time = time.time() + timeout
        while time.time() < end_time:
            # Use get_email with `_slice` to fetch only the latest email
            emails = self.get_emails(filters=filters, slice_=slice(None, 1))  # Retrieve only the latest email
            if emails:
                return emails[0]["uid"], emails[0]  # Return UID and full email data
            time.sleep(check_interval)

        # Return None if no email found within the timeout period
        return None, None

    def _decode_email_text(self, part):
        content = part.get_payload(decode=True)
        return content.decode() if content else ""

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
            "from": lambda v: f'FROM "{v}"',
            "to": lambda v: f'TO "{v}"',
            "after": lambda v: f'SINCE {datetime.strptime(v, "%Y-%m-%d").strftime("%d-%b-%Y")}',
            "before": lambda v: f'BEFORE {datetime.strptime(v, "%Y-%m-%d").strftime("%d-%b-%Y")}',
            "has": lambda v: 'HASATTACHMENT' if v == "attachment" else '',
        }

        criteria = [formatter(filters[key]) for key, formatter in criteria_map.items() if
                    key in filters and filters[key]]

        match = filters.get("met", "all").upper()
        return "OR " + " ".join(criteria) if match == "ANY" else " ".join(criteria)

    def _slice_emails(self, email_ids, slice_):
        try:
            start, stop = slice_.start, slice_.stop
            return email_ids[start:stop]
        except Exception as e:
            print(f"Error applying slice: {e}")
            return email_ids

    def get_emails(self, filters, slice_=slice(None)):
        self.connect()
        self.select_mailbox()

        search_criteria = self._imap_search_criteria(filters) or 'ALL'
        status, email_ids = self.connection.search(None, search_criteria)
        if status != 'OK' or not email_ids[0]:
            print("No emails found.")
            return []

        email_id_list = email_ids[0].split()[::-1]
        sliced_email_ids = self._slice_emails(email_id_list, slice_)

        emails = []
        for email_id in sliced_email_ids:
            status, msg_data = self.connection.fetch(email_id, '(RFC822)')
            if status == 'OK' and msg_data:
                raw_email = msg_data[0][1]
                emails.append(Email(raw_email))

        return emails

def main():
    imap_client = ImapClient(Settings())
    imap_client.connect()
    filters = {
        "met": "all",
        "from": "no_reply@gmail.com",
        "after": "2024-11-01"
    }

    # Get the latest 2 emails matching the criteria
    emails = imap_client.get_emails(filters, slice_=slice(None, 2))
    for email in emails:
        print(f"ID: {email['id']}, Subject: {email['subject']}")

    imap_client.disconnect()

if __name__ == "__main__":
    main()
