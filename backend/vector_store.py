from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from .config import *

class VectorStoreManager:
    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.embeddings = OpenAIEmbeddings()
    
    def ensure_index_exists(self):
        """Ensure the Pinecone index exists, create if it doesn't"""
        try:
            if PINECONE_INDEX not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=PINECONE_INDEX,
                    dimension=PINECONE_DIMENSION,
                    metric=PINECONE_METRIC,
                    spec=ServerlessSpec(
                        cloud=PINECONE_CLOUD,
                        region=PINECONE_REGION
                    )
                )
            return self.pc.Index(PINECONE_INDEX)
        except Exception as e:
            raise Exception(f"Error with Pinecone index: {str(e)}")
    
    def check_index_has_data(self):
        """Check if the Pinecone index contains any records"""
        try:
            index = self.pc.Index(PINECONE_INDEX)
            stats = index.describe_index_stats()
            return stats.total_vector_count > 0
        except Exception as e:
            raise Exception(f"Error checking index data: {str(e)}")
    
    def get_available_files(self):
        """Get list of available files in the index"""
        try:
            index = self.pc.Index(PINECONE_INDEX)
            
            # Query the index with a dummy vector to get all documents
            # We'll use a zero vector since we just want the metadata
            dummy_vector = [0.0] * PINECONE_DIMENSION
            
            # Query with top_k set to a large number to get all documents
            # We'll use include_metadata=True to get the metadata
            response = index.query(
                vector=dummy_vector,
                top_k=10000,  # Large number to get all documents
                include_metadata=True
            )
            
            # Extract unique filenames from metadata
            files = set()
            if 'matches' in response:
                print("response['matches']", response['matches'])
                for match in response['matches']:
                    if 'metadata' in match and METADATA_FILENAME_KEY in match['metadata']:
                        files.add(match['metadata'][METADATA_FILENAME_KEY])
            
            return sorted(list(files))
        except Exception as e:
            raise Exception(f"Error getting available files: {str(e)}")
    
    def store_documents(self, documents):
        """Store documents in Pinecone"""
        try:
            vectorstore = PineconeVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings,
                index_name=PINECONE_INDEX,
                pinecone_api_key=PINECONE_API_KEY
            )
            return vectorstore
        except Exception as e:
            raise Exception(f"Failed to store embeddings: {str(e)}")
    
    def get_vectorstore(self, filename_filter=None):
        """Get existing vectorstore with optional filename filter"""
        try:
            vectorstore = PineconeVectorStore.from_existing_index(
                index_name=PINECONE_INDEX,
                embedding=self.embeddings
            )
            
            # If filename filter is provided, create a filtered retriever
            if filename_filter:
                # Create a custom retriever that filters by filename
                original_retriever = vectorstore.as_retriever()
                
                def filtered_retriever(query):
                    docs = original_retriever.get_relevant_documents(query)
                    # Filter documents by filename
                    filtered_docs = [
                        doc for doc in docs 
                        if doc.metadata.get(METADATA_FILENAME_KEY) == filename_filter
                    ]
                    return filtered_docs
                
                # Replace the retriever with filtered version
                vectorstore.retriever = type('FilteredRetriever', (), {
                    'get_relevant_documents': filtered_retriever
                })()
            
            return vectorstore
        except Exception as e:
            raise Exception(f"Error getting vectorstore: {str(e)}")
