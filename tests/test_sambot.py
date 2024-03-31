import unittest

import sambot
import settings
import tests
from chat import Chat


class TestSambot(tests.DatabaseTestCase):
    """
    Tests for the sambot module.
    """

    def test_find_or_create_chat_empty_session(self):
        """
        Empty session should create new chat and add key to session.
        """
        empty_session = {}
        result = sambot.find_or_create_chat(session=empty_session)
        valid_session = {settings.CHAT_SESSION_KEY: str(result.id)}
        self.assertEqual(valid_session, empty_session, "session modified correctly")

    def test_find_or_create_chat_invalid_key_in_session(self):
        """
        Invalid key in session should create a new chat and add key to session.
        """
        invalid_session = {settings.CHAT_SESSION_KEY: "INVALID_KEY"}
        result = sambot.find_or_create_chat(session=invalid_session)
        valid_session = {settings.CHAT_SESSION_KEY: str(result.id)}
        self.assertEqual(valid_session, invalid_session, "session modified correctly")

    def test_find_or_create_chat_valid_key_in_session(self):
        """
        A valid key in the session should return the existing chat referenced.
        """
        existing_chat = Chat.objects.create()
        valid_session = {settings.CHAT_SESSION_KEY: str(existing_chat.id)}
        result = sambot.find_or_create_chat(session=valid_session)
        self.assertEqual(result.id, existing_chat.id, "retrieved correct chat")


if __name__ == "__main__":
    unittest.main()
