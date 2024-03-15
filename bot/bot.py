import logging
import time
import uuid
from typing import *

import flask
from transitions.extensions import HierarchicalMachine

import config
import gpt
import persistence as db
import templates
from conversation import BotMessage, Conversation, SystemMessage, UserMessage

logger = logging.Logger(__name__)


"""
Send email
Respond to greeting
Propose conversation starters
Fetch project information from github
Inject sambot code into prompt asking about how the bot works.
"""


"""
Bot can be in the following ACTIVE states:
1. processing_gpt3 and processing_gpt4,
2. sending_email
3. retrieving_github_info
"""

"""
BOt can also be in the following PASSIVE states:
1. choose_strategy,
2. awaiting_email_confirmation
"""


class BotFixtures:
    """
    Static data used by the bot.
    """

    class Static:
        MEMORIES = "static/backend/memories.md"
        PERSONALITY = "static/backend/personality.md"

    class Templates:
        SUMMARIZE = "backend/prompts/summarize.html"
        SYSTEM = "backend/prompts/system.html"
        IS_GREETING = "backend/prompts/is_greeting.html"

    def _read_file(self, filename) -> str:
        """Read and return the contents of a file as a string."""
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()

    @property
    def memories(self) -> str:
        return self._read_file(self.Static.MEMORIES)

    @property
    def personality(self) -> str:
        return self._read_file(self.Static.PERSONALITY)


class Bot:
    """
    Bot wraps a conversation and contains additional state that informs
    how it responds to the user. Bot is the link between the app's Flask
    API, openai's ChatGPT API, and the conversation database model.
    """

    fixtures = BotFixtures()

    def _load_template(self, template_name, data) -> str:
        """Load template using data and return it as a string."""
        return templates.render(template_name, data)

    def _summarize_prompt(self, long_content, relevant_question) -> str:
        """Prompt designed for gpt-3.5 to summarize some arbitrarily long
        content into bullet-points relevant to answering the given question."""
        data = {"long_content": long_content, "relevant_question": relevant_question}
        return self._load_template(self.fixtures.Templates.SUMMARIZE, data)

    def _send_prompt_to_gpt3(self, prompt) -> str:
        """Send a blocking API call to gpt-3 using a single prompt."""
        convo = Conversation.create_empty()
        convo.append(UserMessage(prompt))
        return self._send_convo_to_gpt3(convo)

    def _interpret_gpt_bool(self, gpt_bool: str) -> bool:
        """Interpret a string response from ChatGPT as either yes or no.
        If unsure, this method will default to no and log a warning. NOTE:
        this method relies on assumptions about how GPT is prompted to
        interpret whether GPT said yes or no and will by no means work
        for the general case."""
        caps = gpt_bool.upper()
        if "YES" in caps:
            return True
        elif "NO" in caps:
            return False
        logger.warning(
            f"Failed to interpret GPT bool: '{gpt_bool}', defaulting to False."
        )
        return False

    def _is_greeting(self, user_content) -> bool:
        """Return `True` if the `user_content` is deemed to be a
        greeting, `False` otherwise."""
        is_greeting_prompt = self._load_template(
            self.fixtures.Templates.IS_GREETING,
            data={"user_content": user_content},
        )
        gpt_bool = self._send_prompt_to_gpt3(is_greeting_prompt)
        return self._interpret_gpt_bool(gpt_bool)

    def default_system_prompt(self, user_content) -> str:
        """Prompt designed for gpt-4 to generate a response in the tone of
        sambot's personality, using a summarized version of the sambot memories.
        NOTE: This function sends a blocking call to gpt-3.5."""
        summarize_prompt = self._summarize_prompt(self.fixtures.memories, user_content)
        memory_knowledge = self._send_prompt_to_gpt3(summarize_prompt)
        data = {"personality": self.fixtures.personality, "knowledge": memory_knowledge}
        return self._load_template(self.fixtures.Templates.SYSTEM, data)

    def __init__(self):
        ...
        # load conversation


def _format_response(response_text: str) -> str:
    """
    Replace tabs and newlines with spaces to make the response SSE-friendly.
    """
    return response_text.replace("\n", " ").replace("\t", " ").lower()


