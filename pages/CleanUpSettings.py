import streamlit as st
from util import load_session_state

st.set_page_config(page_title="Clean Up Settings", layout="wide", initial_sidebar_state="collapsed")
load_session_state()

if "delete_mode" not in st.session_state:
    st.session_state["delete_mode"] = "Move to Trash (Recommended)"

if "include_trash" not in st.session_state:
    st.session_state["include_trash"] = True

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("You must log in first!")
    st.stop()

st.markdown("## 🧹 Clean Up Settings")

# Delete behavior setting
st.markdown("### Delete Mode")
delete_mode = st.radio(
    "How do you want to delete emails?",
    ["Move to Trash (Recommended)", "Permanent Delete"],
    index=0 if st.session_state.get("delete_mode") != "Permanent Delete" else 1
)

# Save the choice in session state
st.session_state["delete_mode"] = delete_mode

# Trash folder toggle
st.markdown("### Trash Folder")
include_trash = st.checkbox(
    "Include emails from Trash folder during scan",
    value=st.session_state.get("include_trash", True)
)
st.session_state["include_trash"] = include_trash

# Navigation
st.markdown("---")
col1, col2 = st.columns([1,0.11])

with col1:
    if st.button("Set up a scheduled clean up"):
        st.switch_page("pages/ScheduleCleanUp.py")

with col2:
    if st.button("Back to Dashboard"):
        st.switch_page("pages/Dashboard.py")
