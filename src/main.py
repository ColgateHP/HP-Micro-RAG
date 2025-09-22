import os, re, argparse
from datetime import datetime
from googleapiclient.http import MediaFileUpload
from .document_loader import load_documents_from_txt, get_gdrive_service
from .knowledge_graph import extract_graph_from_chunks
from .rag_pipeline import create_rag_pipeline
from .markdown_generator import generate_markdown


INPUT_FILE_PATH = "source_documents.txt"
OUTPUT_FOLDER_URL = "https://drive.google.com/drive/folders/1HgLq4YfqOINtfzaFCy-bP44skJB0AXFs"

def get_folder_id_from_url(url: str) -> str:
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', url)
    if match: return match.group(1)
    raise ValueError(f"无法从文件夹URL中提取ID: {url}")

def upload_to_drive(file_content: str, folder_id: str, topic: str):
    service = get_gdrive_service()
    file_name = f"{topic.replace(' ', '_')}_知识图谱_{datetime.now().strftime('%Y%m%d')}.md"
    with open(file_name, "w", encoding="utf-8") as f: f.write(file_content)
    media = MediaFileUpload(file_name, mimetype='text/markdown', resumable=True)
    file_metadata = {'name': file_name, 'parents': [folder_id]}
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"[SUCCESS] File '{file_name}' with ID: {file.get('id')} uploaded to Google Drive.")
    os.remove(file_name)

def main():
    parser = argparse.ArgumentParser(description="Advanced RAG Knowledge Graph Builder from a URL list.")
    parser.add_argument("--topic", required=True, help="知识图谱的主题。")
    args = parser.parse_args()
    
    try:
        output_folder_id = get_folder_id_from_url(OUTPUT_FOLDER_URL)
    except ValueError as e:
        print(f"[ERROR] {e}")
        return

    print("--- [START] Advanced RAG Knowledge Graph Workflow ---")
    
    print(f"\n[Step 1/5] Loading documents from '{INPUT_FILE_PATH}'...")
    documents = load_documents_from_txt(INPUT_FILE_PATH)
    if not documents:
        print("[ERROR] No documents loaded. Aborting workflow.")
        return

    print("\n[Step 2/5] Creating RAG pipeline (chunking text and building FAISS vector store)...")
    retriever, summary_chain = create_rag_pipeline(documents)
    
    print("\n[Step 3/5] Extracting knowledge graph using LLM...")
    all_content = [doc.page_content for doc in documents]
    graph = extract_graph_from_chunks(all_content)
    print(f"[INFO] Extracted a graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")

    print("\n[Step 4/5] Generating final Markdown report with GraphRAG...")
    markdown_content = generate_markdown(graph, retriever, summary_chain, args.topic)

    print(f"\n[Step 5/5] Uploading Markdown to GDrive folder ID: {output_folder_id}")
    upload_to_drive(markdown_content, output_folder_id, args.topic)
    
    print("\n--- [COMPLETE] Workflow Finished Successfully ---")

if __name__ == "__main__":
    main()
