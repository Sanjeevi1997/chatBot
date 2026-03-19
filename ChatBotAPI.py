import streamlit as st
from dotenv import load_dotenv
from htmlTemplates import css, bot_template
from llama_index import VectorStoreIndex
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
import pymongo
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
client = pymongo.MongoClient(MONGODB_URL)

def handle_userinput(user_question):
    message = st.session_state.conversation.query(user_question)
    st.session_state.chat_history.append({
        "question": user_question,
        "answer": message.response
    })

def main():
    st.set_page_config(page_title="Accenture chatBot",
                       page_icon=":question:")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if client and st.session_state.conversation is None:
        print("Connected to MongoDB")
        store = MongoDBAtlasVectorSearch(client)
        index = VectorStoreIndex.from_vector_store(vector_store=store)
        st.session_state.conversation = index.as_query_engine()
        print("Query engine ready")

    st.header("Chat with Accenture :gem:")
    user_question = st.text_input("Ask questions :male-detective:")
    if user_question:
        handle_userinput(user_question)

    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['question']}")
        st.write(bot_template.replace("{{MSG}}", chat["answer"]), unsafe_allow_html=True)

if __name__ == '__main__':
    main()
