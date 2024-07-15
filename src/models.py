import dataclasses
from uuid import uuid4
from collections import UserList
import json
import apis.openai as openai
import os
import settings
import logger
import asyncio
import resources
import Levenshtein as lev
import random

_logger = logger.get_logger(__name__)


class DbError(Exception):
    """Something went wrong while reading or writing to the database."""

    ...


class ReadError(DbError):
    """Something went wrong while reading data from the database."""

    ...


class WriteError(DbError):
    """Something went wrong while writing data to the database."""

    ...


class BadId(ReadError):
    """The provided id for database reading is either missing or malformed."""

    ...


class NotFound(BadId):
    """The id wasn't found in the database."""

    ...


class IdNone(BadId):
    """The provided id is None."""

    ...


@dataclasses.dataclass
class Message:
    """Chat gpt message."""

    role: str
    content: str


class Messages(UserList):
    """Unique message collection with DB create, load, and save."""

    __init_key = uuid4()  # soft force clients to use factory init methods

    def __init__(self, key=None, id=None, initlist=None):
        super().__init__(initlist=initlist)
        if key != self.__init_key:
            raise ValueError(
                "Please use factory method to initialize a Messages object!"
            )
        self.id = id

    @staticmethod
    def _todict(messages):
        """Return a dictionary representation of the given Messages object."""
        return {
            "id": messages.id,
            "initlist": [dataclasses.asdict(msg) for msg in messages.data],
        }

    @staticmethod
    def _filename(id):
        """The filename for storing a messages object with the given id."""
        return f"{settings.LOCAL_MESSAGES_DIR}/msg-{id}.json"

    @classmethod
    def load_from_id(cls, id):
        if not id:
            _logger.debug("Could not load messages using None id.")
            raise IdNone
        try:
            with open(cls._filename(id), "r") as file:
                data = json.load(file)
                initlist = [
                    Message(role=m["role"], content=m["content"])
                    for m in data["initlist"]
                ]
                instance = cls(key=cls.__init_key, id=data["id"], initlist=initlist)
                _logger.debug(f"Loaded messages from id {id}.")
                return instance
        except FileNotFoundError as e:
            err_msg = f"Could not find messages with id {id}."
            _logger.warn(err_msg)
            raise NotFound(err_msg) from e
        except json.decoder.JSONDecodeError as e:
            err_msg = f"Error decoding messages with id: {id}. {e.args}"
            _logger.warn(err_msg)
            raise NotFound(err_msg) from e

    @classmethod
    def create(cls, system: str):
        try:
            id = str(uuid4())
            initlist = [Message(role="system", content=system)]
            instance = cls(key=cls.__init_key, id=id, initlist=initlist)

            # make sure messages directory exists
            os.makedirs(settings.LOCAL_MESSAGES_DIR, exist_ok=True)

            with open(cls._filename(id), "w") as file:
                json.dump(cls._todict(instance), file)
                return instance

        except Exception as e:
            raise WriteError(f"Failed to create Messages: {e}.") from e

    def save(self):
        try:
            with open(self._filename(self.id), "w") as file:
                json.dump(self._todict(self), file)
                return self
        except Exception as e:
            raise WriteError(f"Failed to save Messages: {e}.") from e

    def delete(self):
        try:
            os.remove(self._filename(self.id))
        except Exception as e:
            raise WriteError(f"Failed to delete messages: {e}.") from e

    def deep_copy(self):
        """Return a deep-copy of this Messages object."""
        copied_msg_data = [Message(role=m.role, content=m.content) for m in self.data]
        return Messages(key=self.__init_key, id=self.id, initlist=copied_msg_data)

    def to_display(self):
        """Format messages for front-end display."""
        return [m for m in self.data if m.role != "system"]

    def to_gpt(self):
        """Format messages for calls to chat gpt's api."""
        return [dataclasses.asdict(m) for m in self.data]

    def to_system_gen(self):
        """Format messages as string for injection into system prompt generator."""
        return '\n'.join([f"{m.role} :: {m.content}" for m in self.data if m.role != "system"])


