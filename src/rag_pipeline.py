from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from . import config

def create_rag_pipeline(documents):
    """创建并返回一个完整的RAG Pipeline，包含向量库和摘要链。"""
    # 1. 文本分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    print(f"[INFO] Split {len(documents)} documents into {len(chunks)} chunks.")

    # 2. 创建Embedding模型
    embeddings = OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL_NAME,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )

    # 3. 创建并填充FAISS向量库
    vector_store = FAISS.from_documents(chunks, embeddings)
    print("[INFO] Created FAISS vector store.")

    # 4. 创建摘要生成链
    llm = ChatOpenAI(
        model=config.LLM_MODEL_NAME,
        temperature=0,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )
    prompt = PromptTemplate.from_template(config.SUMMARY_PROMPT)
    summary_chain = prompt | llm

    return vector_store.as_retriever(), summary_chain

def get_entity_summary(entity: str, retriever, summary_chain):
    """为指定实体从向量库中检索信息并生成摘要。"""
    try:
        context_docs = retriever.get_relevant_documents(entity)
        context = "\n---\n".join([doc.page_content for doc in context_docs])
        
        response = summary_chain.invoke({"entity": entity, "context": context})
        return response.content
    except Exception as e:
        print(f"[ERROR] Failed to generate summary for entity '{entity}': {e}")
        return "无法生成摘要。"
