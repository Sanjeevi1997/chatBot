from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain.vectorstores import FAISS
from llama_index import VectorStoreIndex, StorageContext, SimpleDirectoryReader
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
from llama_index.storage.storage_context import StorageContext
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
import os
import pymongo
from werkzeug.utils import secure_filename

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf'}

client = pymongo.MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.1.1")

#msanjeeviraman97
#KaqTpAvO40QR0Lzj

db = client.get_database("ChatBot")

collection = db["ChunkData"]

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def upload_chunk_data(pdf_name,pdf_doc):
  upload_data = {
    "PDFFileName": pdf_name,
    "JunkData": text_chunk
  }
  result = collection.insert_one(upload_data)
  print("Inserted document with ID: {result.inserted_id}")
  

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_pdf_raw_text(pdf_doc):
    text = ""
    pdf_reader = PdfReader(pdf_doc)
    for page in pdf_reader.pages:
      text += page.extract_text()
    return text

@app.route('/upload/PDF_Files', methods=['POST'])
def upload_files():
    load_dotenv()
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400

    pdf_docs = request.files.getlist('files')

    for pdf_doc in pdf_docs:
      if pdf_doc and allowed_file(pdf_doc.filename):
        pdf_fileName = os.path.splitext(pdf_doc.filename)[0]
        raw_text = get_pdf_raw_text(pdf_doc)
        text_chunks = get_text_chunks(raw_text)
        upload_chunk_data(pdf_fileName,pdf_doc)
        # vectorstore = get_vectorstore(text_chunks)

    client.close()
    return jsonify(""), 200

if __name__ == '__main__':
    app.run(debug=True)
