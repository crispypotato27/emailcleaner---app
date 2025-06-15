# Import necessary libraries for email handling, threading, and security
import imaplib                    # For interacting with the IMAP server
import email                      # For parsing email content
from email.header import decode_header  # For decoding MIME-encoded headers
import getpass                    # (Not used here) typically used to securely get user input
from collections import defaultdict  # (Not used here) could be for organizing grouped data
import ssl                        # For creating secure SSL connections
import concurrent.futures         # For multi-threading/concurrency
import threading                  # For thread locks
import time                       # For measuring performance/delays
from datetime import datetime, timedelta  # For date operations (not used in this snippet)

# Class for scanning emails quickly and safely using IMAP and threading
class FastEmailScanner:
    def __init__(self, email_address, password, imap_server):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.mail = None  # Will store the IMAP connection
        self.lock = threading.Lock()  # Thread lock for safe shared data access

    def connect(self):
        """Connect to the email server using IMAP over SSL."""
        try:
            context = ssl.create_default_context()  # Secure SSL context
            self.mail = imaplib.IMAP4_SSL(self.imap_server, 993, ssl_context=context)
            self.mail.login(self.email_address, self.password)
            print(f"✅ Successfully connected to {self.email_address}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False

    def create_connection(self):
        """Create and return a new IMAP connection (used by each thread)."""
        try:
            context = ssl.create_default_context()
            mail = imaplib.IMAP4_SSL(self.imap_server, 993, ssl_context=context)
            mail.login(self.email_address, self.password)
            return mail
        except:
            return None

    def decode_mime_words(self, s):
        """Decode encoded email headers like subject or sender."""
        try:
            decoded_parts = decode_header(s)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):  # Decode bytes using the specified encoding
                    decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_string += part
            return decoded_string
        except:
            return str(s) if s else "Unknown"

    def get_email_info_batch(self, mail_conn, msg_ids):
        """Fetch and decode headers for a batch of email message IDs."""
        emails = []
        try:
            msg_set = ','.join(str(mid.decode() if isinstance(mid, bytes) else mid) for mid in msg_ids)
            _, msg_data = mail_conn.fetch(msg_set, '(UID BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)])')
            
            i = 0
            while i < len(msg_data):
                if isinstance(msg_data[i], tuple) and len(msg_data[i]) > 1:
                    try:
                        # Extract UID
                        uid_info = msg_data[i][0].decode() if isinstance(msg_data[i][0], bytes) else str(msg_data[i][0])
                        uid = uid_info.split('UID ')[1].split(' ')[0] if 'UID ' in uid_info else None
                        
                        email_message = email.message_from_bytes(msg_data[i][1])
                        subject = self.decode_mime_words(email_message.get("Subject", "No Subject"))
                        sender = self.decode_mime_words(email_message.get("From", "Unknown Sender"))
                        date = email_message.get("Date", "Unknown Date")
                        
                        # Clean sender email
                        if '<' in sender and '>' in sender:
                            sender = sender.split('<')[1].split('>')[0]

                        # Add to result list
                        emails.append({
                            'subject': subject[:100],
                            'sender': sender[:60],
                            'date': date,
                            'message_id': email_message.get("Message-ID", "")[:50],
                            'uid': uid
                        })
                    except Exception:
                        continue  # Skip problematic emails
                i += 1
        except Exception as e:
            print(f"⚠️  Batch processing error: {str(e)}")

        return emails

    def process_chunk(self, args):
        """Process a batch (chunk) of email IDs from a specific folder."""
        chunk, folder = args
        mail_conn = self.create_connection()
        if not mail_conn:
            return []
        try:
            mail_conn.select(folder)
            return self.get_email_info_batch(mail_conn, chunk)
        except Exception:
            return []
        finally:
            try:
                mail_conn.close()
                mail_conn.logout()
            except:
                pass

    def scan_folder_fast(self, folder_name, limit=None):
        """Scan all emails in a folder using parallel threads for speed."""
        try:
            status, _ = self.mail.select(folder_name)
            if status != 'OK':
                print(f"❌ Could not access folder: {folder_name}")
                return []

            _, msg_ids = self.mail.search(None, 'ALL')
            msg_id_list = msg_ids[0].split()

            if not msg_id_list:
                return []

            if limit:
                msg_id_list = msg_id_list[-limit:]

            total_emails = len(msg_id_list)
            print(f"📁 Fast scanning {folder_name}... ({total_emails} emails)")

            # Split emails into chunks
            chunk_size = 50
            chunks = [msg_id_list[i:i + chunk_size] for i in range(0, len(msg_id_list), chunk_size)]

            all_emails = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                chunk_args = [(chunk, folder_name) for chunk in chunks]
                future_to_chunk = {executor.submit(self.process_chunk, args): args for args in chunk_args}

                processed_chunks = 0
                for future in concurrent.futures.as_completed(future_to_chunk):
                    chunk_emails = future.result()
                    all_emails.extend(chunk_emails)
                    processed_chunks += 1
                    if processed_chunks % 2 == 0:
                        progress = (processed_chunks / len(chunks)) * 100
                        print(f"   📊 Progress: {progress:.0f}% ({len(all_emails)} emails processed)")

            return all_emails
        except Exception as e:
            print(f"❌ Error scanning {folder_name}: {str(e)}")
            return []

    def scan_unread_fast(self, limit=200):
        """Scan unread emails using smaller chunks for better speed."""
        try:
            self.mail.select('INBOX')
            _, msg_ids = self.mail.search(None, 'UNSEEN')
            if not msg_ids[0]:
                return [], 0

            msg_id_list = msg_ids[0].split()
            total_unread = len(msg_id_list)

            print(f"📧 Found {total_unread} unread emails")

            if total_unread > 1000:
                print(f"⚠️  Large mailbox detected! Processing most recent {limit} for speed.")
                msg_id_list = msg_id_list[-limit:]
            elif total_unread > 500:
                response = input(f"Process all {total_unread} unread emails? (y/N - default processes {limit}): ")
                if response.lower() != 'y':
                    msg_id_list = msg_id_list[-limit:]

            chunk_size = 25
            chunks = [msg_id_list[i:i + chunk_size] for i in range(0, len(msg_id_list), chunk_size)]

            all_emails = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                chunk_args = [(chunk, 'INBOX') for chunk in chunks]
                future_to_chunk = {executor.submit(self.process_chunk, args): args for args in chunk_args}

                for future in concurrent.futures.as_completed(future_to_chunk):
                    chunk_emails = future.result()
                    all_emails.extend(chunk_emails)
                    if len(all_emails) % 50 == 0:
                        print(f"   📧 Processed {len(all_emails)} unread emails...")

            return all_emails, total_unread
        except Exception as e:
            print(f"❌ Error scanning unread emails: {str(e)}")
            return [], 0

    def get_folder_list(self):
        """Return list of folders/mailboxes available on the server."""
        try:
            _, folders = self.mail.list()
            folder_names = []
            for folder in folders:
                folder_info = folder.decode().split('"')
                if len(folder_info) >= 3:
                    folder_names.append(folder_info[-2])
            return folder_names
        except Exception as e:
            print(f"❌ Error getting folder list: {str(e)}")
            return []

    def scan_all_fast(self):
        """Comprehensive scan: unread + spam + junk folders."""
        start_time = time.time()
        results = {
            'unread': [],
            'spam': [],
            'junk': [],
            'folders': [],
            'total_unread_count': 0,
            'scan_time': 0
        }

        folders = self.get_folder_list()
        results['folders'] = folders
        print(f"📂 Available folders: {', '.join(folders[:5])}{'...' if len(folders) > 5 else ''}")

        print(f"\n🚀 Fast scanning unread emails...")
        results['unread'], results['total_unread_count'] = self.scan_unread_fast()

        spam_folders = ['Spam', 'Junk', 'SPAM', 'JUNK', '[Gmail]/Spam', 'Bulk Mail', 'Junk Email']

        for spam_folder in spam_folders:
            if spam_folder in folders:
                print(f"\n🗑️ Fast scanning {spam_folder}...")
                spam_emails = self.scan_folder_fast(spam_folder, limit=100)
                if 'spam' in spam_folder.lower():
                    results['spam'].extend(spam_emails)
                else:
                    results['junk'].extend(spam_emails)

        results['scan_time'] = time.time() - start_time
        return results

    def delete_emails_by_uid(self, folder_name, uids_to_delete):
        """Delete emails by their unique identifier (UID) in a given folder."""
        if not uids_to_delete:
            return 0

        try:
            mail_conn = self.create_connection()
            if not mail_conn:
                print("❌ Could not create connection for deletion")
                return 0

            mail_conn.select(folder_name)
            deleted_count = 0
            batch_size = 50

            for i in range(0, len(uids_to_delete), batch_size):
                batch = uids_to_delete[i:i + batch_size]
                uid_list = ','.join(batch)

                try:
                    mail_conn.uid('STORE', uid_list, '+FLAGS', '\\Deleted')
                    deleted_count += len(batch)

                    if deleted_count % 100 == 0:
                        print(f"   🗑️ Deleted {deleted_count}/{len(uids_to_delete)} emails...")
                except Exception as e:
                    print(f"⚠️  Error deleting batch: {str(e)}")
                    continue

            mail_conn.expunge()
            mail_conn.close()
            mail_conn.logout()
            return deleted_count
        except Exception as e:
            print(f"❌ Error during deletion: {str(e)}")
            return 0
