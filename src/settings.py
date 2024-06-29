from _env_secrets import FLASK_SECRET_KEY, OPENAI_API_KEY

DEBUG = True

SESSION_MESSAGES_KEY = "sambot-messages"
LOCAL_MESSAGES_DIR = "../data/messages"
LOG_LEVEL = "INFO" if not DEBUG else "DEBUG"
