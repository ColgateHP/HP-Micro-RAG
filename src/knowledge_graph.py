import json
import networkx as nx
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from . import config

def extract_graph_from_chunks(text_chunks: list[str]) -> nx.DiGraph:
    llm = ChatOpenAI(
        model=config.LLM_MODEL_NAME, temperature=0,
        api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL
    )
    prompt = PromptTemplate.from_template(config.GRAPH_EXTRACTION_PROMPT)
    chain = prompt | llm
    graph = nx.DiGraph()
    for chunk in text_chunks:
        try:
            response = chain.invoke({"text": chunk})
            data = json.loads(response.content)
            for node_data in data.get('nodes', []):
                graph.add_node(node_data['id'], **node_data.get('properties', {}))
            for edge_data in data.get('edges', []):
                graph.add_edge(edge_data['source'], edge_data['target'], label=edge_data['label'])
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"[WARNING] Could not parse LLM output for graph extraction: {e}")
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred during graph extraction: {e}")
    return graph
