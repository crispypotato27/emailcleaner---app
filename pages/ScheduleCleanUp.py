import streamlit as st
import json
import os
from util import load_session_state

def save_schedule_to_json(email, schedule_config):
    os.makedirs("config", exist_ok=True)
    user_config_path = f"config/schedule_{email.replace('@', '_at_')}.json"
    with open(user_config_path, "w") as f:
        json.dump(schedule_config, f, indent=4)
    return user_config_path

st.set_page_config(page_title="Schedule Clean Up", layout="wide")
load_session_state()

# 🔐 Auth
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("You must log in first!")
    st.stop()

email = st.session_state.get("email", "user@example.com")
st.markdown("## 🧹 Schedule Clean Up")

# 🔘 Enable/Disable Scheduled Cleanup
enabled = st.toggle("🔘 Enable Scheduled Cleanup", value=False)

if enabled:
    # 🔁 Frequency
    frequency = st.radio(
        "How often should the cleanup run?",
        ["Every day", "Every Monday", "Every 1st of the Month", "Custom"],
        index=0,
        horizontal=True
    )

    custom_days = []
    if frequency == "Custom":
        st.markdown("#### 📅 Choose specific days of the week:")
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        custom_days = st.multiselect("Select days to run cleanup:", days_of_week)

    # 🕒 Time Input
    schedule_time = st.text_input("⏰ Setup Schedule Time (24hr format, HH:MM)", value="21:00")

    # 🧹 What to Delete
    delete_ui_to_internal = {
        "Unread older than 7 days": "Unread Emails",
        "Read older than 30 days": "Old Emails",
        "Emails from subscriptions": "Subscription Emails",
    }

    delete_options_ui = st.multiselect(
        "Select what you want to clean:",
        list(delete_ui_to_internal.keys()),
        default=["Unread older than 7 days"]
    )

    # ♻️ Move to Trash
    move_to_trash = st.checkbox("♻️ Move to Trash instead of deleting permanently", value=False)

    # ✨ Separate Spam and Trash
    include_spam = st.checkbox("🗑️ Include Spam", value=False)
    include_trash = False
    if not move_to_trash:
        include_trash = st.checkbox("🧺 Include Trash", value=False)

    # Build delete options
    internal_options = [delete_ui_to_internal[o] for o in delete_options_ui]
    if include_spam:
        internal_options.append("Spam")
    if include_trash:
        internal_options.append("Trash")

    # 📦 Build schedule config
    schedule_config = {
        "email": email,
        "enabled": True,
        "frequency": frequency,
        "time": schedule_time,
        "delete_options": internal_options,
        "move_to_trash": move_to_trash,
    }
    if frequency == "Custom":
        schedule_config["custom_days"] = custom_days

    # 💾 Save config
    path = save_schedule_to_json(email, schedule_config)
    st.success(f"✅ Saved schedule config to `{path}`")

    # 🧾 Preview Summary
    st.markdown("### 📊 What Will Be Cleaned:")
    for opt in delete_options_ui:
        st.markdown(f"- ✅ {opt}")
    if include_spam:
        st.markdown("- 🧪 Spam")
    if include_trash:
        st.markdown("- 🧹 Trash")

    if frequency == "Custom":
        custom_day_str = ", ".join(custom_days) if custom_days else "No days selected"
        st.info(f"📅 Scheduled: Custom on {custom_day_str} at {schedule_time}")
    else:
        st.info(f"📅 Scheduled: {frequency} at {schedule_time}")
else:
    # Save minimal config with enabled: False
    schedule_config = {
        "email": email,
        "enabled": False
    }
    path = save_schedule_to_json(email, schedule_config)
    st.warning("⚠️ Scheduled cleanup is currently disabled. No cleanup will run.")
    st.caption(f"(Saved config path: `{path}`)")

# 🔙 Back to settings
if st.button("Back to Clean Up Settings"):
    st.switch_page("pages/CleanUpSettings.py")
