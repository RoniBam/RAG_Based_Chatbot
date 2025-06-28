import streamlit as st
from .chat_interface import ChatInterface
from .upload_interface import UploadInterface
from backend.config import *

def main():
    st.title("Document Q&A System")
    
    # Check for required environment variables
    if not OPENAI_API_KEY:
        st.error("Please set your OPENAI_API_KEY in the .env file")
        return
    
    if not PINECONE_API_KEY:
        st.error("Please set your PINECONE_API_KEY in the .env file")
        return
    
    # Initialize interfaces
    chat_interface = ChatInterface()
    upload_interface = UploadInterface()
    
    # Create tabs
    tab1, tab2 = st.tabs(["Ask Questions", "Upload Document"])
    
    with tab1:
        chat_interface.render()
    
    with tab2:
        upload_interface.render()

if __name__ == "__main__":
    main()
