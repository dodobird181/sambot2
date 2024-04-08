import os

import applogging
import settings
from models.chat import Chat, ChatFactory

# create DB directory if none exists yet
logger = applogging.get_logger(__name__)
if os.path.exists(settings.PICKLE_DB_PATH):
    logger.info(f'Found existing database folder: "{settings.PICKLE_DB_PATH}".')
else:
    logger.info(f'Creating database folder: "{settings.PICKLE_DB_PATH}"...')
    os.makedirs(settings.PICKLE_DB_PATH, exist_ok=True)
