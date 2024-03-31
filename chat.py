import copy
import dataclasses
import pathlib
import pickle
import uuid

import logs
import settings
import utils


class ChatFactory(utils.Factory):
    """
    For creating and retrieving chat objects from the database.
    """

    def create(self):
        """
        Create an empty chat in the database.
        """
        chat = Chat()
        with open(self.path(chat), "wb") as file:
            pickle.dump(chat, file)
        return chat

    def retrieve(self, id):
        """
        Retrieve a chat from the database.
        """
        try:
            with open(self.path(id), "rb") as file:
                return pickle.load(file)
        except FileNotFoundError as e:
            logs.warning(f"No chat found at = {self.path(id)}", exc_info=e)
            return None

    def delete(self, id):
        """
        Delete a chat from the database.
        """
        path = pathlib.Path(self.path(id))
        path.unlink(missing_ok=True)


class Chat:
    """
    Chat object that supports deep-copy, CRUD operations via pickle,
    message appending and sending requests to chat gpt's api.
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

        def dict(self):
            return {"role": self.role, "content": self.content}

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
        with open(f"{settings.PICKLE_DB_PATH}{self.id}.pkl", "wb") as file:
            pickle.dump(self, file)
