import abc
from typing import *
from collections import UserDict, UserList
import uuid


class Message(UserDict, abc.ABC):
    """
    Represents a string message. Inherits from UserDict because
    the ChatGPT API expects messages to be in a dictionary format.
    """

    def __init__(self, content: str):
        super().__init__()
        self |= {
            'role': self.role(),
            'content': content,
        }

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

    def role(self) -> str:
        return 'user'


class BotMessage(Message):
    """
    A message sent by a bot.
    """

    def role(self) -> str:
        # assistant is expected by the GPT api
        return 'assistant'


class SystemMessage(Message):
    """
    A ChatGPT 'system' message.
    """

    def role(self) -> str:
        return 'system'


class Conversation(UserList):
    """
    A mutable conversation composed of 1 or more messages. Contains
    persistance methods for saving data across user-sessions.
    """

    def __init__(self, system: SystemMessage):
        super().__init__([system])
        self.id = uuid.uuid4()

    def set_system(self, system: SystemMessage):
        """
        Set the system message.
        """
        self[0] = system

    def latest_message(self, message_class=Message) -> Message:
        """
        Get the latest message in this conversation, where `message_class`
        is an optional parameter denoting the type of message you wish to retrieve.
        """
        for i in range(len(self) - 1, -1, -1):
            # iterate backwards through the list
            message = self[i]
            if isinstance(message, message_class):
                return message
        raise StopIteration  # shouldn't happen unless list data tampered with...

    def append(self, item) -> None:
        """
        Append a message onto the end of this conversation.
        """
        if not isinstance(item, Message):
            raise TypeError('Conversation item must be a Message.')

        if isinstance(item, SystemMessage):
            raise TypeError('Append does not support SystemMessage. Use set_system instead.')

        latest_msg = self.latest_message()
        if isinstance(item, UserMessage) and isinstance(latest_msg, UserMessage):
            raise TypeError('Message out of turn. Expected BotMessage, got UserMessage.')

        if isinstance(item, BotMessage) and isinstance(latest_msg, BotMessage):
            raise TypeError('Message out of turn. Expected UserMessage, got BotMessage.')

        super().append(item)
