import openai

from src import settings

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

# expose module endpoints
from apis.openai.completions import get_completion
from apis.openai.embeddings import get_embedding
from apis.openai.utils import *
