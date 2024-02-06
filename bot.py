from flask.wrappers import Request
from conversation import Conversation, SystemMessage, UserMessage, BotMessage
from persistence import load_convo, save_convo
from typing import Optional, Generator
import gpt



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
        convo = Conversation(system=SystemMessage('You are a helpful assistant.'))
        convo.append(UserMessage(f'''
            Please extract and summarize using bullet points any relevant information in: "{bot_memories}"
            to answer the following user quesiton: "{user_prompt}". Respond with only a bullet-point saying
            there is no information if no relevant information exists to answer the question, or if the question
            seems unintelligable.
        '''))
        gpt.chat(
            conversation=convo,
            model='gpt-3.5-turbo',
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
        f'''
            Please extract and summarize using bullet points any relevant information in: "{bot_memories}"
            to answer the following user quesiton: "{user_prompt}". Respond with only a bullet-point saying
            there is no information if no relevant information exists to answer the question, or if the question
            seems unintelligable.
        '''
