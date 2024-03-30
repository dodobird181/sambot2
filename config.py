"""
Global application config.
"""

import logging

# TODO: Delete old config vars
CONVO_ID_SESSION_KEY = "sambot_convo_id"
TEMPLATES_FILEPATH = "templates"

PICKLE_DB_PATH = ".pkldb/"
CHAT_SESSION_KEY = "sambot-chat-session"
LOGGING_LEVEL = logging.INFO

# import secret keys
from env_secrets import *
