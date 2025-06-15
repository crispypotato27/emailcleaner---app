import streamlit as st
from utilClean import scan_all_fast, delete_emails
from datetime import datetime, timedelta
from util import background, load_session_state
import pytz

# background("assets/bg2.png")
load_session_state()

st.title("Email Scan Results")
st.markdown("View and manage your unread, spam, junk, and trash emails.")

# Ensure user is logged in
if not st.session_state.get("logged_in"):
    st.error("You must log in first.")
    st.stop()

email_address = st.session_state.get("email")
password = st.session_state.get("app_password")
imap_server = "imap.gmail.com"

# Scan Settings
st.subheader("Scan Settings")
col1, col2 = st.columns(2)

with col1:
    scan_option = st.selectbox(
        "How far back do you want to scan?",
        ["Last 7 days", "Last 30 days", "Last 90 days", "Last 6 months", "Last year", "All emails"],
        index=1
    )

with col2:
    include_trash = st.checkbox("Include Trash Folder in Scan", value=True)

if scan_option == "Last 7 days":
    days_back = 7
elif scan_option == "Last 30 days":
    days_back = 30
elif scan_option == "Last 90 days":
    days_back = 90
elif scan_option == "Last 6 months":
    days_back = 180
elif scan_option == "Last year":
    days_back = 365
else:
    days_back = None

pst = pytz.timezone('Asia/Manila')
if days_back is not None:
    cutoff_date = datetime.now(pst) - timedelta(days=days_back)
    st.info(f"🗓️ Scanning emails from {cutoff_date.strftime('%B %d, %Y')} onwards")
else:
    st.info("🗓️ Scanning all emails")

# Scan Trigger
if st.button("🔍 Scan Mailbox"):
    with st.spinner("Scanning mailbox, please wait..."):
        results = scan_all_fast(email_address, password, imap_server, days_back)
        if results:
            st.session_state.scan_results = results
            st.session_state.scan_date_range = scan_option
            st.session_state.include_trash = include_trash
            st.success(f"Scan completed in {results['scan_time']:.2f} seconds!")
        else:
            st.error("Scan failed. Please check your credentials or try again later.")

