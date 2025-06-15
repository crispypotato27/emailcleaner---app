import os
import json
from datetime import datetime
import pytz
from utilClean import scan_all_fast, delete_emails

def get_current_schedule_time():
    now = datetime.now(pytz.timezone("Asia/Manila"))
    return now.strftime("%H:%M"), now.strftime("%A"), now.day

def load_all_schedules(config_dir="config"):
    configs = []
    for file in os.listdir(config_dir):
        if file.startswith("schedule_") and file.endswith(".json"):
            with open(os.path.join(config_dir, file), "r") as f:
                configs.append(json.load(f))
    return configs

def clean_email(email, password, imap_server, delete_option, permanent=False):
    print(f"Running cleanup for {email} - {delete_option}")
    results = scan_all_fast(email, password, imap_server, days_back=30)

    if not results:
        print("Scan failed or returned no emails.")
        return

    all_folders = results['folders']
    cleaned_count = 0

    if delete_option == "Unread Emails":
        cleaned_count = delete_emails("INBOX", results["unread"], all_folders, permanent=True)

    elif delete_option == "Old Emails":
        all_old = []
        for group in ['unread', 'spam', 'junk', 'trash']:
            for e in results[group]:
                if e['datetime'] and (datetime.now(pytz.timezone('Asia/Manila')) - e['datetime']).days > 30:
                    all_old.append(e)
        cleaned_count = delete_emails("INBOX", all_old, all_folders, permanent=True)

    elif delete_option == "Spam":
        cleaned_count = delete_emails("Spam", results["spam"], all_folders, permanent=True)

    elif delete_option == "Trash":
        cleaned_count = delete_emails("Trash", results["trash"], all_folders, permanent=True)
    
    elif delete_option == "Subscription Emails":
        cleaned_count = delete_emails("INBOX", results["subscriptions"], all_folders, permanent=True)

    print(f"✅ Deleted {cleaned_count} emails for {email}")

def run_scheduled_cleanups():
    current_time, current_day, current_day_number = get_current_schedule_time()
    print(f"🕒 Running checks for {current_time} on {current_day}")

    configs = load_all_schedules()
    for config in configs:
        if not config.get("enabled", False):  # 👈 Skip if disabled or missing
            print(f"🚫 Skipping {config['email']} – schedule disabled.")
            continue

        if config["time"] != current_time:
            print(f"⏭️ {config['email']} – not scheduled at {current_time}")
            continue

        freq = config["frequency"]
        should_run = (
            freq == "Every day"
            or (freq == "Every Monday" and current_day == "Monday")
            or (freq == "Every 1st of the Month" and current_day_number == 1)
            or (freq == "Custom" and current_day in config.get("custom_days", []))
        )

        if should_run:
            email = config["email"]
            password = os.environ.get("EMAIL_PASSWORD_" + email.replace("@", "_at_"))
            if not password:
                print(f"⚠️ No password set for {email}. Skipping.")
                continue

            imap_server = "imap.gmail.com"
            for delete_option in config["delete_options"]:
                clean_email(email, password, imap_server, delete_option)
        else:
            print(f"⏭️ {config['email']} – does not match frequency rule.")

# You can now schedule this with GitHub Actions
if __name__ == "__main__":
    run_scheduled_cleanups()
