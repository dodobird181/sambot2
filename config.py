"""
Global application config.
"""

TEMPLATES_FILEPATH = "templates"
TEST_DATA_FILEPATH = "test_data/"
DATA_FILEPATH = "data/"
MEMORIES_FILEPATH = "sam-bot-memories.md"
PERSONALITY_FILEPATH = "sam-bot-personality.md"

from env_secrets import OPENAI_API_KEY, FLASK_SECRET_KEY
