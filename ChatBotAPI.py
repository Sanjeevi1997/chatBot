import streamlit as st
from dotenv import load_dotenv
from htmlTemplates import css, bot_template
from dotenv import load_dotenv
from llama_index import VectorStoreIndex, StorageContext, SimpleDirectoryReader
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
from llama_index.storage.storage_context import StorageContext
import pymongo
import os
from werkzeug.utils import secure_filename

MONGODB_URL = os.getenv("MONGODB_URL")
client = pymongo.MongoClient(MONGODB_URL)

def handle_userinput(user_question):
    message = st.session_state.conversation.query(user_question)
    st.write(bot_template.replace(
        "{{MSG}}", message.response), unsafe_allow_html=True)
    
def get_raw_text():
   database = client.get_database("ChatBot")
   collection = database["JunkData"]
   find_data = {
    "Action": "Upload"
   }
   result = collection.find_one(find_data)
   return result.get('JunkData')

def main():
    load_dotenv()
    st.set_page_config(page_title="Accenture chatBot",
                       page_icon=":question:")
    st.write(css, unsafe_allow_html=True)
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    
    if client and st.session_state.conversation == None:
        print("Connection Succesfully")
        store = MongoDBAtlasVectorSearch(client)
        storage_context = StorageContext.from_defaults(
        vector_store=store
        )
        raw_text = get_raw_text()
        file_path = "./File_Upload/Content.txt"
        with open(file_path, 'w', encoding='utf-8', errors='ignore') as file:
            file.write(raw_text)
            print("Upload the file in local location")
        documents = SimpleDirectoryReader("./File_Upload").load_data()
        database = client.get_database("default_db")
        collection = database["default_collection"]
        collection.delete_many({})
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        st.session_state.conversation = index.as_query_engine()
        print("Embedding created")
    
    
    st.header("Chat with Accenture :gem:")
    user_question = st.text_input("Ask questions :male-detective:")
    if user_question:
        handle_userinput(user_question)

if __name__ == '__main__':
    main()