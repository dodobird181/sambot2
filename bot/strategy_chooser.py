import asyncio
import enum
import logging
import templates
import conversation
import gpt

logger = logging.Logger(__name__)


class BotStrategy(enum.Enum):
    """
    Enum representation of how the bot should respond to a user's input.
    """

    DEFAULT = enum.auto()
    GREETING = enum.auto()
    PROPOSE_TOPICS = enum.auto()
    SEND_EMAIL = enum.auto()


def response_to_bool(gpt_response: str) -> bool:
    """
    Translate a gpt response to a boolean value.
    """
    caps = gpt_response.upper()
    if "YES" in caps:
        return True
    elif "NO" in caps:
        return False
    logger.warning(
        f"Failed to interpret GPT bool: '{gpt_response}', defaulting to False."
    )
    return False


def choose_bot_strategy(user_content, convo) -> BotStrategy:
    """
    Given some user input, and the current conversation, choose an appropriate bot strategy.
    """
    gpt.chat(convo=conversation.Conversation())

