import os
import argparse
from datetime import datetime
from googleapiclient.http import MediaFileUpload
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .document_loader import load_documents_from_gdrive, get_gdrive_service
from .knowledge_graph import extract_graph_from_chunks
from .rag_pipeline import create_rag_pipeline
from .markdown_generator import generate_markdown
from . import config

def upload_to_drive(file_content: str, folder_id: str, topic: str):
    """将文件内容上传到指定的Google Drive文件夹。"""
    service = get_gdrive_service()
    file_name = f"{topic.replace(' ', '_')}_知识图谱_{datetime.now().strftime('%Y%m%d')}.md"
    
    # 将内容写入临时文件以便上传
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(file_content)
        
    file_metadata = {'name': file_name, 'parents': [folder_id]}
    media = MediaFileUpload(file_name, mimetype='text/markdown', resumable=True)
    
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"[SUCCESS] File '{file_name}' with ID: {file.get('id')} uploaded to Google Drive.")
    
    os.remove(file_name) # 清理临时文件

def main():
    parser = argparse.ArgumentParser(description="Advanced RAG Knowledge Graph Builder from Google Drive docs.")
    parser.add_argument("--topic", required=True, help="知识图谱的主题。")
    parser.add_argument("--input_folder", required=True, help="输入文档的Google Drive文件夹ID。")
    parser.add_argument("--output_folder", required=True, help="输出Markdown的Google Drive文件夹ID。")
    args = parser.parse_args()
    
    print("--- [START] Advanced RAG Knowledge Graph Workflow ---")
    
    # 1. 加载文档
    print(f"\n[Step 1/5] Loading documents from GDrive folder: {args.input_folder}")
    documents = load_documents_from_gdrive(args.input_folder)
    if not documents:
        print("[ERROR] No documents loaded. Aborting workflow.")
        return

    # 2. 创建RAG Pipeline (包含文本分块和向量库)
    print("\n[Step 2/5] Creating RAG pipeline (chunking text and building FAISS vector store)...")
    retriever, summary_chain = create_rag_pipeline(documents)
    
    # 3. 从文本中提取知识图谱
    print("\n[Step 3/5] Extracting knowledge graph using LLM...")
    all_chunks_text = [doc.page_content for doc in documents]
    graph = extract_graph_from_chunks(all_chunks_text)
    print(f"[INFO] Extracted a graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")

    # 4. 生成Markdown报告
    print("\n[Step 4/5] Generating final Markdown report with GraphRAG...")
    markdown_content = generate_markdown(graph, retriever, summary_chain, args.topic)

    # 5. 上传到Google Drive
    print(f"\n[Step 5/5] Uploading Markdown to GDrive folder: {args.output_folder}")
    upload_to_drive(markdown_content, args.output_folder, args.topic)
    
    print("\n--- [COMPLETE] Workflow Finished Successfully ---")

if __name__ == "__main__":
    main()
