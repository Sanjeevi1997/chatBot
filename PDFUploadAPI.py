from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceInstructEmbeddings
from dotenv import load_dotenv
#from langchain.vectorstores import FAISS
import os
import pymongo
from werkzeug.utils import secure_filename

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf'}

client = pymongo.MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.1.1")

db = client.get_database("ChatBot")

collection = db["ChunkData"]

def get_vectorstore(text_chunks):
    embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    #embeddings = OpenAIEmbeddings() //chargeable ==> /1000 token = 0.004$
    #vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return embeddings

def upload_chunk_data(pdf_name,text_chunk):
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
        upload_chunk_data(pdf_fileName,text_chunks)
        #vectorstore = get_vectorstore(text_chunks)

    client.close()
    return jsonify("All PDF files are uploaded successfully"), 200

if __name__ == '__main__':
    app.run(debug=True)
