"""
Global application config.
"""

DATABASE_FILEPATH = '.database.db'
CREATE_TABLES_SCRIPT = 'create_tables.sql'
DROP_TABLES_SCRIPT = 'drop_tables.sql'

MEMORIES_FILEPATH = 'sam-bot-memories.md'
PERSONALITY_FILEPATH = 'sam-bot-personality.md'

from env_secrets import OPENAI_API_KEY