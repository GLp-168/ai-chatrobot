from dotenv import load_dotenv
import os

load_dotenv(override=True)

class Settings:
    """
    项目配置
    """

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    MODEL_NAME = os.getenv("MODEL_NAME")


