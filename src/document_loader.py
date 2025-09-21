import os
import io
import json
import fitz  # PyMuPDF
from docx import Document
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from langchain.docstore.document import Document as LangchainDocument

def get_gdrive_service():
    """初始化并返回Google Drive API服务实例。"""
    creds_json = os.getenv('GCP_SA_KEY', '{}')
    creds_info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

def load_documents_from_gdrive(folder_id: str) -> list[LangchainDocument]:
    """从指定的Google Drive文件夹下载并解析文档，返回Langchain Document对象列表。"""
    service = get_gdrive_service()
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])
    
    docs = []
    if not items:
        print(f"[WARNING] No files found in Google Drive folder: {folder_id}")
        return docs

    for item in items:
        file_id, file_name, mime_type = item['id'], item['name'], item['mimeType']
        print(f"[INFO] Processing file: {file_name}")
        
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        
        content = ""
        try:
            if 'pdf' in mime_type:
                with fitz.open(stream=fh, filetype="pdf") as pdf_doc:
                    content = "".join(page.get_text() for page in pdf_doc)
            elif 'wordprocessingml.document' in mime_type:
                doc = Document(fh)
                content = "\n".join(para.text for para in doc.paragraphs)

            if content:
                docs.append(LangchainDocument(page_content=content, metadata={"source": file_name}))
        except Exception as e:
            print(f"[ERROR] Failed to process {file_name}: {e}")
            
    return docs
