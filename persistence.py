import os
from datetime import datetime

from msgspec import DecodeError, Struct
from msgspec.json import decode, encode

from config import DATA_FILEPATH

if not os.path.exists(DATA_FILEPATH):
    os.makedirs(DATA_FILEPATH)


class Sambot(Struct):
    id: str
    convo_id: str
    state: str


class Message(Struct):
    role: str
    content: str
    created_at: datetime


class Conversation(Struct):
    id: str
    messages: list[Message]


def save_sambot(app_sambot, path=DATA_FILEPATH) -> None:
    """
    Save an app sambot to a json file.
    """
    json_string = encode(
        Sambot(
            id=app_sambot.id,
            convo_id=app_sambot.convo.id,
            state=app_sambot.state,
        ),
    )
    with open(f"{path}BOT--{app_sambot.id}.json", "wb") as file:
        file.write(json_string)


def save_convo(app_conversation, path=DATA_FILEPATH) -> None:
    """
    Save an app conversation to a json file.
    """
    json_string = encode(
        Conversation(
            id=app_conversation.id,
            messages=[
                Message(
                    role=app_message["role"],
                    content=app_message["content"],
                    created_at=app_message.created_at,
                )
                for app_message in app_conversation
            ],
        )
    )
    with open(f"{path}CONVO--{app_conversation.id}.json", "wb") as file:
        file.write(json_string)


def load_sambot(id, path=DATA_FILEPATH):
    try:
        with open(f"{path}BOT--{id}.json", "r") as file:
            sambot = decode(file.read(), type=Sambot)
    except FileNotFoundError:
        return None

    import bot.bot as bot

    return bot.Sambot(
        convo=load_convo(id=sambot.convo_id),
        state=sambot.state,
        id=sambot.id,
    )


def load_convo(id: str, path=DATA_FILEPATH):
    """
    Load an app conversation from its id, or return None if the file
    cannot be found. TODO: this method is a little
    lengthy and uses delayed imports. See if you can't fix this...
    """
    try:
        with open(f"{path}CONVO--{id}.json", "r") as file:
            conversation = decode(file.read(), type=Conversation)
    except FileNotFoundError:
        return None

    def replace_non_ascii_with_space(s):
        return "".join(c if ord(c) < 128 else " " for c in s)

    from conversation import BotMessage
    from conversation import Conversation as AppConversation
    from conversation import SystemMessage, UserMessage

    json_system = conversation.messages[0]
    system = SystemMessage(
        content=json_system.content,
        created_at=json_system.created_at,
    )
    app_conversation = AppConversation(system=system, id=conversation.id)
    for message in conversation.messages[1:]:
        if "system" == message.role:
            raise DecodeError("System message in non-0th position.")
        msg_class = UserMessage if "user" == message.role else BotMessage
        app_conversation.append(
            msg_class(
                content=replace_non_ascii_with_space(message.content),
                created_at=message.created_at,
            )
        )

    return app_conversation
