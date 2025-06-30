from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from .config import *
import streamlit as st

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
                stats = index.describe_index_stats()
                return stats.total_vector_count > 0
        except Exception as e:
            raise Exception(f"Error checking index data: {str(e)}")
    
    def get_available_files(self, username=None):
        """Get list of available files in the index for a specific user"""
        try:
            index = self.pc.Index(PINECONE_INDEX)
            
            # Query the index with a dummy vector to get all documents
            dummy_vector = [0.0] * PINECONE_DIMENSION
            
            if username:
                # Filter by username
                response = index.query(
                    vector=dummy_vector,
                    top_k=10000,
                    include_metadata=True,
                    filter={METADATA_USERNAME_KEY: {"$eq": username}}
                )
            else:
                # Get all documents
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
            
            # Create a new retriever class with the filtered function
            class FilteredRetriever:
                def __init__(self, original_retriever, filter_func):
                    self.original_retriever = original_retriever
                    self.filter_func = filter_func
                
                def get_relevant_documents(self, query):
                    return self.filter_func(query)
            
            # Replace the retriever with filtered version
            vectorstore.retriever = FilteredRetriever(original_retriever, filtered_retriever)
            
            return vectorstore
        except Exception as e:
            raise Exception(f"Error getting vectorstore: {str(e)}")
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            index = self.pc.Index(PINECONE_INDEX)
            stats = index.describe_index_stats()
            
            # Get user statistics by querying all documents
            user_stats = {}
            try:
                # Query all documents to get user distribution
                dummy_vector = [0.0] * PINECONE_DIMENSION
                response = index.query(
                    vector=dummy_vector,
                    top_k=10000,
                    include_metadata=True
                )
                
                if 'matches' in response:
                    for match in response['matches']:
                        if 'metadata' in match and METADATA_USERNAME_KEY in match['metadata']:
                            username = match['metadata'][METADATA_USERNAME_KEY]
                            if username not in user_stats:
                                user_stats[username] = 0
                            user_stats[username] += 1
            except Exception as e:
                st.warning(f"Could not retrieve user statistics: {str(e)}")
            
            return {
                'total_vectors': stats.total_vector_count,
                'total_dimension': stats.dimension,
                'index_fullness': stats.index_fullness,
                'user_stats': user_stats
            }
        except Exception as e:
            raise Exception(f"Error getting database stats: {str(e)}")
    
    def clear_database(self):
        """Clear all data from the Pinecone database"""
        try:
            index = self.pc.Index(PINECONE_INDEX)
            
            # First, let's check what's actually in the index
            print(f"Attempting to clear index: {PINECONE_INDEX}")
            
            # Get index stats before deletion
            stats_before = index.describe_index_stats()
            print(f"Vectors before deletion: {stats_before.total_vector_count}")
            
            if stats_before.total_vector_count == 0:
                print("No vectors to delete")
                return 0
            
            # Try the delete_all method first
            try:
                print("Attempting delete_all operation...")
                index.delete(delete_all=True)
                print("delete_all operation completed")
            except Exception as delete_error:
                print(f"delete_all failed: {delete_error}")
                
                # Fallback: delete by querying all vectors
                print("Falling back to manual deletion...")
                dummy_vector = [0.0] * PINECONE_DIMENSION
                
                # Query all vectors
                response = index.query(
                    vector=dummy_vector,
                    top_k=10000,
                    include_metadata=True
                )
                
                vector_ids = []
                if 'matches' in response:
                    for match in response['matches']:
                        if 'id' in match:
                            vector_ids.append(match['id'])
                
                print(f"Found {len(vector_ids)} vectors to delete")
                
                if vector_ids:
                    # Delete in batches of 1000
                    batch_size = 1000
                    for i in range(0, len(vector_ids), batch_size):
                        batch = vector_ids[i:i + batch_size]
                        print(f"Deleting batch {i//batch_size + 1}: {len(batch)} vectors")
                        index.delete(ids=batch)
            
            # Verify deletion
            stats_after = index.describe_index_stats()
            print(f"Vectors after deletion: {stats_after.total_vector_count}")
            
            return stats_before.total_vector_count - stats_after.total_vector_count
            
        except Exception as e:
            print(f"Error in clear_database: {e}")
            raise Exception(f"Error clearing database: {str(e)}")
    
    def delete_user_documents(self, username):
        """Delete all documents for a specific user"""
        try:
            index = self.pc.Index(PINECONE_INDEX)
            
            # Query to get all vectors for the user
            dummy_vector = [0.0] * PINECONE_DIMENSION
            response = index.query(
                vector=dummy_vector,
                top_k=10000,
                include_metadata=True,
                filter={METADATA_USERNAME_KEY: {"$eq": username}}
            )
            
            # Extract vector IDs to delete
            vector_ids = []
            if 'matches' in response:
                for match in response['matches']:
                    if 'id' in match:
                        vector_ids.append(match['id'])
            
            # Delete the vectors
            if vector_ids:
                index.delete(ids=vector_ids)
            
            return len(vector_ids)
        except Exception as e:
            raise Exception(f"Error deleting user documents: {str(e)}")

    def clear_cache(self):
        """Clear the cached file list"""
        self._cached_files = None
