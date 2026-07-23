"""正式运行时启用的默认工具集合。"""

from app.core.setting import Settings
from app.knowledge.factory import create_knowledge_retriever
from app.tools.current_time import CurrentTimeTool
from app.tools.knowledge_search import KnowledgeSearchTool
from app.tools.registry import ToolRegistry


def create_default_tool_registry() -> ToolRegistry:
    """创建新的 Registry，避免不同 ChatService 实例共享可变注册状态。"""
    knowledge_retriever = create_knowledge_retriever(
        knowledge_dir=Settings.KNOWLEDGE_DIR,
        chunk_size=Settings.KNOWLEDGE_CHUNK_SIZE,
        chunk_overlap=Settings.KNOWLEDGE_CHUNK_OVERLAP,
    )
    return ToolRegistry(
        tools=[
            CurrentTimeTool(),
            KnowledgeSearchTool(
                retriever=knowledge_retriever,
                default_top_k=Settings.KNOWLEDGE_TOP_K,
                max_top_k=Settings.KNOWLEDGE_MAX_TOP_K,
                max_query_characters=Settings.KNOWLEDGE_MAX_QUERY_CHARACTERS,
            ),
        ]
    )
