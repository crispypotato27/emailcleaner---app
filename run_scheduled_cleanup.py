import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import os
from utilClean import scan_all_fast, delete_emails

# Load credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]), scope
)
client = gspread.authorize(credentials)
sheet = client.open("Email Cleaner Database").sheet1

# Get current PH time
now = datetime.now(pytz.timezone("Asia/Manila"))
now_time = now.strftime("%H:%M")

# Read all rows
records = sheet.get_all_records()

for row in records:
    email = row["Email"]
    password = row["Password"]
    imap_server = row.get("IMAP Server", "imap.gmail.com")  # default to Gmail
    freq = row["Frequency"]
    scheduled_time = row["Time"]
    delete_option = row["Delete Options"]

    if scheduled_time == now_time:
        print(f"Running cleanup for {email} - {delete_option}")

        results = scan_all_fast(email, password, imap_server, days_back=30)

        if not results:
            print("Scan failed or returned no emails.")
            continue

        all_folders = results['folders']
        cleaned_count = 0

        if delete_option == "Unread Emails":
            cleaned_count = delete_emails("INBOX", results["unread"], all_folders, permanent=True)

        elif delete_option == "Spam and Junk":
            spam_emails = results["spam"] + results["junk"]
            cleaned_count = delete_emails("Spam", spam_emails, all_folders, permanent=True)

        elif delete_option == "Old Emails":
            all_old = []
            for group in ['unread', 'spam', 'junk', 'trash']:
                for e in results[group]:
                    if e['datetime'] and (datetime.now(pytz.timezone('Asia/Manila')) - e['datetime']).days > 30:
                        all_old.append(e)
            cleaned_count = delete_emails("INBOX", all_old, all_folders, permanent=True)

        elif delete_option == "All (Unread + Spam + Trash)":
            all_combined = results["unread"] + results["spam"] + results["junk"] + results["trash"]
            cleaned_count = delete_emails("INBOX", all_combined, all_folders, permanent=True)

        print(f"✅ Deleted {cleaned_count} emails for {email}")

