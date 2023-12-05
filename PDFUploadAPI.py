from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceInstructEmbeddings
from dotenv import load_dotenv
#from langchain.vectorstores import FAISS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf'}

def get_vectorstore(text_chunks):
    embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    #embeddings = OpenAIEmbeddings() //chargeable ==> /1000 token = 0.004$
    #vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return embeddings

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

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        if pdf and allowed_file(pdf.filename):
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
            
    return text

@app.route('/upload/PDF_Files', methods=['POST'])
def upload_files():
    load_dotenv()
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400

    pdf_docs = request.files.getlist('files')

    # get pdf text
    raw_text = get_pdf_text(pdf_docs)

    # get the text chunks
    text_chunks = get_text_chunks(raw_text)

    # create vector store - issue in free source
    #vectorstore = get_vectorstore(text_chunks)


    return jsonify(text_chunks), 200

if __name__ == '__main__':
    app.run(debug=True)
