"""
Global application config.
"""

import logging
import os

# TODO: Delete old config vars
CONVO_ID_SESSION_KEY = "sambot_convo_id"
TEMPLATES_FILEPATH = "templates"

PICKLE_DB_PATH = ".pkldb/"
CHAT_SESSION_KEY = "sambot-chat-session"
LOGGING_LEVEL = logging.INFO

FLASK_SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]