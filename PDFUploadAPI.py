from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import pymongo
import os
from llama_index import VectorStoreIndex, StorageContext, SimpleDirectoryReader
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch

load_dotenv()

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf'}

MONGODB_URL = os.getenv("MONGODB_URL")
client = pymongo.MongoClient(MONGODB_URL)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_pdf_raw_text(pdf_docs):
    text = ""
    for pdf_doc in pdf_docs:
        pdf_reader = PdfReader(pdf_doc)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def vectorize_and_store(raw_text):
    file_path = "./File_Upload/Content.txt"
    with open(file_path, 'w', encoding='utf-8', errors='ignore') as file:
        file.write(raw_text)
    print("Written to local file")

    database = client.get_database("default_db")
    collection = database["default_collection"]
    collection.delete_many({})
    print("Cleared old vectors")

    store = MongoDBAtlasVectorSearch(client)
    storage_context = StorageContext.from_defaults(vector_store=store)
    documents = SimpleDirectoryReader("./File_Upload").load_data()
    VectorStoreIndex.from_documents(documents, storage_context=storage_context)
    print("Embeddings created and stored in MongoDB")

@app.route('/upload/PDF_Files', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400

    pdf_docs = request.files.getlist('files')

    invalid_files = [f.filename for f in pdf_docs if not allowed_file(f.filename)]
    if invalid_files:
        return jsonify({"error": f"Invalid file type(s): {invalid_files}. Only PDF files are allowed."}), 400

    raw_text = get_pdf_raw_text(pdf_docs)
    vectorize_and_store(raw_text)

    return jsonify("PDF files uploaded and vectorized successfully"), 200

if __name__ == '__main__':
    app.run(debug=True)
