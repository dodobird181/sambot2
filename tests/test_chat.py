import pathlib
import pickle
import unittest
import uuid

import models
import tests


class TestChatFactory(tests.DatabaseTestCase):
    """
    Tests for the chat factory object.
    """

    def setUp(self):
        super().setUp()
        self.chat_id = "05588eed-d7eb-45a4-b0ad-9fe39ab3c22a"
        self.chat_path = f"tstpkldb/{self.chat_id}.pkl"
        self.factory = models.ChatFactory()

    def test_path(self):
        """
        Test path method works with UUID, str, and chat objects.
        """
        self.assertEqual(self.chat_path, self.factory.path(self.chat_id), "str id works")
        self.assertEqual(self.chat_path, self.factory.path(uuid.UUID(self.chat_id)), "uuid works")
        self.assertEqual(self.chat_path, self.factory.path(models.Chat()), "chat object works")

    def test_create(self):
        """
        Test create chat.
        """
        self.factory.create()
        with open(self.chat_path, "rb") as file:
            chat = pickle.load(file)
        self.assertEqual(self.chat_id, str(chat.id), "created chat has correct id")
        self.assertEqual([], chat.messages, "created chat has no messages")

    def test_retrieve(self):
        """
        Test retrieve chat.
        """
        with open(self.chat_path, "wb") as file:
            pickle.dump(models.Chat(), file)
        chat = self.factory.retrieve(self.chat_id)
        self.assertEqual(self.chat_id, str(chat.id), "retrieved chat has correct id")
        self.assertEqual([], chat.messages, "retrieved chat has no messages")

    def test_delete(self):
        """
        Test delete chat.
        """
        with open(self.chat_path, "wb") as file:
            pickle.dump(models.Chat(), file)
        os_path = pathlib.Path(self.chat_path)
        self.assertTrue(os_path.exists())
        self.factory.delete(self.chat_id)
        self.assertFalse(os_path.exists())


class TestChat(tests.DatabaseTestCase):
    """
    Tests for the chat object.
    """

    def setUp(self):
        super().setUp()
        self.chat_id = "05588eed-d7eb-45a4-b0ad-9fe39ab3c22a"
        self.chat_path = f"tstpkldb/{self.chat_id}.pkl"

    def test_save_append(self):
        """
        Test chat can save to database with a message appended to it.
        """
        chat = models.Chat()
        chat.append("Hello world!", models.Chat.USER)
        os_path = pathlib.Path(self.chat_path)
        self.assertFalse(os_path.exists())
        chat.save()
        self.assertTrue(os_path.exists())
        with open(self.chat_path, "rb") as file:
            saved_chat = pickle.load(file)
        self.assertEqual(1, len(saved_chat.messages), "chat contains message")
        self.assertEqual("Hello world!", saved_chat.messages[0].content, "message content correct")
        self.assertEqual(models.Chat.USER, saved_chat.messages[0].role, "message role is user")

    def test_copy(self):
        """
        Test chat can perform a deep-copy.
        """
        chat1 = models.Chat()
        chat1.append("Hello world", models.Chat.USER)
        chat2 = chat1.copy()
        self.assertNotEqual(chat1.id, chat2.id, "different database id")
        self.assertNotEqual(id(chat1), id(chat2), "different object instances")
        self.assertEqual(chat1.messages, chat2.messages, "same messages")


if __name__ == "__main__":
    unittest.main()
