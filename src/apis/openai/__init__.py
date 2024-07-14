import openai

import settings

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
APIConnectionError = openai.APIConnectionError

# expose module endpoints
from apis.openai.completions import get_completion, async_get_completion
from apis.openai.embeddings import Embedding, k_nearest
