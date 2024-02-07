from functools import cached_property
from typing import Generator, Optional

from flask import session

import gpt
import persistence as db
from config import CONVO_ID_SESSION_KEY, MEMORIES_FILEPATH, PERSONALITY_FILEPATH
from conversation import BotMessage, Conversation, SystemMessage, UserMessage


class Sambot:

    @cached_property
    def _bot_memories(self) -> str:
        with open(MEMORIES_FILEPATH, "r", encoding="utf-8") as file:
            return file.read()

    @cached_property
    def _bot_personality(self) -> str:
        with open(PERSONALITY_FILEPATH, "r", encoding="utf-8") as file:
            return file.read()

    def _extract_knowledge_prompt(self, user_content: str) -> str:
        return f"""Please extract and summarize using bullet points any relevant information in: "{self._bot_memories}"
            to answer the following user quesiton: "{user_content}". Respond with only a bullet-point saying
            there is no information if no relevant information exists to answer the question, or if the question
            seems unintelligable."""

    def _load_session_convo(self) -> Conversation:
        """
        Load the request session's conversation from the database, or create a new conversation
        and save it to both the session and the database for future access.
        """
        if convo_id := session.get(CONVO_ID_SESSION_KEY, None):
            if convo := db.load_convo(convo_id):
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

    def stream_convo(self, user_content: str) -> Generator[Conversation, None, None]:
        """
        Stream a partially updating conversation object back to the caller. A `UserMessage`
        containing the given `user_content` will be appended to the conversation first. Then,
        a `BotMessage` will be appended and slowly updated as data from ChatGPT is streamed
        back from their API.
        """
        convo = self._load_session_convo()


class Bot:
    """
    Contains main app logic. Bridge between the flask app endpoints and the
    rest of the app, including: app models, the persistance layer, and interaction
    with third-party APIs. TODO: Maybe write a better description of this class later.
    """

    def __init__(self, convo_id: str):
        self.convo_id = convo_id

    def chat_stream(self, user_content: str) -> Generator[Conversation, None, None]:
        """
        Chat with the bot, using the given `user_content`, and receive a stream of
        `Conversation` objects as they update while the bot responds.
        """
        convo = self.get_convo()
        extracted_info = self.extract_knowledge_info(user_content)

    def extract_knowledge_info(user_content) -> str:
        """
        Extract relevant information from the given `user_content` and return a string.
        """
        convo = Conversation(system=SystemMessage("You are a helpful assistant."))
        convo.append(
            UserMessage(
                f"""
            Please extract and summarize using bullet points any relevant information in: "{bot_memories}"
            to answer the following user quesiton: "{user_prompt}". Respond with only a bullet-point saying
            there is no information if no relevant information exists to answer the question, or if the question
            seems unintelligable.
        """
            )
        )
        gpt.chat(
            conversation=convo,
            model="gpt-3.5-turbo",
        )

    def get_convo(self) -> Optional[Conversation]:
        """
        Get the conversation for this bot, or None if none could be found.
        """
        try:
            return load_convo(id=self.convo_id)
        except FileNotFoundError:
            return None


class Knowledge(str):
    """
    String representation of what information the bot knows
    about how to answer a given piece of user content.
    """

    def __init__(self, user_content: str):
        f"""
            Please extract and summarize using bullet points any relevant information in: "{bot_memories}"
            to answer the following user quesiton: "{user_prompt}". Respond with only a bullet-point saying
            there is no information if no relevant information exists to answer the question, or if the question
            seems unintelligable.
        """
