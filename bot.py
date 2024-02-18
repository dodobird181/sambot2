import enum
import functools
import re
import threading
import time
from typing import Generator, Optional

from flask import session

import gpt
import persistence as db
import templating
from config import CONVO_ID_SESSION_KEY, MEMORIES_FILEPATH, PERSONALITY_FILEPATH
from conversation import BotMessage, Conversation, SystemMessage, UserMessage


@functools.lru_cache()
def _bot_memories() -> str:
    with open(MEMORIES_FILEPATH, "r", encoding="utf-8") as file:
        return file.read()


@functools.lru_cache()
def _bot_personality() -> str:
    with open(PERSONALITY_FILEPATH, "r", encoding="utf-8") as file:
        return file.read()


def _extract_knowledge_prompt(user_content: str) -> str:
    return f"""Summarize relevant information using bullet points from: "{_bot_memories()}"
        to answer the following user quesiton: "{user_content}". Keep your summary as short as possible,
        responding with "NO INFO" if none of the information available is relevant, or a single bullet
        point if the user question is not very specific."""


def _create_system_prompt(user_content: str) -> str:
    knowledge = _extract_bot_knowledge(user_content)
    return f"""{_bot_personality()}\n\n Instructions: Respond to all user messages using the information
    provided below as your main source of truth: \n\n {knowledge}"""


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
    if convo_id := session.get(CONVO_ID_SESSION_KEY, None):
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
    session[CONVO_ID_SESSION_KEY] = convo.id
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


class BotResponse:
    """
    Contains high-level logic for building sambot responses given the user's
    input, conversation context, and
    """

    class Strategy(enum.Enum):
        """
        Represents the strategy to use for generating the bot's response.
        """

        CHOOSE_STRATEGY = (
            "choose_strategy",
            "this is a meta strategy",
        )
        POLL_GITHUB_API = (
            "poll_github_api",
            "poll sam morris's github API to get information about his public repositories.",
        )
        SUMMARIZE_EXPERIENCE = (
            "summarize_experience",
            "search in your knowledge-base for specific information about yourself and your interests.",
        )
        OFFER_NEW_CONVO_TOPIC = (
            "offer_new_convo_topic",
            "propose a new topic of conversation",
        )
        SEARCH_THE_WEB = (
            "search_the_web",
            "search the web for specific information that may not be in your knowledge-base.",
        )
        SEND_EMAIL = ("send_email", "begin a flow that will send an email to the user.")

    def __init__(self, convo):
        self.convo = convo

    def _gpt_3_response(self, prompt) -> str:
        temp_convo = Conversation(SystemMessage("You are a helpful assistant."))
        temp_convo.append(UserMessage(prompt))
        return gpt.chat(temp_convo, model="gpt-3.5-turbo")

    def _use_strategy(self, strategy) -> str:
        """Use GPT3 strategy and return response."""
        strategy_list = [x.value[1] for x in self.Strategy]
        if self.Strategy.CHOOSE_STRATEGY == strategy:
            # disallow choose strategy from choosing itself
            strategy_list.remove(self.Strategy.CHOOSE_STRATEGY.value[1])
        prompt = templating.render_jinja2(
            template_name=f"response_strategies/{strategy.value[0]}.html",
            data={
                "convo": self.convo,
                "strategy_list": strategy_list,
            },
        )
        print(f"strategy prompt: {prompt}")
        result = self._gpt_3_response(prompt=prompt)
        print(f"strategy result: {result}")
        return result
