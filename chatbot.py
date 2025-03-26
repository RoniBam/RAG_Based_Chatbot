import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings.spacy_embeddings import SpacyEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent

import os

os.environ["KPM_DUPLICATE_LIB_OK"] = "TRUE"

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")


def read_pdf(pdf_doc):
    text = ""
    for pdf in pdf_doc:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    return chunks


#to do - change the vector to cloud DB so it will not be stored locally
embeddings = SpacyEmbeddings(model_name="en_core_web_sm")


def vector_store(text_chunks):
    vector_store1 = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store1.save_local("faiss_db")


def get_conversational_chain(tools, ques):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, api_key=api_key)
    prompt = ChatPromptTemplate.from_messages([
        ("system",
        """You are a helpful assistant. Answer the question as defatild as possible from the provided context, make sure to provide all the details
        , if the answer is not in the provided context just say "answer is not available", don't provide the wrong answer""",
         ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    tool = [tools]
    agent = create_tool_calling_agent(llm, tool, prompt)
    agent_executor = AgentExecutor(agent=agent,tools=tool,verbose=True)
    response = agent_executor.invoke({"input": ques})
    print(response)
    st.write("Reply: ", response['output'])


def user_input(user_question):
    new_db = FAISS.load_local("faiss_db",embeddings,allow_dangerous_deserialization=True)
    retriever = new_db.as_retriever()
    retrieval_chain = create_retriever_tool(retriever, "pdf_extractor", "This tool will give answers from a PDF uploaded by the user")
    get_conversational_chain(retrieval_chain,user_question)


def main():
    st.set_page_config("Chat PDF")
    st.header("RAG based Chat with PDF")
    user_question = st.text_input("Ask a Question from the PDF files")
    if user_question:
        user_input(user_question)
    with st.sidebar:
        pdf_doc = st.file_uploader("Upload your PDF files and click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & process"):
            with st.spinner("Processing..."):
                raw_text = read_pdf(pdf_doc)
                text_chunks = get_chunks(raw_text)
                vector_store(text_chunks)
                st.success("Done")

if __name__ == "__main__":
    main()




