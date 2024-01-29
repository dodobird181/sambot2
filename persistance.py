from msgspec.json import decode, encode
from msgspec import Struct
from msgspec import DecodeError
from datetime import datetime
from config import DATA_FILEPATH
import os


if not os.path.exists(DATA_FILEPATH):
    os.makedirs(DATA_FILEPATH)


class Message(Struct):
    role: str
    content: str
    created_at: datetime


class Conversation(Struct):
    id: str
    messages: list[Message]


def save_convo(app_conversation, path=DATA_FILEPATH) -> None:
    """
    Save an app conversation to a json file.
    """
    json_string = encode(Conversation(
        id=app_conversation.id,
        messages=[
            Message(
                role=app_message['role'],
                content=app_message['content'],
                created_at=app_message.created_at,
            ) for app_message in app_conversation
        ],
    ))
    with open(f'{path}{app_conversation.id}.json', 'wb') as file:
        file.write(json_string)


def load_convo(id: str, path=DATA_FILEPATH):
    """
    Load an app conversation from its id. TODO: this method is a little
    lengthy and uses delayed imports. See if you can't fix this...
    """
    with open(f'{path}{id}.json', 'r') as file:
        conversation = decode(file.read(), type=Conversation)

    from conversation import Conversation as AppConversation
    from conversation import SystemMessage, UserMessage, BotMessage
    json_system = conversation.messages[0]
    system = SystemMessage(
        content=json_system.content,
        created_at=json_system.created_at,
    )
    app_conversation = AppConversation(system=system, id=conversation.id)
    for message in conversation.messages[1:]:
        if 'system' == message.role:
            raise DecodeError('System message in non-0th position.')
        msg_class = UserMessage if 'user' == message.role else BotMessage
        app_conversation.append(msg_class(content=message.content, created_at=message.created_at))

    return app_conversation
