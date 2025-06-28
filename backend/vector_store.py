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
    
    def get_vectorstore(self):
        """Get existing vectorstore"""
        try:
            return PineconeVectorStore.from_existing_index(
                index_name=PINECONE_INDEX,
                embedding=self.embeddings
            )
        except Exception as e:
            raise Exception(f"Error getting vectorstore: {str(e)}")
