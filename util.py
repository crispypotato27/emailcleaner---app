import imaplib
import pathlib
import base64
import json
import os
import re
from bs4 import BeautifulSoup
import streamlit as st

SESSION_FILE = "session.json"
UNSUB_DIR = os.path.join("storage", "unsubscribed")

# --- Saves which emails you Unsub from ---
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def handle_login(email, password):
    """Handle IMAP login and session storage."""
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email, password)

        # Set Streamlit session state
        st.session_state.logged_in = True
        st.session_state.email = email
        st.session_state.app_password = password

        # Save persistent session
        save_session({
            "logged_in": True,
            "email": email,
            "app_password": password
        })

        return True, f"Logged in as {email}!", mail

    except imaplib.IMAP4.error as e:
        return False, f"Login failed: {e}", None
    
def _get_user_file(email):
    os.makedirs(UNSUB_DIR, exist_ok=True)
    safe_email = email.replace("@", "_at_").replace(".", "_dot_")
    return os.path.join(UNSUB_DIR, f"{safe_email}.json")

def load_unsubscribed_emails(email):
    path = _get_user_file(email)
    try:
        with open(path, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_unsubscribed_email(user_email, target_email):
    unsubscribed = load_unsubscribed_emails(user_email)
    unsubscribed.add(target_email)
    with open(_get_user_file(user_email), "w") as f:
        json.dump(list(unsubscribed), f)

# --- Unsub from emails ---
def extract_unsubscribe_link(msg):
    """
    Extract unsubscribe link and type ('http' or 'mailto') from an email.message.Message object.
    Returns tuple (type, link) or (None, None) if not found.
    """
    keywords = [
        'unsubscribe', 'subscription', 'optout', 'notifications',
        'abmelden', 'désabonnement', 'cancel', 'manage preferences'
    ]
    unsubscribe_link = None
    unsubscribe_type = None

    def check_text_for_mailto(text):
        mailtos = re.findall(r'(mailto:\S+)', text, re.I)
        for mailto in mailtos:
            if any(kw in mailto.lower() for kw in keywords):
                return 'mailto', mailto
        return None, None

    def check_html_for_link(html):
        soup = BeautifulSoup(html, 'html.parser')
        anchors = soup.find_all('a')
        for a in anchors:
            href = a.get('href', '')
            if href:
                href_lower = href.lower()
                text_lower = a.get_text(strip=True).lower()
                if any(kw in href_lower for kw in keywords) or any(kw in text_lower for kw in keywords):
                    if href_lower.startswith('mailto:'):
                        return 'mailto', href
                    elif href_lower.startswith('http'):
                        return 'http', href
                    else:
                        return 'unknown', href
        return None, None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)

            if not payload:
                continue

            try:
                content = payload.decode('utf-8', errors='ignore')
            except Exception:
                content = str(payload)

            if content_type == 'text/html':
                unsubscribe_type, unsubscribe_link = check_html_for_link(content)
            elif content_type == 'text/plain':
                unsubscribe_type, unsubscribe_link = check_text_for_mailto(content)

            if unsubscribe_link:
                return unsubscribe_type, unsubscribe_link

    else:
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                text = payload.decode('utf-8', errors='ignore')
            except Exception:
                text = str(payload)
            return check_text_for_mailto(text)

    return None, None

# --- Connect to IMAP ---
def get_imap_connection():
    email = st.session_state.get("email")
    password = st.session_state.get("app_password")
    if not (email and password):
        return None
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email, password)
        return mail
    except Exception as e:
        st.error(f"IMAP login failed: {e}")
        return None

# --- Session Utilities ---
def save_session(data: dict):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f)

def load_session_state():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            for key, value in data.items():
                st.session_state[key] = value

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# --- Optional UI tools ---
def load_css(path):
    css_path = pathlib.Path(path)
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def action_block(title, img_url, button_label, page_name):
    with st.container():
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
        st.markdown(f'<img src="{img_url}" width="50" />', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button(button_label, key=button_label):
            st.switch_page(page_name)

def background(path):
    with open(path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{encoded}");
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
