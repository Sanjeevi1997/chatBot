from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import pymongo
import os
from llama_index import StorageContext, load_index_from_storage
from werkzeug.utils import secure_filename

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf'}

MONGODB_URL = os.getenv("MONGODB_URL")
client = pymongo.MongoClient(MONGODB_URL)

def upload_data(raw_text):
  database = client.get_database("ChatBot")
  collection = database["JunkData"]
  filter_data = {
    "Action": "Upload"
  }
  
  existing_document = collection.find_one(filter_data)
  if existing_document:
    upload_data = { "$set": {
    "Action": "Upload",
    "JunkData": raw_text
    }}
    collection.update_one(filter_data, upload_data)
  else:
    insert_data = {
    "Action": "Upload",
    "JunkData": raw_text
    }
    collection.insert_one(insert_data)
  print("document uploaded in DB")

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
