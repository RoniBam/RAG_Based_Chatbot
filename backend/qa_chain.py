from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from .config import *

class QAChain:
    def __init__(self):
        self.chat_model = ChatOpenAI(temperature=TEMPERATURE)
    
    def create_qa_chain(self, vectorstore):
        """Create a question-answering chain"""
        return ConversationalRetrievalChain.from_llm(
            llm=self.chat_model,
            retriever=vectorstore.as_retriever(),
            return_source_documents=True
        )
