import asyncio

import apis.openai as openai
import logs
import sambot
import utils
from chat import Chat

# sambot.perform_response("What's your life experience", Chat(), sambot.Strategy.DEFAULT)

logger = logs.get_logger(__name__)

logger.debug("Ignore me!")
logger.info("Hello world!")
