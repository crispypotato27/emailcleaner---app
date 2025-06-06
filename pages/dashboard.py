import streamlit as st
import pathlib
import base64

st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="collapsed"
)

with open("assets/bg2.png", "rb") as file:
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

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# path of css file
css_file = pathlib.Path(r"assets/style.css")

# Loads the external CSS
load_css(css_file)

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("You must log in first!")
    st.stop()

email = st.session_state.get("email", "Unknown User")

st.markdown(f"<h2><strong>{email.upper()}</strong></h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Clean Up Settings")
    st.image("https://img.icons8.com/ios-filled/50/000000/broom.png", width=50)
    if st.button("Open Clean Up Settings"):
        st.switch_page("pages/CleanUpSettings.py")

with col2:
    st.markdown("### Scan Email")
    st.image("https://img.icons8.com/ios-filled/50/000000/email.png", width=50)
    if st.button("Start Scan"):
        st.switch_page("pages/ScanEmails.py")

with col3:
    st.markdown("### Delete Subscriptions")
    st.image("https://img.icons8.com/ios-filled/50/000000/trash.png", width=50)
    if st.button("Delete Subscriptions"):
        st.switch_page("pages/DeleteSubscriptions.py")  

if st.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.success("You have been logged out.")
    st.switch_page("main.py")
