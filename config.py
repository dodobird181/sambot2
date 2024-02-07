"""
Global application config.
"""

CONVO_ID_SESSION_KEY = "sambot_convo_id"
TEMPLATES_FILEPATH = "templates"
TEST_DATA_FILEPATH = "test_data/"
DATA_FILEPATH = "data/"
MEMORIES_FILEPATH = "sam-bot-memories.md"
PERSONALITY_FILEPATH = "sam-bot-personality.md"

from env_secrets import FLASK_SECRET_KEY, OPENAI_API_KEY
