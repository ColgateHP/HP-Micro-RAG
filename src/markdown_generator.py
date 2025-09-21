from .rag_pipeline import get_entity_summary

def generate_markdown(graph, retriever, summary_chain, topic: str) -> str:
    """生成包含GraphRAG结果的Markdown文件内容。"""
    title = f"{topic}知识图谱"
    md = f"# {title}\n\n"
    md += "本文档通过AI自动构建，结合了知识图谱结构化信息与向量检索的深度内容摘要。\n\n"

    # 使用Set确保每个节点只处理一次
    processed_nodes = set()

    for node in graph.nodes():
        if node in processed_nodes:
            continue
        
        md += f"## 实体: {node}\n\n"
        
        # 1. 生成实体摘要 (RAG)
        summary = get_entity_summary(node, retriever, summary_chain)
        md += f"**摘要**:\n{summary}\n\n"

        # 2. 列出实体属性
        properties = graph.nodes[node]
        if properties:
            md += "**属性**:\n"
            for key, value in properties.items():
                md += f"- `{key}`: {value}\n"
            md += "\n"

        # 3. 列出关系
        md += "**关系**:\n"
        has_relations = False
        # 出向关系
        for _, target, data in graph.out_edges(node, data=True):
            md += f"- **{data.get('label', '关联到')}** -> `{target}`\n"
            has_relations = True
        # 入向关系
        for source, _, data in graph.in_edges(node, data=True):
            md += f"- **{data.get('label', '被...关联')}** <- `{source}`\n"
            has_relations = True
        
        if not has_relations:
            md += "- *该实体没有明确的直接关系。*\n"

        md += "\n---\n\n"
        processed_nodes.add(node)
        
    return md
