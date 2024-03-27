import asyncio

import apis.openai as openai
import sambot
import utils
from chat import Chat

sambot.perform_response("What's your life experience", Chat(), sambot.Strategy.DEFAULT)
