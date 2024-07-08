import os

# This is the flag that determines whether we are in production
DEBUG = False

if DEBUG:
    # use local secrets for development
    from _env_secrets import FLASK_SECRET_KEY, OPENAI_API_KEY
else:
    # pull secrets from production environment
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

SESSION_MESSAGES_KEY = "sambot-messages"
LOCAL_MESSAGES_DIR = "../data/messages" if DEBUG else "data/messages"
LOCAL_RESOURCE_DIR = "../res" if DEBUG else "res"
LOG_LEVEL = "INFO" if not DEBUG else "DEBUG"
