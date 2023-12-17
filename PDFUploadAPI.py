from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain.vectorstores import FAISS
import pymongo
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf'}

MONGODB_URL = os.getenv("MONGODB_URL")
client = pymongo.MongoClient(MONGODB_URL)

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def upload_data(raw_text):
  database = client.get_database("ChatBot")
  collection = database["JunkData"]
  filter_data = {
    "Action": "Upload"
  }
  upload_data = { "$set": {
    "Action": "Upload",
    "JunkData": raw_text
    }}
  dbResponse = collection.update_one(filter_data, upload_data)
  print("Inserted document with ID: {dbResponse.inserted_id}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_pdf_raw_text(pdf_docs):
    text = ""
    for pdf_doc in pdf_docs:
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
    raw_text = get_pdf_raw_text(pdf_docs)
    upload_data(raw_text)

    client.close  

    return jsonify("PDF files Upload successfully"), 200

if __name__ == '__main__':
    app.run(debug=True)
