import os, io, re, json
from typing import List
import fitz  # PyMuPDF
from docx import Document
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from langchain.docstore.document import Document as LangchainDocument
from src.ocr_processor import get_text_from_image

def get_gdrive_service():
    creds_json = os.getenv('GCP_SA_KEY', '{}')
    creds_info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

def _get_id_from_url(url: str) -> str:
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match: return match.group(1)
    raise ValueError(f"无法从URL中提取ID: {url}")

def _download_and_parse_file(service, file_id: str, doc_name: str) -> LangchainDocument | None:
    try:
        file_metadata = service.files().get(fileId=file_id, fields='mimeType').execute()
        mime_type = file_metadata.get('mimeType')
        content = ""

        if 'pdf' in mime_type:
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done: _, done = downloader.next_chunk()
            fh.seek(0)
            
            with fitz.open(stream=fh, filetype="pdf") as pdf_doc:
                for page_num, page in enumerate(pdf_doc):
                    content += page.get_text()
                    images = page.get_images(full=True)
                    if images:
                        print(f"[INFO] Found {len(images)} image(s) on page {page_num + 1} of '{doc_name}' for OCR.")
                    for img in images:
                        xref = img[0]
                        base_image = pdf_doc.extract_image(xref)
                        content += get_text_from_image(base_image["image"])
        
        elif 'google-apps.document' in mime_type:
            export_request = service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, export_request)
            done = False
            while not done: _, done = downloader.next_chunk()
            fh.seek(0)
            doc = Document(fh)
            content = "\n".join(para.text for para in doc.paragraphs)

        if content:
            return LangchainDocument(page_content=content, metadata={"source": doc_name})
        print(f"[WARNING] 文件内容为空或不支持的格式: {doc_name}")
        return None
    except HttpError as e:
        print(f"[ERROR] 下载文件 {doc_name} (ID: {file_id}) 时发生HTTP错误: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 处理文件 {doc_name} 时发生未知错误: {e}")
        return None

def load_documents_from_txt(file_path: str) -> List[LangchainDocument]:
    if not os.path.exists(file_path):
        print(f"[ERROR] 输入文件未找到: {file_path}")
        return []
    service = get_gdrive_service()
    docs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if ':' not in line: continue
            doc_name, url = [part.strip() for part in line.split(':', 1)]
            try:
                print(f"[INFO] 开始处理文档: {doc_name}")
                file_id = _get_id_from_url(url)
                if doc := _download_and_parse_file(service, file_id, doc_name):
                    docs.append(doc)
            except ValueError as e:
                print(e)
    return docs
