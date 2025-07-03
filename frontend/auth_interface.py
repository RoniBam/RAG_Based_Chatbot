import streamlit as st
import time
from backend.auth_manager import AuthManager
from backend.session_manager import SessionManager

class AuthInterface:
    def __init__(self):
        self.auth_manager = AuthManager()
        self.session_manager = SessionManager()
    
    def render_login(self):
        """Render the login form"""
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1>🔐 Document Q&A System</h1>
            <p style='font-size: 1.2rem; color: #666;'>Please login to continue</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create a centered container
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.container():
                
                st.subheader("Login")
                
                with st.form("login_form", clear_on_submit=True):
                    username = st.text_input("Username or Email", placeholder="Enter your username or email")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                      
                    col1, col2 = st.columns(2)
                    with col1:
                        login_button = st.form_submit_button("Login", use_container_width=True, type="primary")
                    with col2:
                        switch_to_signup = st.form_submit_button("Create Account", use_container_width=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Handle form submissions
                if login_button:
                    if username and password:
                        success, message, user_data = self.auth_manager.login_user(username, password)
                        if success:
                            # Set user session
                            self.session_manager.set_user_session(user_data)
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please fill in all fields")
                
                if switch_to_signup:
                    st.session_state.auth_mode = "signup"
                    st.rerun()
    
    def render_signup(self):
        """Render the signup form"""
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1>🔐 Document Q&A System</h1>
            <p style='font-size: 1.2rem; color: #666;'>Create your account</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create a centered container
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.container():
                st.markdown("""
                <div style='background-color: #f0f2f6; padding: 2rem; border-radius: 10px; border: 1px solid #ddd;'>
                """, unsafe_allow_html=True)
                
                st.subheader("Sign Up")
                
                with st.form("signup_form", clear_on_submit=True):
                    username = st.text_input("Username", placeholder="Choose a username (min 3 characters)")
                    email = st.text_input("Email", placeholder="Enter your email address")
                    password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 characters)")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                    
                    # Add some spacing
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        signup_button = st.form_submit_button("Sign Up", use_container_width=True, type="primary")
                    with col2:
                        switch_to_login = st.form_submit_button("Back to Login", use_container_width=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Handle form submissions
                if signup_button:
                    if username and email and password and confirm_password:
                        if password != confirm_password:
                            st.error("Passwords do not match")
                        else:
                            success, message = self.auth_manager.register_user(username, email, password)
                            if success:
                                st.success(f"✅ {message}")
                                st.info("You can now login with your new account!")
                                st.session_state.auth_mode = "login"
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    else:
                        st.error("Please fill in all fields")
                
                if switch_to_login:
                    st.session_state.auth_mode = "login"
                    st.rerun()
    
    def render_auth_page(self):
        """Render the main authentication page"""
        # Initialize session state
        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"
        
        # Check if user is already authenticated
        if st.session_state.get("authenticated", False):
            st.success("You are already logged in!")
            if st.button("Continue to App"):
                st.session_state.current_page = "main"
                st.rerun()
            return
        
        # Render login or signup based on current mode
        if st.session_state.auth_mode == "login":
            self.render_login()
        else:
            self.render_signup()
    
    def logout(self):
        """Logout the current user"""
        self.session_manager.clear_session()
        st.success("Logged out successfully!")
        st.rerun()
