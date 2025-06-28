import streamlit as st
from .chat_interface import ChatInterface
from .upload_interface import UploadInterface
from .auth_interface import AuthInterface
from .admin_interface import AdminInterface
from backend.config import *

# Set page config at the very beginning - this must be the first Streamlit command
st.set_page_config(
    page_title="Document Q&A System",
    page_icon="🔐",
    layout="wide"
)

def main():
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_page" not in st.session_state:
        st.session_state.current_page = "auth"
    
    # Check for required environment variables
    if not OPENAI_API_KEY:
        st.error("Please set your OPENAI_API_KEY in the .env file")
        return
    
    if not PINECONE_API_KEY:
        st.error("Please set your PINECONE_API_KEY in the .env file")
        return
    
    # Authentication check - redirect to login if not authenticated
    if not st.session_state.authenticated:
        auth_interface = AuthInterface()
        auth_interface.render_auth_page()
        return
    
    # Main application (user is authenticated)
    st.title("📚 Document Q&A System")
    
    # User info and navigation
    user_data = st.session_state.get("user_data", {})
    if user_data:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            admin_badge = "👑 Admin" if user_data.get("is_admin", False) else "👤 User"
            st.write(f"Welcome, **{user_data.get('username', 'User')}** {admin_badge}")
        with col2:
            if user_data.get("is_admin", False):
                if st.button("🔧 Admin Panel"):
                    st.session_state.current_page = "admin"
                    st.rerun()
        with col3:
            if st.button("🚪 Logout"):
                auth_interface = AuthInterface()
                auth_interface.logout()
                return
    
    # Page routing
    if st.session_state.get("current_page") == "admin":
        admin_interface = AdminInterface()
        admin_interface.render()
        if st.button("← Back to Main"):
            st.session_state.current_page = "main"
            st.rerun()
    else:
        # Main application tabs
        tab1, tab2 = st.tabs(["Ask Questions", "Upload Document"])
        
        with tab1:
            chat_interface = ChatInterface()
            chat_interface.render()
        
        with tab2:
            upload_interface = UploadInterface()
            upload_interface.render()

if __name__ == "__main__":
    main()
