import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

pinecone_api_key = os.getenv("PINECONE_API_KEY")

# Initialize Pinecone client
pc = Pinecone(api_key=pinecone_api_key)

index_name = os.getenv("PINECONE_INDEX")

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings()

# Initialize chat model
chat_model = ChatOpenAI(temperature=0)

def ensure_index_exists():
    """Ensure the Pinecone index exists, create if it doesn't"""
    try:
        # Check if index already exists
        if index_name not in pc.list_indexes().names():
            # Create index if it doesn't exist
            st.write(f"Creating index: {index_name}")
            pc.create_index(
                name=index_name,
                dimension=1536,  # OpenAI embeddings dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"  # Change to your preferred region
                )
            )
            st.info(f"Created new Pinecone index: {index_name}")
        
        return pc.Index(index_name)
    except Exception as e:
        st.error(f"Error with Pinecone index: {str(e)}")
        return None

def check_index_has_data():
    """Check if the Pinecone index contains any records"""
    try:
        index = pc.Index(index_name)
        # Get the index statistics
        stats = index.describe_index_stats()
        # Check if there are any vectors in the index
        return stats.total_vector_count > 0
    except Exception as e:
        st.error(f"Error checking index data: {str(e)}")
        return False

def process_pdf(file_path):
    """Process PDF file and return chunks"""
    try:
        # Load PDF
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        if not pages:
            raise ValueError("No content found in PDF")
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(pages)
        return chunks
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def get_qa_chain(vectorstore):
    """Create a question-answering chain"""
    return ConversationalRetrievalChain.from_llm(
        llm=chat_model,
        retriever=vectorstore.as_retriever(),
        return_source_documents=True
    )

def upload_document():
    """Handle document upload and processing"""
    st.subheader("Upload New Document")
    st.write("Upload a PDF file to process and add to the knowledge base")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Check file size
        file_size = uploaded_file.size / (1024 * 1024)  # Convert to MB
        if file_size > 200:
            st.error("File size exceeds 200 MB limit")
            return
        
        # Save uploaded file temporarily
        temp_file_path = f"temp_{uploaded_file.name}"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        try:
            with st.spinner("Processing PDF..."):
                # Process PDF
                chunks = process_pdf(temp_file_path)
                st.info(f"Extracted {len(chunks)} chunks from PDF")
                
            with st.spinner("Connecting..."):
                # Ensure index exists
                index = ensure_index_exists()
                if index is None:
                    st.error("Index is None")
                    return
                
            with st.spinner("Storing embeddings..."):
                try:
                    vectorstore = PineconeVectorStore.from_documents(
                        documents=chunks,
                        embedding=embeddings,
                        index_name=index_name,
                        pinecone_api_key=pinecone_api_key
                    )
                    st.success(f"Successfully processed {len(chunks)} chunks and stored in Pinecone!")
                    st.info("Your document is now ready for querying!")
                    
                except Exception as e2:
                    st.warning(f"Failed to store embeddings: {e2}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your API keys and try again.")
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

def chat_interface():
    """Handle the chat interface"""
    st.subheader("Ask Questions")
    st.write("Ask questions about your uploaded documents")
    
    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Check if index has data
    if not check_index_has_data():
        st.warning("No documents have been uploaded yet. Please upload a document first.")
        return
    
    # Initialize vectorstore
    try:
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=index_name,
            embedding=embeddings
        )
        
        # Create QA chain
        qa_chain = get_qa_chain(vectorstore)
        
        # Display chat history
        for q, a in st.session_state.chat_history:
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {a}")
            st.markdown("---")
        
        # Create a form for the input and button
        with st.form(key="question_form"):
            # Create a row for the input and button
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # Add question input
                question = st.text_input("", key="question_input", placeholder="Type your question here...")
            
            with col2:
                # Add submit button
                submit_button = st.form_submit_button("Send")
        
        # Process the question when the form is submitted
        if submit_button and question:
            with st.spinner("Thinking..."):
                # Get answer
                result = qa_chain({"question": question, "chat_history": st.session_state.chat_history})
                
                # Update chat history
                st.session_state.chat_history.append((question, result["answer"]))
                
                # Clear the input after sending
                st.session_state.question_input = ""
                
                # Rerun to update the chat history display
                st.rerun()
    
    except Exception as e:
        st.error(f"Error initializing vector store: {str(e)}")

def main():
    st.title("Document Q&A System")
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Please set your OPENAI_API_KEY in the .env file")
        return
    
    if not pinecone_api_key:
        st.error("Please set your PINECONE_API_KEY in the .env file")
        return
    
    # Create tabs
    tab1, tab2 = st.tabs(["Ask Questions", "Upload Document"])
    
    with tab1:
        chat_interface()
    
    with tab2:
        upload_document()

if __name__ == "__main__":
    main()