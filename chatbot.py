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

# Initialize Pinecone client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

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

def main():
    st.title("PDF Document Processor and Q&A")
    st.write("Upload a PDF file to process and ask questions about it")
    
    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Please set your OPENAI_API_KEY in the .env file")
        return
    
    if not os.getenv("PINECONE_API_KEY"):
        st.error("Please set your PINECONE_API_KEY in the .env file")
        return
    
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
                        pinecone_api_key=os.getenv("PINECONE_API_KEY")
                    )
                    
                    # Create QA chain
                    qa_chain = get_qa_chain(vectorstore)
                    
                    st.success(f"Successfully processed {len(chunks)} chunks and stored in Pinecone!")
                    st.info("Your documents are now ready for querying!")
                    
                    # Add question input
                    st.subheader("Ask questions about your PDF")
                    question = st.text_area("Enter your question:", height=100)
                    
                    if question:
                        with st.spinner("Thinking..."):
                            # Get answer
                            result = qa_chain({"question": question, "chat_history": st.session_state.chat_history})
                            
                            # Update chat history
                            st.session_state.chat_history.append((question, result["answer"]))
                            
                            # Display answer
                            st.subheader("Answer:")
                            st.write(result["answer"])
                            
                            # Display source documents
                            with st.expander("View Source Documents"):
                                for doc in result["source_documents"]:
                                    st.write("---")
                                    st.write(doc.page_content)
                                    
                except Exception as e2:
                    st.warning(f"Method 2 failed: {e2}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your API keys and try again.")
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

if __name__ == "__main__":
    main()