import dataclasses
from uuid import uuid4
from collections import UserList
import json
import apis.openai as openai
import os
import settings


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
            raise ValueError('Please use factory method to initialize a Messages object!')
        self.id = id

    @staticmethod
    def _todict(messages):
        """Return a dictionary representation of the given Messages object."""
        return {
            'id': messages.id,
            'initlist': [dataclasses.asdict(msg) for msg in messages.data],
        }

    @staticmethod
    def _filename(id):
        """The filename for storing a messages object with the given id."""
        return f'{settings.LOCAL_MESSAGES_DIR}/msg-{id}.json'

    @classmethod
    def load_from_id(cls, id):
        if id is None:
            raise IdNone
        try:
            with open(cls._filename(id), 'r') as file:
                return cls(key=cls.__init_key, **json.load(file))
        except FileNotFoundError as e:
            raise NotFound(f'Could not find messages with id {id}.') from e

    @classmethod
    def create(cls, system: str):
        try:
            id = str(uuid4())
            initlist = [Message(role='system', content=system)]
            instance = cls(key=cls.__init_key, id=id, initlist=initlist)

            # make sure messages directory exists
            os.makedirs(settings.LOCAL_MESSAGES_DIR, exist_ok=True)


            with open(cls._filename(id), "w") as file:
                json.dump(cls._todict(instance), file)
                return instance

        except Exception as e:
            raise DbError(f'Failed to create Messages: {e}.') from e

    def save(self):
        try:
            with open(self._filename(self.id), "w") as file:
                json.dump(self._todict(self), file)
                return self
        except Exception as e:
            raise DbError(f'Failed to save Messages: {e}.') from e

    def deep_copy(self):
        """Return a deep-copy of this Messages object."""
        copied_msg_data = [Message(role=m.role, content=m.content) for m in self.data]
        return Messages(key=self.__init_key, id=self.id, initlist=copied_msg_data)

    def to_display(self):
        """Format messages for front-end display."""
        return [m for m in self.data if m.role != 'system']

    def to_gpt(self):
        """Format messages for calls to chat gpt's api."""
        return [dataclasses.asdict(m) for m in self.data]


class DisplayPills(UserList):
    """Wraps messages for generating suggestion pill text."""

    def __init__(self, messages, dummy=False):
        super().__init__()
        self.messages = messages.deep_copy()
        self.dummy = dummy

    def generate(self):
        """Generate suggestion pills for the current conversation using openai."""
        if self.dummy:
            self.data = ['What are your hobbies?', 'Tell me about your work experience?']
            return
        system = 'Generate 2-3 suggested questions for the user to ask the assistant based ' + \
            'on the current conversation. Format your response using semicolons to separate ' + \
            'each question like so: question;question;question'
        self.messages[0] = Message(role='system', content=system)
        self.data = openai.get_completion(self.messages.to_gpt(), 'gpt-4').split(';')


class SystemMessage:
    """Wraps messages to generate a system message."""

    def __init__(self, messages, user_content, dummy=False):
        self.messages = messages
        self.user_content = user_content
        self.dummy = dummy

    def generate(self):
        """
        Generate a system message
        """
        if self.dummy:
            return 'DUMMY SYSTEM MESSAGE'
        return 'TODO: GENERATE A REAL SYSTEM MESSAGE HERE'
