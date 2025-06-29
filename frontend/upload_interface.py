import streamlit as st
import os
from backend.document_processor import DocumentProcessor
from backend.vector_store import VectorStoreManager

class UploadInterface:
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.vector_store_manager = VectorStoreManager()
    
    def render(self):
        """Render the upload interface"""
        st.subheader("Upload New Document")
        st.write("Upload a PDF file to process and add to your knowledge base")
        
        # Get current user information
        user_data = st.session_state.get("user_data", {})
        if not user_data:
            st.error("User information not found. Please login again.")
            return
        
        username = user_data.get("username", "")
        user_id = user_data.get("id", "")
        
        # Display user info
        st.info(f"📁 Uploading documents for user: **{username}**")
        
        # File uploader
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None:
            try:
                # Validate file size
                self.document_processor.validate_file_size(uploaded_file.size)
                
                # Save uploaded file temporarily
                temp_file_path = f"temp_{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                try:
                    with st.spinner("Processing PDF..."):
                        chunks = self.document_processor.process_pdf(
                            temp_file_path, 
                            uploaded_file.name, 
                            username, 
                            user_id
                        )
                        st.info(f"Extracted {len(chunks)} chunks from PDF")
                    
                    with st.spinner("Connecting..."):
                        self.vector_store_manager.ensure_index_exists()
                    
                    with st.spinner("Storing embeddings..."):
                        self.vector_store_manager.store_documents(chunks)
                        st.success(f"Successfully processed {len(chunks)} chunks and stored in Pinecone!")
                        st.info(f"Document '{uploaded_file.name}' is now ready for querying!")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
            
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
