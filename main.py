import streamlit as st
import pathlib
import base64

# Background Image
with open("assets/bg.png", "rb") as file:
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

# Define the correct path to the CSS file
css_file = pathlib.Path(r"C:\Users\bokis\OneDrive\Dokumen\School\Codes\main\assets\style.css")

# Load the external CSS
load_css(css_file)

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown('<div class="left-column">', unsafe_allow_html=True)
    st.markdown("## Welcome back!")
    st.markdown("### Email Cleaner")
    st.markdown('*“An intelligent email assistant that automatically organizes, filters, and declutters your inbox — so you never miss what matters.”*')
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="right-column">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Login</div>', unsafe_allow_html=True)
    email = st.text_input("Email", label_visibility="collapsed", placeholder="Email", key="email")
    password = st.text_input("Password", label_visibility="collapsed", placeholder="App password",key="password", type="password")
    login = st.button("Log in", key="login")

    st.markdown("""
        <div class="tutorial">
            Here’s a <a href="https://www.youtube.com/watch?v=N_J3HCATA1c">tutorial</a> how to set up an account!
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)



