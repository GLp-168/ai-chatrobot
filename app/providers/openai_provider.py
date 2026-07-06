from openai import OpenAI

from app.core.setting import Settings

class OpenAIProvider:
    """
    大模型 Provider
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Settings.OPENAI_API_KEY,
            base_url=Settings.OPENAI_BASE_URL,
        )

    def chat(self, message: str) -> str:
        
        response = self.client.chat.completions.create(
            model=Settings.MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
        )

        return response.choices[0].message.content
    
    