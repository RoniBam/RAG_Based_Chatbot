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
        
        # Check if index has data
        try:
            if not self.vector_store_manager.check_index_has_data():
                st.warning("No documents have been uploaded yet. Please upload a document first.")
                return
        except Exception as e:
            st.error(f"Error checking documents: {str(e)}")
            return
        
        # Initialize vectorstore
        try:
            vectorstore = self.vector_store_manager.get_vectorstore()
            qa_chain = self.qa_chain.create_qa_chain(vectorstore)
            
            # Display chat history
            for q, a in st.session_state.chat_history:
                st.markdown(f"**Q:** {q}")
                st.markdown(f"**A:** {a}")
                st.markdown("---")
            
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
                    #st.markdown("<div style='padding-top: 5px;'>", unsafe_allow_html=True)
                    send_button = st.button("Send", use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # Process the question when the send button is clicked
            if send_button and question:
                with st.spinner("Thinking..."):
                    result = qa_chain({"question": question, "chat_history": st.session_state.chat_history})
                    st.session_state.chat_history.append((question, result["answer"]))
                    st.session_state.question_input = ""
                    st.rerun()
        
        except Exception as e:
            st.error(f"Error initializing chat: {str(e)}")
