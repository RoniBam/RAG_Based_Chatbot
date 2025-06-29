import streamlit as st
from backend.vector_store import VectorStoreManager
from backend.qa_chain import QAChain

class ChatInterface:
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.qa_chain = QAChain()
    
    def render(self):
        """Render the chat interface"""
        st.subheader("Ask Questions")
        st.write("Ask questions about your uploaded documents")
        
        # Initialize session state for chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Initialize session state for current answer
        if "current_answer" not in st.session_state:
            st.session_state.current_answer = None
        if "current_question" not in st.session_state:
            st.session_state.current_question = None
        
        # Clear cached file list when entering this tab to ensure fresh data
        if "available_files_cache" in st.session_state:
            del st.session_state.available_files_cache
        
        # Check if index has data
        try:
            if not self.vector_store_manager.check_index_has_data():
                st.warning("No documents have been uploaded yet. Please upload a document first.")
                return
        except Exception as e:
            st.error(f"Error checking documents: {str(e)}")
            return
        
        # Get available files
        try:
            available_files = self.vector_store_manager.get_available_files()
            
            if not available_files:
                st.warning("No documents found in the database.")
                return
            
            # File selection with no default value
            st.write("**Select a document to query:**")
            selected_file = st.selectbox(
                "Choose a document:",
                options=[""] + available_files,  # Add empty option at the beginning
                key="file_selector",
                help="Select the document you want to ask questions about",
                placeholder="Select a document..."
            )
            
            # Check if a file is selected
            if not selected_file:
                st.error("⚠️ Please select a document before asking questions.")
                return
            
            # Display selected file
            st.success(f" Currently querying: **{selected_file}**")
            
        except Exception as e:
            st.error(f"Error getting available files: {str(e)}")
            return
        
        # Initialize vectorstore with file filter
        try:
            vectorstore = self.vector_store_manager.get_vectorstore(filename_filter=selected_file)
            qa_chain = self.qa_chain.create_qa_chain(vectorstore)
            
            # Create a container for the input and button
            input_container = st.container()
            
            with input_container:
                # Create a row for the input and button
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    # Add question input with proper label
                    question = st.text_input(
                        "Question", 
                        key="question_input", 
                        placeholder="Type your question here...",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    # Add send button with proper alignment
                    st.markdown("<div style='padding-top: 20px;'>", unsafe_allow_html=True)
                    send_button = st.button("Send", use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # Process the question when the send button is clicked
            if send_button and question:
                with st.spinner("Thinking..."):
                    result = qa_chain({"question": question, "chat_history": st.session_state.chat_history})
                    st.session_state.chat_history.append((question, result["answer"]))
                    # Store current question and answer for display
                    st.session_state.current_question = question
                    st.session_state.current_answer = result["answer"]
                    st.rerun()
            
            # Display only the current answer
            if st.session_state.current_answer:
                st.write("---")
                st.write("**Current Question & Answer:**")
                st.markdown(f"**Q:** {st.session_state.current_question}")
                st.markdown(f"**A:** {st.session_state.current_answer}")
                
                # Show chat history expander only if there are more than one conversation
                if len(st.session_state.chat_history) > 1:
                    with st.expander(f"View Chat History ({len(st.session_state.chat_history)} conversations)"):
                        for i, (q, a) in enumerate(st.session_state.chat_history):
                            st.markdown(f"**Q{i+1}:** {q}")
                            st.markdown(f"**A{i+1}:** {a}")
                            if i < len(st.session_state.chat_history) - 1:
                                st.markdown("---")
        
        except Exception as e:
            st.error(f"Error initializing chat: {str(e)}")

        # Clear cached file list when entering this tab to ensure fresh data
        self.vector_store_manager.clear_cache()