from msgspec.json import decode, encode
from msgspec import Struct
from datetime import datetime
from config import DATA_FILEPATH
import os


"""
TODO: Finish this file by creating tools for encoding and decoding `Conversation` objects
to and from json + tools for saving and loading json files locally. Should add config for database
location / json file location and remove old variables.
"""

if not os.path.exists(DATA_FILEPATH):
    os.makedirs(DATA_FILEPATH)


class Message(Struct):
    role: str
    content: str
    created_at: datetime


class Conversation(Struct):
    id: str
    messages: list[Message]


def save_conversation(app_conversation, path=DATA_FILEPATH) -> None:
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
