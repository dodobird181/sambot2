import copy
import dataclasses
import enum
import pickle
import uuid

import config
import gpt
import logger


class ChatFactory:
    """
    For creating and retrieving chat objects from the database.
    """

    def create(self):
        """
        Create an empty chat in the database.
        """
        chat = Chat()
        with open(f"{config.PICKLE_DB_PATH}{chat.id}.pkl", "wb") as file:
            pickle.dump(chat, file)
        return chat

    def retrieve(self, id):
        """
        Retrieve a chat from the database.
        """
        with open(f"{config.PICKLE_DB_PATH}{id}.pkl", "rb") as file:
            return pickle.load(file)


class Chat:
    """
    Chat object that supports deep-copy, CRUD operations via pickle,
    message appending and sending requests via chat gpt's api.
    """

    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"

    @dataclasses.dataclass
    class Message:
        """
        Dataclass for storing message data.
        """

        content: str
        role: str

    objects = ChatFactory()

    def __init__(self):
        """
        Create an empty chat with random uuid.
        """
        self.id = uuid.uuid4()
        self.messages = []

    def copy(self):
        """
        Create a deep-copy of this chat.
        """
        chat_copy = Chat()
        chat_copy.messages = copy.deepcopy(self.messages)
        return chat_copy

    def append(self, content, role):
        """
        Append a new message onto this chat.
        """
        message = self.Message(content, role)
        self.messages.append(message)

    def save(self):
        """
        Save this chat to the database.
        """
        with open(f"{config.PICKLE_DB_PATH}{self.id}.pkl", "wb") as file:
            pickle.dump(self, file)

    def gpt_request(self, model, stream=False):

        def streamed_response():
            return gpt.request(
                messages=[
                    {"role": i.role, "content": i.content} for i in self.messages
                ],
                model=model,
                stream=stream,
            )

        if stream:
            for chunk in streamed_response():
                yield chunk
        else:
            all_data = "".join(chunk for chunk in streamed_response())
            return all_data
