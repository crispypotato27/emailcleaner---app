import streamlit as st

st.set_page_config(
    page_title="Login page",
    #layout="wide",
    initial_sidebar_state="collapsed"
)

from util import load_css, background, handle_login

if st.session_state.get("logged_in"):
    st.switch_page("pages/Dashboard.py")

# Background image
background("assets/bg.png")


with st.container():
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="left-column">', unsafe_allow_html=True)
        st.markdown("# Welcome back!")
        st.markdown("### Email Cleaner")
        st.markdown('*“An intelligent email assistant that automatically organizes, filters, and declutters your inbox — so you never miss what matters.”*')
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="right-column">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Login</div>', unsafe_allow_html=True)
        
        email = st.text_input("Email", label_visibility="collapsed", placeholder="Email", key="email_input")
        password = st.text_input("Password", label_visibility="collapsed", placeholder="Password (16 Characters)", key="password", type="password")
        login = st.button("Log in", key="login")

        # Main.py
        if login:
            if email and password:
                success, message, mail = handle_login(email, password)
                if success:
                    st.success("Login successful!")
                    st.success(message)
                    st.switch_page("pages/Dashboard.py")
                else:
                    st.error(message)
            else:
                st.warning("Please enter both email and password.")


        st.markdown("""
            <div class="tutorial">
                Here’s a <a href="https://www.youtube.com/watch?v=N_J3HCATA1c">tutorial</a> how to set up an account!
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
