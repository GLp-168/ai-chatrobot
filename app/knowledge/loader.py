"""从受控目录加载本地知识文档。"""

from pathlib import Path

from app.knowledge.models import Document


class DocumentLoader:
    """只读取知识根目录内的 Markdown 和纯文本文件。

    文件路径来自服务端配置而不是模型参数。对每个候选文件再次执行 resolve 和
    relative_to 校验，可以阻止符号链接把读取范围带到知识目录之外。
    """

    SUPPORTED_SUFFIXES = frozenset({".md", ".txt"})

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def load(self) -> list[Document]:
        """按来源路径稳定排序并加载所有非空知识文档。"""
        if not self._root.is_dir():
            raise FileNotFoundError(f"知识库目录不存在: {self._root}")

        documents: list[Document] = []
        for candidate in sorted(self._root.rglob("*")):
            if candidate.suffix.lower() not in self.SUPPORTED_SUFFIXES:
                continue

            resolved = candidate.resolve()
            try:
                relative_path = resolved.relative_to(self._root)
            except ValueError:
                # 跳过指向知识目录之外的符号链接。
                continue

            if not resolved.is_file():
                continue

            content = resolved.read_text(encoding="utf-8-sig").strip()
            if not content:
                continue

            documents.append(
                Document(
                    source=relative_path.as_posix(),
                    content=content,
                )
            )

        return documents
