from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from src import config

def create_rag_pipeline(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    print(f"[INFO] Split {len(documents)} documents into {len(chunks)} chunks.")

    embeddings = OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL_NAME, api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL
    )
    vector_store = FAISS.from_documents(chunks, embeddings)
    print("[INFO] Created FAISS vector store.")

    llm = ChatOpenAI(
        model=config.LLM_MODEL_NAME, temperature=0,
        api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL
    )
    prompt = PromptTemplate.from_template(config.SUMMARY_PROMPT)
    summary_chain = prompt | llm
    return vector_store.as_retriever(), summary_chain

def get_entity_summary(entity: str, retriever, summary_chain):
    try:
        context_docs = retriever.get_relevant_documents(entity)
        context = "\n---\n".join([doc.page_content for doc in context_docs])
        response = summary_chain.invoke({"entity": entity, "context": context})
        return response.content
    except Exception as e:
        print(f"[ERROR] Failed to generate summary for entity '{entity}': {e}")
        return "无法生成摘要。"
