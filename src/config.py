import os

# --- LLM and Embeddings Configuration ---
# 从环境变量中获取，确保代码的灵活性和安全性
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") # 适配私有化部署
LLM_MODEL_NAME = "gpt-4-turbo"
EMBEDDING_MODEL_NAME = "text-embedding-3-small"

# --- Text Processing Configuration ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# --- Prompt Templates ---
GRAPH_EXTRACTION_PROMPT = """
你是一个精通分析牙膏制造行业微生物SOP文档的AI专家。请从下面的文本中提取知识图谱信息。
你需要识别出核心的实体（如操作规程、记录表、培养基、设备、特定操作等），以及它们之间的关系。
请以严格的JSON格式输出，包含一个"nodes"列表和一个"edges"列表。
- 每个"node"对象应包含"id"（实体名称）和"properties"（一个描述该实体的键值对对象）。
- 每个"edge"对象应包含"source"（源节点id），"target"（目标节点id），以及"label"（描述关系的动词短语）。

示例如下：
{{
  "nodes": [
    {{"id": "QA-MICRO-TIB-009", "properties": {{"type": "操作指引", "version": "1.0"}}}},
    {{"id": "TAT培养基", "properties": {{"code": "K", "type": "BD培养基"}}}}
  ],
  "edges": [
    {{"source": "QA-MICRO-TIB-009", "target": "TAT培养基", "label": "定义了配制方法"}}
  ]
}}

文本内容:
---
{text}
---
"""

SUMMARY_PROMPT = """
你是一个专业的文档摘要AI。请根据以下提供的上下文信息，为实体“{entity}”生成一段简洁、精确的描述性摘要。
摘要应重点突出该实体的关键属性、功能或与其他实体的关联。请直接输出摘要内容，不要添加任何多余的解释。

上下文信息:
---
{context}
---
"""
