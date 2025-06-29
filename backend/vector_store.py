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
    
    def check_index_has_data(self, username=None):
        """Check if the Pinecone index contains any records for the user"""
        try:
            index = self.pc.Index(PINECONE_INDEX)
            stats = index.describe_index_stats()
            
            if username:
                # Check if user has any documents
                dummy_vector = [0.0] * PINECONE_DIMENSION
                response = index.query(
                    vector=dummy_vector,
                    top_k=10000,
                    include_metadata=True,
                    filter={METADATA_USERNAME_KEY: {"$eq": username}}
                )
                return len(response.get('matches', [])) > 0
            else:
                return stats.total_vector_count > 0
        except Exception as e:
            raise Exception(f"Error checking index data: {str(e)}")
    
    def get_available_files(self):
        """Get list of available files in the index"""
        try:
            # Check if we have cached results
            if hasattr(self, '_cached_files') and self._cached_files is not None:
                return self._cached_files
            
            index = self.pc.Index(PINECONE_INDEX)
            
            # Query the index with a dummy vector to get all documents
            dummy_vector = [0.0] * PINECONE_DIMENSION
            
            response = index.query(
                vector=dummy_vector,
                top_k=10000,
                include_metadata=True
            )
            
            # Extract unique filenames from metadata
            files = set()
            if 'matches' in response:
                for match in response['matches']:
                    if 'metadata' in match and METADATA_FILENAME_KEY in match['metadata']:
                        files.add(match['metadata'][METADATA_FILENAME_KEY])
            
            file_list = sorted(list(files))
            
            # Cache the result
            self._cached_files = file_list
            
            return file_list
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
    
    def get_vectorstore(self, filename_filter=None, username=None):
        """Get existing vectorstore with optional filename and username filters"""
        try:
            vectorstore = PineconeVectorStore.from_existing_index(
                index_name=PINECONE_INDEX,
                embedding=self.embeddings
            )
            
            # Create a custom retriever that filters by filename and username
            original_retriever = vectorstore.as_retriever()
            
            def filtered_retriever(query):
                docs = original_retriever.get_relevant_documents(query)
                # Filter documents by filename and username
                filtered_docs = []
                for doc in docs:
                    include_doc = True
                    
                    if filename_filter and doc.metadata.get(METADATA_FILENAME_KEY) != filename_filter:
                        include_doc = False
                    
                    if username and doc.metadata.get(METADATA_USERNAME_KEY) != username:
                        include_doc = False
                    
                    if include_doc:
                        filtered_docs.append(doc)
                
                return filtered_docs
            
            # Replace the retriever with filtered version
            vectorstore.retriever = type('FilteredRetriever', (), {
                'get_relevant_documents': filtered_retriever
            })()
            
            return vectorstore
        except Exception as e:
            raise Exception(f"Error getting vectorstore: {str(e)}")

    def clear_cache(self):
        """Clear the cached file list"""
        self._cached_files = None