def load_session_convo() -> Conversation:
    """
    Load the request session's conversation from the database, or create a new conversation
    and save it to both the session and the database for future access.
    """
    if convo_id := flask.session.get(config.CONVO_ID_SESSION_KEY, None):
        if convo := db.load_convo(convo_id):
            print("found existing convo in db!")
            return convo
        else:
            # missing in database but key existed, create a new convo
            # and log a warning. Either the convo got deleted from the
            # database, or an invalid id was saved in the session...
            print(
                f"WARNING: convo_id ({convo_id}) in session but missing from database."
            )

    # create, save, and return a new conversation
    convo = Conversation.create_empty()
    session[config.CONVO_ID_SESSION_KEY] = convo.id
    db.save_convo(convo)
    return convo


def _extract_bot_knowledge(user_content: str) -> str:
    """
    Use ChatGPT to extract relevant "bot-knowledge" for responding to
    the user content. This is a blocking call.
    """
    extract_prompt = _extract_knowledge_prompt(user_content)
    extract_convo = Conversation(SystemMessage("You are a helpful assistant."))
    extract_convo.append(UserMessage(extract_prompt))
    return gpt.chat(extract_convo, model="gpt-3.5-turbo")
    """
    TODO: Make this also cover + summarize the chat's previous conversation data (incrementally, so
    we don't waste a LOT of GPT tokens.) This may help the AI stay in character during long conversations.
    E.g., if it admits it's an AI, it will then start referring to itself as such because it exists
    in the cobversation data. I will have to make a fake conversation to submit to GPT, and then pipe the response
    to the real conversation + save and return that one. Jeez! A little complicated!
    """


def dummy_stream(
    user_content: str,
    convo: Conversation,
) -> Generator[Conversation | str, None, None]:
    dummy_text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus.
        Suspendisse lectus tortor, dignissim sit amet, adipiscing nec, ultricies sed, dolor. Cras
        elementum ultrices diam.
    """
    convo.append(UserMessage(user_content))
    yield convo
    yield "START ELLIPSIS"
    time.sleep(3)
    partial_message = ""
    for token in dummy_text.split(" "):
        partial_message += token + " "
        if isinstance(convo.latest, UserMessage):
            convo.append(BotMessage(""))
        convo.update(BotMessage(partial_message))
        yield convo
        time.sleep(0.02)
    db.save_convo(convo)


def stream_convo(
    user_content: str,
    convo: Conversation,
) -> Generator[Conversation | str, None, None]:
    """
    Stream a partially updating conversation object back to the caller. A `UserMessage`
    containing the given `user_content` will be appended to the conversation first. Then,
    a `BotMessage` will be appended and slowly updated as data from ChatGPT is streamed
    back from their API.
    """

    # yield user message immediately.
    convo.append(UserMessage(user_content))
    yield convo

    # let client know it can start ellipsis animation.
    yield "START ELLIPSIS"

    # compute system message (this is a blocking call to the ChatGPT API.)
    system_prompt = _create_system_prompt(user_content)
    print(system_prompt)
    convo.set_system(SystemMessage(system_prompt))

    # stream response data back to client.
    partial_response = ""
    for token in gpt.chat_stream(convo):
        partial_response += token
        partial_response = _format_response(partial_response)
        if isinstance(convo.latest, UserMessage):
            # append the initial bot message. this is done here because i
            # want the smallest possible delay between when the ellipsis
            # animation stops and GPT starts streaming!.
            convo.append(BotMessage(""))
        convo.update(BotMessage(partial_response))
        yield convo

    # save after entire bot response has been created.
    db.save_convo(convo)


def stream_initial(
    user_content: str,
    convo: Conversation,
) -> Generator[Conversation | str, None, None]:
    """
    TODO
    """

    # let client know it can start ellipsis animation.
    yield "START ELLIPSIS"

    # compute system message (this is a blocking call to the ChatGPT API.)
    system_prompt = _create_system_prompt(user_content)
    print(system_prompt)
    convo.set_system(SystemMessage(system_prompt))
    convo.append(UserMessage(user_content))

    # stream response data back to client.
    partial_response = ""
    for token in gpt.chat_stream(convo):
        partial_response += token
        partial_response = _format_response(partial_response)
        if isinstance(convo.latest, UserMessage):
            # append the initial bot message. this is done here because i
            # want the smallest possible delay between when the ellipsis
            # animation stops and GPT starts streaming!.
            convo.pop()  # remove user msg before yielding!
            convo.append(BotMessage(""))
        convo.update(BotMessage(partial_response))
        yield convo

    # save after entire bot response has been created.
    db.save_convo(convo)
