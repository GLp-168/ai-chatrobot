"""项目内置的 Prompt 模板。

把默认 Prompt 放在独立模块中，可以让它像代码一样被审查、测试和版本管理。
生产环境仍然可以通过环境变量覆盖它，而不需要修改源码。

当前 GLM OpenAI 兼容端在启用 tools 时无法正确处理非 ASCII System Prompt，
因此默认模板使用英文；它明确要求模型跟随用户语言，不影响中文回答。
"""


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI assistant. Reply in the user's language. "
    "Use available tools for relevant factual information."
)
