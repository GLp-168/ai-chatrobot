"""让模型按需检索本地知识库的工具。"""

from typing import Any

from app.knowledge.retriever import BM25Retriever
from app.schemas.tool import ToolDefinition


class KnowledgeSearchTool:
    """将受控 BM25 Retriever 暴露为模型可调用工具。"""

    name = "search_knowledge_base"

    def __init__(
        self,
        retriever: BM25Retriever,
        default_top_k: int = 3,
        max_top_k: int = 5,
        max_query_characters: int = 500,
    ) -> None:
        if default_top_k < 1:
            raise ValueError("default_top_k 必须大于 0")
        if max_top_k < default_top_k:
            raise ValueError("max_top_k 必须大于等于 default_top_k")
        if max_query_characters < 1:
            raise ValueError("max_query_characters 必须大于 0")

        self._retriever = retriever
        self._default_top_k = default_top_k
        self._max_top_k = max_top_k
        self._max_query_characters = max_query_characters

    @property
    def definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "Search project-specific knowledge. Use it for questions about "
                    "the project, internal decisions, or private documentation. "
                    "Cite returned source and chunk_id in the final answer."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "A focused natural-language search query.",
                            "maxLength": self._max_query_characters,
                        },
                        "top_k": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": self._max_top_k,
                            "default": self._default_top_k,
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        }

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """校验模型参数并返回带可追溯来源的相关切片。"""
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query 必须是非空字符串")
        if len(query) > self._max_query_characters:
            raise ValueError(
                f"query 不能超过 {self._max_query_characters} 个字符"
            )

        top_k = arguments.get("top_k", self._default_top_k)
        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise ValueError("top_k 必须是整数")
        if top_k < 1 or top_k > self._max_top_k:
            raise ValueError(f"top_k 必须在 1 到 {self._max_top_k} 之间")

        clean_query = query.strip()
        results = self._retriever.search(clean_query, top_k=top_k)
        matches = [
            {
                "source": result.chunk.source,
                "chunk_id": result.chunk.id,
                "score": round(result.score, 4),
                "content": result.chunk.content,
            }
            for result in results
        ]

        return {
            "query": clean_query,
            "matches": matches,
            "message": (
                "请仅基于匹配内容回答，不要添加资料未说明的事实，"
                "并引用 source 和 chunk_id。"
                if matches
                else "知识库中没有找到相关内容，请明确告知用户。"
            ),
        }
