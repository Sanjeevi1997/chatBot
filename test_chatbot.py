"""
Tests for ChatBot application:
  - PDFUploadAPI: allowed_file, get_pdf_raw_text, upload_data, /upload/PDF_Files endpoint
  - ChatBotAPI:   get_raw_text, handle_userinput
"""

import io
import pytest
from unittest.mock import MagicMock, patch, mock_open


# ---------------------------------------------------------------------------
# PDFUploadAPI tests
# ---------------------------------------------------------------------------

@pytest.fixture
def flask_app():
    """Create Flask test client with mocked MongoDB."""
    with patch("pymongo.MongoClient") as mock_client, \
         patch("os.getenv", return_value="mongodb://mock"):
        import importlib, sys
        # Remove cached module so the patch takes effect
        sys.modules.pop("PDFUploadAPI", None)
        import PDFUploadAPI as api
        api.client = mock_client.return_value
        api.app.config["TESTING"] = True
        yield api.app.test_client(), api


class TestAllowedFile:
    def test_pdf_allowed(self, flask_app):
        _, api = flask_app
        assert api.allowed_file("report.pdf") is True

    def test_pdf_uppercase_allowed(self, flask_app):
        _, api = flask_app
        assert api.allowed_file("report.PDF") is True

    def test_txt_not_allowed(self, flask_app):
        _, api = flask_app
        assert api.allowed_file("notes.txt") is False

    def test_no_extension(self, flask_app):
        _, api = flask_app
        assert api.allowed_file("nodotfile") is False

    def test_empty_filename(self, flask_app):
        _, api = flask_app
        assert api.allowed_file("") is False


class TestGetPdfRawText:
    def test_extracts_text_from_single_page(self, flask_app):
        _, api = flask_app
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Hello World"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("PDFUploadAPI.PdfReader", return_value=mock_reader):
            result = api.get_pdf_raw_text([io.BytesIO(b"%PDF-fake")])

        assert result == "Hello World"

    def test_concatenates_multiple_pages(self, flask_app):
        _, api = flask_app
        page1 = MagicMock()
        page1.extract_text.return_value = "Page1 "
        page2 = MagicMock()
        page2.extract_text.return_value = "Page2"

        mock_reader = MagicMock()
        mock_reader.pages = [page1, page2]

        with patch("PDFUploadAPI.PdfReader", return_value=mock_reader):
            result = api.get_pdf_raw_text([io.BytesIO(b"%PDF-fake")])

        assert result == "Page1 Page2"

    def test_multiple_pdf_files(self, flask_app):
        _, api = flask_app
        page_a = MagicMock()
        page_a.extract_text.return_value = "FileA"
        page_b = MagicMock()
        page_b.extract_text.return_value = "FileB"

        reader_a = MagicMock()
        reader_a.pages = [page_a]
        reader_b = MagicMock()
        reader_b.pages = [page_b]

        with patch("PDFUploadAPI.PdfReader", side_effect=[reader_a, reader_b]):
            result = api.get_pdf_raw_text(
                [io.BytesIO(b"a"), io.BytesIO(b"b")]
            )

        assert result == "FileAFileB"

    def test_empty_page_text(self, flask_app):
        _, api = flask_app
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("PDFUploadAPI.PdfReader", return_value=mock_reader):
            result = api.get_pdf_raw_text([io.BytesIO(b"%PDF")])

        assert result == ""


class TestUploadData:
    def test_inserts_when_no_existing_document(self, flask_app):
        _, api = flask_app
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        api.client.get_database.return_value.get_collection = MagicMock()
        api.client.get_database.return_value.__getitem__ = MagicMock(
            return_value=mock_collection
        )

        api.upload_data("some text")

        mock_collection.insert_one.assert_called_once_with(
            {"Action": "Upload", "JunkData": "some text"}
        )
        mock_collection.update_one.assert_not_called()

    def test_updates_when_existing_document(self, flask_app):
        _, api = flask_app
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = {"Action": "Upload", "JunkData": "old"}
        api.client.get_database.return_value.__getitem__ = MagicMock(
            return_value=mock_collection
        )

        api.upload_data("new text")

        mock_collection.update_one.assert_called_once_with(
            {"Action": "Upload"},
            {"$set": {"Action": "Upload", "JunkData": "new text"}},
        )
        mock_collection.insert_one.assert_not_called()


