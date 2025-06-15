import imaplib
import email
from email.header import decode_header
import concurrent.futures
import time
import ssl
from datetime import datetime, timedelta
import re
import pytz

def create_connection(email_address, password, imap_server):
    try:
        context = ssl.create_default_context()
        mail = imaplib.IMAP4_SSL(imap_server, 993, ssl_context=context)
        mail.login(email_address, password)
        return mail
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def decode_mime_words(s):
    try:
        decoded_parts = decode_header(s)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part
        return decoded_string
    except:
        return str(s) if s else "Unknown"

def parse_email_date(date_str):
    if not date_str or date_str == "Unknown Date":
        return None
    try:
        date_str = re.sub(r'\([A-Za-z]+\)', '', date_str)
        date_str = re.sub(r'\s+', ' ', date_str).strip()
        for fmt in (
            '%a, %d %b %Y %H:%M:%S %z',
            '%d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S',
            '%d %b %Y %H:%M:%S'
        ):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None

def get_email_info_batch(mail_conn, msg_ids, cutoff_date=None):
    emails = []
    try:
        msg_set = ','.join(mid.decode() if isinstance(mid, bytes) else str(mid) for mid in msg_ids)
        typ, msg_data = mail_conn.fetch(msg_set, '(UID BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)])')

        if typ != 'OK' or not msg_data:
            print(f"Fetch failed or empty: {typ}, {msg_data}")
            return []

        for i in range(0, len(msg_data)):
            item = msg_data[i]
            if item is None or not isinstance(item, tuple) or len(item) < 2:
                continue

            try:
                raw_header = item[0].decode() if isinstance(item[0], bytes) else str(item[0])
                uid_match = re.search(r'UID (\d+)', raw_header)
                uid = uid_match.group(1) if uid_match else None

                email_message = email.message_from_bytes(item[1])
                subject = decode_mime_words(email_message.get("Subject", "No Subject"))
                sender = decode_mime_words(email_message.get("From", "Unknown Sender"))
                date_str = email_message.get("Date", "Unknown Date")
                email_date = parse_email_date(date_str)

                if cutoff_date and email_date and email_date < cutoff_date:
                    continue

                emails.append({
                    'subject': subject[:200],
                    'sender': sender[:200],
                    'date': date_str,
                    'message_id': email_message.get("Message-ID", "")[:100],
                    'uid': uid,
                    'datetime': email_date
                })

            except Exception as e:
                print(f"Error processing item: {item} — {e}")
                continue

    except Exception as e:
        print(f"Batch processing error: {e}")
    return emails

def process_chunk(args):
    chunk, folder, email_address, password, imap_server, cutoff_date = args
    mail_conn = create_connection(email_address, password, imap_server)
    if not mail_conn:
        return []
    try:
        mail_conn.select(folder)
        return get_email_info_batch(mail_conn, chunk, cutoff_date)
    finally:
        try:
            mail_conn.close()
            mail_conn.logout()
        except:
            pass

def scan_folder_fast(mail, folder_name, email_address, password, imap_server, days_back=None):
    try:
        status, _ = mail.select(folder_name)
        if status != 'OK':
            return []

        cutoff_date = None
        if days_back is not None and isinstance(days_back, int):
            pst = pytz.timezone('Asia/Manila')
            cutoff_date = datetime.now(pst) - timedelta(days=days_back)

        _, msg_ids = mail.search(None, 'ALL')
        msg_id_list = msg_ids[0].split()
        if not msg_id_list:
            return []

        chunk_size = 25
        chunks = [msg_id_list[i:i + chunk_size] for i in range(0, len(msg_id_list), chunk_size)]
        all_emails = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            args = [(chunk, folder_name, email_address, password, imap_server, cutoff_date) for chunk in chunks]
            for future in concurrent.futures.as_completed([executor.submit(process_chunk, arg) for arg in args]):
                all_emails.extend(future.result())

        for e in all_emails:
            e["email_address"] = email_address
            e["password"] = password
            e["imap_server"] = imap_server

        return all_emails
    except Exception as e:
        print(f"Error scanning {folder_name}: {e}")
        return []

