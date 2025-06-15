import json
from utilclean import scan_all_fast, delete_emails

# Load config
with open("config/schedule_config.json") as f:
    config = json.load(f)

# Use config to determine behavior
frequency = config["frequency"]
delete_target = config["delete_options"]
scan_results = scan_all_fast(...)

if delete_target == "Unread Emails":
    emails_to_delete = scan_results["unread"]
elif delete_target == "Old Emails":
    emails_to_delete = [e for e in scan_results["unread"] if e["datetime"] and (datetime.now() - e["datetime"]).days > 30]
elif delete_target == "Spam":
    emails_to_delete = scan_results["spam"] + scan_results["junk"]
else:
    emails_to_delete = scan_results["unread"] + scan_results["spam"] + scan_results["junk"] + scan_results["trash"]

count = delete_emails("inbox", emails_to_delete, scan_results["folders"])
print(f"Deleted {count} emails.")