class DisplayPills(UserList):
    """Wraps messages for generating suggestion pill text."""

    PILLS = [
        "What are your hobbies?",
        "Where are you from?",
        "Can I see your resume?",
        "What is your work experience?",
        "Where were you born?",
        "What is your favourite video game?",
        "Where did you go to school?",
        "What do you like about living in Montreal?",
        "What are your hobbies outside work?",
        "What is your favourite movie?",
        "What is your favourite music genre?",
        "Do you have a favorite programming language?",
        "Do you prefer coffee or tea?",
        "Do you like to read?",
    ]

    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    @staticmethod
    def get_str_similarity(str1, str2) -> float:
        """Get the character distance between two strings as a percentage."""
        distance = lev.distance(str1, str2)
        distance = 0.0001 if distance == 0 else distance  # avoid divide by 0
        return (1 / distance) * 100

    def generate(self):
        """Generate suggestion pills for the user to click on."""

        if len(self.messages) <= 4:
            # dont show pills at very start of a convo
            self.data = []
            return

        pill_options = []  # populated below
        user_message_contents = [
            message.content for message in self.messages if message.role == "user"
        ]
        for pill in self.PILLS:
            should_add = True
            for user_content in user_message_contents:
                if self.get_str_similarity(user_content, pill) >= 6:
                    # dont add if too similar to something already asked by the user
                    should_add = False
            if should_add:
                pill_options.append(pill)

        # sample random pill options
        self.data = random.sample(pill_options, min(3, len(pill_options)))


class SystemMessage:
    """Wraps messages to generate a system message."""

    embeddings = openai.Embedding.load_list('embeddings.json')

    def __init__(self, messages, user_content, dummy=settings.USE_DUMMY_SYSTEM_MESSAGE):
        self.messages = messages
        self.user_content = user_content
        self.dummy = dummy

    async def generate(self):
        """
        Generate a system message
        """

        if self.dummy:
            await asyncio.sleep(2)  # fake delay for testing
            return "DUMMY SYSTEM MESSAGE"

        system_gen_prompt = (
            "Restate the user's question to include the context of the conversation:\n" +
            f"{self.messages.to_system_gen()}"
        )

        contextualized_user_question = await openai.async_get_completion(
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant.',
                },
                {
                    'role': 'user',
                    'content': (
                        "Rephrase the user's question to make sense in the conversation context. Only " +
                        "respond with the new question." +
                        f"\n\nCONVERSATION:\n\n{self.messages.to_system_gen()}\nuser :: {self.user_content}"
                    )
                }
            ],
            model='gpt-4o',
        )
        _logger.debug(f'Original user question: {self.user_content}.')
        _logger.debug(f'Contextualized user quesiton: {contextualized_user_question}.')

        """
        hallucination_stopper = await openai.async_get_completion(
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant.',
                },
                {
                    'role': 'user',
                    'content': (
                        "Rephrase this question by asserting that if the person reading the question" +
                        "doesn't know the answer because it's too specific, that they should tell the" +
                        "user that they don't have that information. Respond only with the new question." +
                        f"\n\Question:\n\n{contextualized_user_question}"
                    )
                }
            ],
            model='gpt-4o',
        )
        _logger.debug(f'Hallucination stopper: {hallucination_stopper}.')"""

        embedding_distances = [d for d in openai.k_nearest(
            content=contextualized_user_question,
            embeddings=self.embeddings,
            k=20,
        ) if d.dist < 0.64]
        _logger.debug(f'''Found k-nearest embedding distances: {[
            (d.e2.content, d.dist)
            for d in embedding_distances
        ]}.''')

        embedded_knowledge = '\n'.join([d.e2.content for d in embedding_distances])
        return f'{resources.STYLE}\n\n#Knowledge\n{embedded_knowledge}'



        system_gen_messages = Messages.create("You are a helpful assistant.")
        system_gen_messages.append(Message(role="user", content=system_gen_prompt))

        system_knowledge = await openai.async_get_completion(
            messages=system_gen_messages.to_gpt(),
            model="gpt-4o",
        )
        system_gen_messages.delete()  # delete the temporary prompt message

        _logger.debug(f'Generated system message "knowledge":\n{system_knowledge}')

        return f"{resources.STYLE}\n\n#Knowledge Base\n{system_knowledge}\n\nBegin now."
