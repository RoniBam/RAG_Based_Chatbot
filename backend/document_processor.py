from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import datetime
from .config import *

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len
        )
    
    def process_pdf(self, file_path, filename, username, user_id):
        """Process PDF file and return chunks with metadata"""
        try:
            # Load PDF
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            
            if not pages:
                raise ValueError("No content found in PDF")
            
            # Split text into chunks
            chunks = self.text_splitter.split_documents(pages)
            
            # Add metadata to each chunk
            upload_time = datetime.now().isoformat()
            for chunk in chunks:
                chunk.metadata[METADATA_FILENAME_KEY] = filename
                chunk.metadata[METADATA_UPLOAD_TIME_KEY] = upload_time
                chunk.metadata[METADATA_USERNAME_KEY] = username
                chunk.metadata[METADATA_USER_ID_KEY] = user_id
            
            return chunks
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def validate_file_size(self, file_size_bytes):
        """Validate file size"""
        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB} MB limit")
        return True