class TestUploadEndpoint:
    def test_returns_400_when_no_files_key(self, flask_app):
        client, _ = flask_app
        response = client.post("/upload/PDF_Files")
        assert response.status_code == 400
        assert b"No files provided" in response.data

    def test_successful_upload(self, flask_app):
        client, api = flask_app
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample PDF content"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        api.client.get_database.return_value.__getitem__ = MagicMock(
            return_value=mock_collection
        )

        with patch("PDFUploadAPI.PdfReader", return_value=mock_reader), \
             patch("PDFUploadAPI.load_dotenv"):
            data = {"files": (io.BytesIO(b"%PDF-1.4"), "test.pdf")}
            response = client.post(
                "/upload/PDF_Files",
                data=data,
                content_type="multipart/form-data",
            )

        assert response.status_code == 200
        assert b"successfully" in response.data.lower()

    def test_upload_multiple_files(self, flask_app):
        client, api = flask_app
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        api.client.get_database.return_value.__getitem__ = MagicMock(
            return_value=mock_collection
        )

        with patch("PDFUploadAPI.PdfReader", return_value=mock_reader), \
             patch("PDFUploadAPI.load_dotenv"):
            data = {
                "files": [
                    (io.BytesIO(b"%PDF-1"), "a.pdf"),
                    (io.BytesIO(b"%PDF-2"), "b.pdf"),
                ]
            }
            response = client.post(
                "/upload/PDF_Files",
                data=data,
                content_type="multipart/form-data",
            )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# ChatBotAPI tests
# ---------------------------------------------------------------------------

@pytest.fixture
def chatbot_api():
    """Import ChatBotAPI with mocked heavy dependencies."""
    import sys

    # Stub out modules that aren't installed in the test env
    for mod in [
        "streamlit", "llama_index", "llama_index.vector_stores.mongodb",
        "llama_index.storage.storage_context",
    ]:
        sys.modules.setdefault(mod, MagicMock())

    with patch("pymongo.MongoClient") as mock_mc, \
         patch("os.getenv", return_value="mongodb://mock"), \
         patch("dotenv.load_dotenv"):
        sys.modules.pop("ChatBotAPI", None)
        import ChatBotAPI as cb
        cb.client = mock_mc.return_value
        yield cb


class TestGetRawText:
    def test_returns_junk_data_field(self, chatbot_api):
        cb = chatbot_api
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = {"Action": "Upload", "JunkData": "raw content"}
        cb.client.get_database.return_value.__getitem__ = MagicMock(
            return_value=mock_collection
        )

        result = cb.get_raw_text()

        assert result == "raw content"
        mock_collection.find_one.assert_called_once_with({"Action": "Upload"})

    def test_returns_none_when_field_missing(self, chatbot_api):
        cb = chatbot_api
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = {"Action": "Upload"}
        cb.client.get_database.return_value.__getitem__ = MagicMock(
            return_value=mock_collection
        )

        result = cb.get_raw_text()

        assert result is None

    def test_uses_correct_database_and_collection(self, chatbot_api):
        cb = chatbot_api
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = {"JunkData": "data"}
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        cb.client.get_database.return_value = mock_db

        cb.get_raw_text()

        cb.client.get_database.assert_called_with("ChatBot")
        mock_db.__getitem__.assert_called_with("JunkData")


class TestHandleUserInput:
    def test_writes_bot_response_to_streamlit(self, chatbot_api):
        cb = chatbot_api
        import streamlit as st

        mock_engine = MagicMock()
        mock_engine.query.return_value.response = "Bot answer"
        st.session_state = MagicMock()
        st.session_state.conversation = mock_engine

        cb.handle_userinput("What is AI?")

        mock_engine.query.assert_called_once_with("What is AI?")
        st.write.assert_called_once()
        written_html = st.write.call_args[0][0]
        assert "Bot answer" in written_html

    def test_empty_question_still_queries(self, chatbot_api):
        cb = chatbot_api
        import streamlit as st

        mock_engine = MagicMock()
        mock_engine.query.return_value.response = ""
        st.session_state = MagicMock()
        st.session_state.conversation = mock_engine

        cb.handle_userinput("")

        mock_engine.query.assert_called_once_with("")
