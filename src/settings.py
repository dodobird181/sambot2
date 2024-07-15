import os

class ConfigurationError(Exception):
    """The application is misconfigured."""
    ...

LOG_LEVEL = 'DEBUG'
IS_DEVELOPMENT = False
USE_DUMMY_SYSTEM_MESSAGE = False
USE_DUMMY_OPENAI_RESPONSE = False

IS_PROD = (
    # production environment if all dummy flags are set to false, and the debug flag is set to false.
    # This way, if anything is set to a fake output, the system automatically assumes we are developing.
    not USE_DUMMY_SYSTEM_MESSAGE and
    not USE_DUMMY_OPENAI_RESPONSE and
    not IS_DEVELOPMENT
)

if IS_PROD:
    # pull secrets from production environment
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    if not FLASK_SECRET_KEY:
        raise ConfigurationError('FLASK_SECRET_KEY is required in production!')

    # don't log debug messages in prod
    LOG_LEVEL = 'INFO'

else:
    # use local secrets for development
    from _dev_secrets import FLASK_SECRET_KEY, OPENAI_API_KEY


SESSION_MESSAGES_KEY = "sambot-messages"
LOCAL_MESSAGES_DIR = "data/messages"
LOCAL_RESOURCE_DIR = "data/resources"
