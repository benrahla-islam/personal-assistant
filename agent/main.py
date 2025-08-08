from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.gemini import Gemini
import os
import dotenv

dotenv.load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")