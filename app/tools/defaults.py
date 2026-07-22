"""正式运行时启用的默认工具集合。"""

from app.tools.current_time import CurrentTimeTool
from app.tools.registry import ToolRegistry


def create_default_tool_registry() -> ToolRegistry:
    """创建新的 Registry，避免不同 ChatService 实例共享可变注册状态。"""
    return ToolRegistry(tools=[CurrentTimeTool()])
