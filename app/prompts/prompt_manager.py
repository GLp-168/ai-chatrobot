"""发送给大模型之前的 Prompt 组装逻辑。"""

from collections.abc import Sequence

from app.schemas.message import ChatMessage


class PromptManager:
    """将系统指令与最近的聊天历史组装为模型消息列表。

    Memory 保存的是用户与 AI 真正发生过的对话；System Prompt 属于应用行为配置，
    不应该写入 Memory。PromptManager 在每次模型调用前把两者组合起来。
    """

    def __init__(self, system_prompt: str, max_history_messages: int) -> None:
        cleaned_system_prompt = system_prompt.strip()
        if not cleaned_system_prompt:
            raise ValueError("system_prompt 不能为空")
        if max_history_messages < 1:
            raise ValueError("max_history_messages 必须大于 0")

        self._system_prompt = cleaned_system_prompt
        self._max_history_messages = max_history_messages

    def build_messages(self, history: Sequence[ChatMessage]) -> list[ChatMessage]:
        """构建 Provider 可以直接发送给模型的完整消息列表。

        构建过程不会修改传入的历史记录。即使调用方意外传入 system 消息，
        这里也会丢弃它，并使用当前应用配置的唯一 System Prompt，避免重复指令。
        """
        conversation = [
            message.copy()
            for message in history
            if message["role"] != "system"
        ]
        recent_history = conversation[-self._max_history_messages :]

        # 裁剪点可能正好落在 assistant 回复上。去掉开头孤立的回复，保证发送给
        # 模型的历史从用户消息开始，避免模型看到一条没有问题来源的回答。
        while recent_history and recent_history[0]["role"] == "assistant":
            recent_history.pop(0)

        system_message: ChatMessage = {
            "role": "system",
            "content": self._system_prompt,
        }
        return [system_message, *recent_history]
