import streamlit as st
import re
from email import message_from_bytes
import webbrowser

from util import (
    load_session_state,
    get_imap_connection,
    extract_unsubscribe_link,
    load_unsubscribed_emails,
    save_unsubscribed_email,
)

st.set_page_config(page_title="Delete Subscriptions", layout="wide", initial_sidebar_state="collapsed")
load_session_state()



if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("You must log in first!")
    st.stop()

email_address = st.session_state.get("email", "Unknown User")
mail = get_imap_connection()
if not mail:
    st.error("IMAP connection not found. Please log in again.")
    st.stop()

# Only load once into session
if "subscriptions" not in st.session_state:
 with st.spinner("Loading your subscriptions..."):
    unsubscribed_emails = load_unsubscribed_emails(email_address)

    mail.select("inbox")
    result, data = mail.search(None, '(BODY "unsubscribe")')
    email_ids = data[0].split()

    seen_emails = set()
    subscriptions = []

    for e_id in email_ids[:100]:
        _, msg_data = mail.fetch(e_id, '(RFC822)')
        raw_email = msg_data[0][1]
        msg = message_from_bytes(raw_email)

        from_header = msg.get('From', '')
        name_email_match = re.search(r'([^<]+)<([^>]+)>', from_header)
        if name_email_match:
            name = name_email_match.group(1).strip()
            sender_email = name_email_match.group(2)

            if sender_email in seen_emails or sender_email in unsubscribed_emails:
                continue
            seen_emails.add(sender_email)

            unsub_type, unsub_link = extract_unsubscribe_link(msg)

            subscriptions.append({
                "name": name,
                "email": sender_email,
                "unsub_type": unsub_type,
                "unsub_link": unsub_link,
            })

    st.session_state.subscriptions = subscriptions

# Display and handle unsubscribes
subs = st.session_state.subscriptions
updated_subs = []

for sub in subs:
    col1, col2, col3 = st.columns([2, 4, 2])
    with col1:
        st.markdown(f"**{sub['name']}**")
    with col2:
        st.markdown(sub["email"])
    with col3:
        if st.button("Unsubscribe", key=sub['email']):
            if sub["unsub_link"]:
                if sub["unsub_type"] == "http":
                    webbrowser.open(sub["unsub_link"])
                    st.success(f"Opened unsubscribe link for {sub['email']}")
                elif sub["unsub_type"] == "mailto":
                    st.info(f"Please send an unsubscribe email to {sub['unsub_link']}")
                else:
                    st.warning("Unsubscribe method unknown.")
            else:
                st.warning(f"No unsubscribe link found for {sub['email']}")

            save_unsubscribed_email(email_address, sub["email"])
            continue  # Skip adding back

    updated_subs.append(sub)

st.session_state.subscriptions = updated_subs

st.markdown("---")
if st.button("Back to Dashboard"):
    st.switch_page("pages/Dashboard.py")
