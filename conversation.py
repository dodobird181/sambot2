import abc
from typing import *
from collections import UserDict, UserList
import uuid
from datetime import datetime


class Message(UserDict, abc.ABC):
    """
    Represents a string message. Inherits from UserDict because
    the ChatGPT API expects messages to be in a dictionary format.
    """

    def __init__(self, content: str, created_at: datetime = None):
        super().__init__()
        self |= {
            "role": self.role(),
            "content": content,
        }
        self.created_at = created_at if created_at else datetime.now()

    @abc.abstractmethod
    def role(self) -> str:
        """
        Who sent the message.
        """
        ...


class UserMessage(Message):
    """
    A message sent by a USER.
    """

    @classmethod
    def role(cls) -> str:
        return "user"


class BotMessage(Message):
    """
    A message sent by a bot.
    """

    def role(self) -> str:
        # assistant is expected by the GPT api
        return "assistant"


class SystemMessage(Message):
    """
    A ChatGPT 'system' message.
    """

    def role(self) -> str:
        return "system"

    @property
    @classmethod
    def EMPTY(cls):
        """
        System message placeholder. Used for initializing conversations before
        an bot response is generated and appended to the end of the conversation.
        """
        return cls("")


class Conversation(UserList):
    """
    A mutable conversation composed of 1 or more messages. Contains
    persistence methods for saving data across user-sessions.
    """

    def __init__(self, system: SystemMessage, id: uuid = uuid.uuid4()):
        super().__init__([system])
        self.id = id

    def set_system(self, system: SystemMessage):
        """
        Set the system message. TODO: This will be deprecated by the more general function: update_latest...
        """
        self[0] = system

    @property
    def latest(self, message_class=Message) -> Message:
        """
        Get the latest message in this conversation, where `message_class`
        is an optional parameter denoting the type of message you wish to retrieve.
        """
        for i in range(len(self) - 1, -1, -1):
            # iterate backwards through the list
            message = self[i]
            if isinstance(message, message_class):
                return message
        raise StopIteration(f"No instance of {message_class} in {self}.")

    def append(self, item) -> None:
        """
        Append a message onto the end of this conversation.
        """
        if not isinstance(item, Message):
            raise TypeError("Conversation item must be a Message.")

        if isinstance(item, SystemMessage):
            raise TypeError(
                "Append does not support SystemMessage. Use set_system instead."
            )

        latest_msg = self.latest
        if isinstance(item, UserMessage) and isinstance(latest_msg, UserMessage):
            raise TypeError(
                "Message out of turn. Expected BotMessage, got UserMessage."
            )

        if isinstance(item, BotMessage) and isinstance(latest_msg, BotMessage):
            raise TypeError(
                "Message out of turn. Expected UserMessage, got BotMessage."
            )

        super().append(item)

    def update(self, item) -> None:
        """
        Update the latest message in this conversation.
        """
        latest_type = type(self.latest)
        if not isinstance(item, latest_type):
            raise TypeError(
                f"Cannot update conversation with {item}, expected {latest_type}."
            )
        self[len(self) - 1] = item