# Results Display
results = st.session_state.get("scan_results", None)
if results is not None:
    scan_range = st.session_state.get("scan_date_range", "Unknown")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📥 Unread Emails", results['total_unread_count'])
    with col2:
        st.metric("🚫 Spam Emails", len(results['spam']))
    with col3:
        st.metric("🧃 Junk Emails", len(results['junk']))
    with col4:
        st.metric("🗑️ Trash Emails", len(results.get('trash', [])))

    tab1, tab2, tab3 = st.tabs(["📥 Unread", "🛡 Spam / Junk", "🗑 Trash"])

    # UNREAD TAB
    with tab1:
        st.subheader("Unread Emails")
        if not results['unread']:
            st.info("No unread emails found in the selected time range.")
        else:
            sort_by = st.selectbox("Sort by:", ["Date (Newest first)", "Date (Oldest first)", "Sender", "Subject"])
            sorted_emails = results['unread'].copy()

            if sort_by == "Date (Newest first)":
                sorted_emails.sort(key=lambda x: x.get('datetime') or datetime.min.replace(tzinfo=pytz.UTC), reverse=True)
            elif sort_by == "Date (Oldest first)":
                sorted_emails.sort(key=lambda x: x.get('date', ''))
            elif sort_by == "Sender":
                sorted_emails.sort(key=lambda x: x.get('sender', '').lower())
            elif sort_by == "Subject":
                sorted_emails.sort(key=lambda x: x.get('subject', '').lower())

            for email in sorted_emails:
                with st.expander(f"📧 {email['subject']}"):
                    st.markdown(f"**From:** {email['sender']}")
                    st.markdown(f"**Date:** {email['date']}")
                    st.markdown(f"**Message ID:** {email['message_id']}")

    # SPAM/JUNK TAB
    with tab2:
        st.subheader("Filter and Manage Spam or Junk Emails")
        folder_choice = st.radio("Choose folder to view:", ["Spam", "Junk"], horizontal=True)

        if folder_choice == "Spam":
            selected_emails = results['spam']
            folder_key = "spam"
        else:
            selected_emails = results['junk']
            folder_key = "junk"

        if not selected_emails:
            st.info(f"No {folder_choice.lower()} emails found.")
        else:
            st.warning(f"Found {len(selected_emails)} {folder_choice.lower()} emails")

            with st.expander(f"📋 Preview first 3 {folder_choice.lower()} emails"):
                for i, email in enumerate(selected_emails[:3]):
                    st.markdown(f"**{i+1}.** {email['subject']} - From: {email['sender']}")

            if st.checkbox(f"Show all {folder_choice.lower()} email details"):
                for email in selected_emails:
                    with st.expander(email['subject']):
                        st.markdown(f"**From:** {email['sender']}")
                        st.markdown(f"**Date:** {email['date']}")
                        st.markdown(f"**Message ID:** {email['message_id']}")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"🗑️ Delete All {folder_choice} Emails", type="primary", key=f"delete_{folder_key}"):
                st.session_state.confirm_delete = True
                st.session_state.delete_folder = folder_key

        with col2:
            if st.session_state.get("confirm_delete") and st.session_state.get("delete_folder") == folder_key:
                if st.button("✅ Confirm Delete", type="secondary", key=f"confirm_{folder_key}"):
                    with st.spinner(f"Deleting {len(selected_emails)} {folder_choice.lower()} emails..."):
                        delete_mode = st.session_state.get("delete_mode", "Move to Trash (Recommended)")
                        permanent = delete_mode == "Permanent Delete"

                        deleted_count = delete_emails(folder_key, selected_emails, results['folders'], permanent=permanent)
                        st.success(f"Deleted {deleted_count} {folder_choice.lower()} emails.")

                        st.session_state.confirm_delete = False
                        st.session_state.delete_folder = None
                        st.rerun()

                if st.button("❌ Cancel", key=f"cancel_{folder_key}"):
                    st.session_state.confirm_delete = False
                    st.session_state.delete_folder = None
                    st.rerun()

    # TRASH TAB
    with tab3:
        st.subheader("Manage Trash Emails")
        trash_emails = results.get('trash', [])
        if not trash_emails:
            st.info("No trash emails found.")
        else:
            st.success(f"Found {len(trash_emails)} emails in Trash")

            filter_term = st.text_input("🔍 Filter by sender or subject")
            filtered = [
                e for e in trash_emails
                if filter_term.lower() in e['sender'].lower() or filter_term.lower() in e['subject'].lower()
            ] if filter_term else trash_emails

            for email in filtered:
                with st.expander(email['subject']):
                    st.markdown(f"**From:** {email['sender']}")
                    st.markdown(f"**Date:** {email['date']}")
                    st.markdown(f"**Message ID:** {email['message_id']}")

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Delete All Trash Emails", type="primary", key="delete_trash"):
                    st.session_state.confirm_delete = True
                    st.session_state.delete_folder = "trash"

            with col2:
                if st.session_state.get("confirm_delete") and st.session_state.get("delete_folder") == "trash":
                    if st.button("✅ Confirm Delete", type="secondary", key="confirm_trash"):
                        with st.spinner(f"Deleting {len(trash_emails)} trash emails..."):
                            permanent = True  # Always permanent in Trash
                            deleted_count = delete_emails("trash", trash_emails, results['folders'], permanent=permanent)
                            st.success(f"Permanently deleted {deleted_count} trash emails.")
                            st.session_state.confirm_delete = False
                            st.session_state.delete_folder = None
                            st.rerun()

                    if st.button("❌ Cancel", key="cancel_trash"):
                        st.session_state.confirm_delete = False
                        st.session_state.delete_folder = None
                        st.rerun()
