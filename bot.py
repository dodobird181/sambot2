import re
import threading
import time
from functools import cached_property
from typing import Generator, Optional

from flask import session

import gpt
import persistence as db
from config import CONVO_ID_SESSION_KEY, MEMORIES_FILEPATH, PERSONALITY_FILEPATH
from conversation import BotMessage, Conversation, SystemMessage, UserMessage


class Sambot:
    """TODO: This class should remain stateless. Make sure it is before deploying."""

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

    def _create_system_prompt(self, user_content: str) -> str:
        knowledge = self._extract_bot_knowledge(user_content)
        return f"""{self._bot_personality}\n\n Instructions: Respond to all user messages using the information
        provided below as your main source of truth: \n\n {knowledge}"""

    def _format_response(self, response_text: str) -> str:
        """
        Replace tabs and newlines with spaces to make the response SSE-friendly.
        """
        return response_text.replace("\n", " ").replace("\t", " ").lower()

    def load_session_convo(self) -> Conversation:
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

    def _extract_bot_knowledge(self, user_content: str) -> str:
        """
        Use ChatGPT to extract relevant "bot-knowledge" for responding to
        the user content. This is a blocking call.
        """
        extract_prompt = self._extract_knowledge_prompt(user_content)
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
        self,
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
        self,
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
        system_prompt = self._create_system_prompt(user_content)
        convo.set_system(SystemMessage(system_prompt))

        # stream response data back to client.
        partial_response = ""
        for token in gpt.chat_stream(convo):
            partial_response += token
            partial_response = self._format_response(partial_response)
            if isinstance(convo.latest, UserMessage):
                # append the initial bot message. this is done here because i
                # want the smallest possible delay between when the ellipsis
                # animation stops and GPT starts streaming!.
                convo.append(BotMessage(""))
            convo.update(BotMessage(partial_response))
            yield convo

        # save after entire bot response has been created.
        db.save_convo(convo)