def scan_unread_fast(mail, email_address, password, imap_server, cutoff_date=None):
    try:
        mail.select('INBOX')
        search_criteria = 'UNSEEN'
        if cutoff_date:
            date_str = cutoff_date.strftime('%d-%b-%Y')
            search_criteria = f'(UNSEEN SINCE "{date_str}")'
        _, msg_ids = mail.search(None, search_criteria)
        if not msg_ids[0]:
            return [], 0

        msg_id_list = msg_ids[0].split()
        total_unread = len(msg_id_list)

        chunk_size = 25
        chunks = [msg_id_list[i:i + chunk_size] for i in range(0, len(msg_id_list), chunk_size)]
        all_emails = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            args = [(chunk, 'INBOX', email_address, password, imap_server, cutoff_date) for chunk in chunks]
            for future in concurrent.futures.as_completed([executor.submit(process_chunk, arg) for arg in args]):
                all_emails.extend(future.result())

        for e in all_emails:
            e["email_address"] = email_address
            e["password"] = password
            e["imap_server"] = imap_server

        return all_emails, total_unread
    except Exception as e:
        print(f"Error scanning unread emails: {e}")
        return [], 0

def get_folder_list(mail):
    try:
        _, folders = mail.list()
        return [folder.decode().split('"')[-2] for folder in folders if len(folder.decode().split('"')) >= 3]
    except Exception as e:
        print(f"Error getting folder list: {e}")
        return []

def scan_all_fast(email_address, password, imap_server, days_back=None):
    start_time = time.time()
    mail = create_connection(email_address, password, imap_server)
    if not mail:
        return None

    try:
        results = {
            'unread': [], 'spam': [], 'junk': [], 'trash': [], 'folders': [],
            'total_unread_count': 0, 'scan_time': 0
        }

        cutoff_date = None
        if days_back is not None and isinstance(days_back, int):
            pst = pytz.timezone('Asia/Manila')
            cutoff_date = datetime.now(pst) - timedelta(days=days_back)

        results['folders'] = get_folder_list(mail)
        results['unread'], results['total_unread_count'] = scan_unread_fast(
            mail, email_address, password, imap_server, cutoff_date
        )

        spam_folders = ['Spam', 'Junk', 'SPAM', 'JUNK', '[Gmail]/Spam', 'Bulk Mail']
        for folder in results['folders']:
            if any(spam_folder.lower() == folder.lower() for spam_folder in spam_folders):
                emails = scan_folder_fast(mail, folder, email_address, password, imap_server, days_back)
                if 'spam' in folder.lower():
                    results['spam'].extend(emails)
                else:
                    results['junk'].extend(emails)

        # Read the setting from session_state
        include_trash = False
        try:
            import streamlit as st
            include_trash = st.session_state.get("include_trash", True)
        except:
            pass

        if include_trash:
            trash_folders = ['Trash', '[Gmail]/Trash', 'Deleted Items', 'Deleted Messages']
            for folder in results['folders']:
                if any(trash_folder.lower() == folder.lower() for trash_folder in trash_folders):
                    emails = scan_folder_fast(mail, folder, email_address, password, imap_server, days_back)
                    results['trash'].extend(emails)

        results['scan_time'] = time.time() - start_time
        return results
    finally:
        try:
            mail.close()
            mail.logout()
        except:
            pass

def delete_emails(folder_type, emails, all_folders, permanent=False):
    if not emails:
        return 0

    mail = None
    try:
        target_folder = next((f for f in all_folders if folder_type.lower() in f.lower()), None)
        if not target_folder:
            return 0

        uids = [email['uid'] for email in emails if email.get('uid')]
        if not uids:
            return 0

        mail = create_connection(
            emails[0].get('email_address'),
            emails[0].get('password'),
            emails[0].get('imap_server')
        )
        if not mail:
            return 0

        mail.select(target_folder)
        for i in range(0, len(uids), 50):
            batch = uids[i:i+50]
            mail.uid('STORE', ','.join(batch), '+FLAGS', '\\Deleted')

        if permanent:
            mail.expunge()

        return len(uids)
    except Exception as e:
        print(f"Error deleting emails: {e}")
        return 0
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except:
                pass
