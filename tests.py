import unittest
import os

from parameterized import parameterized_class, parameterized
from conversation import *
from persistence import load_convo, save_convo
from config import TEST_DATA_FILEPATH
from msgspec.json import encode


if not os.path.exists(TEST_DATA_FILEPATH):
    os.makedirs(TEST_DATA_FILEPATH)


@parameterized_class(
    ("message_class", "expected_role"),
    [(UserMessage, "user"), (BotMessage, "assistant"), (SystemMessage, "system")],
)
class TestMessages(unittest.TestCase):
    """
    Test suite for the `UserMessage`, `BotMessage`, and `SystemMessage` classes.
    """

    def get_other_message_class(self):
        """
        Get another message class, other than the current one
        provided by the @parameterized_class decorator.
        """
        classes = [UserMessage, BotMessage, SystemMessage]
        is_other = lambda x: x != self.message_class
        return next(filter(is_other, classes))

    def setUp(self):
        self.message = self.message_class("Hello world!")

    def test_init(self):
        self.assertEqual(
            self.expected_role, self.message["role"], "Message has expcted role."
        )
        self.assertEqual(
            "Hello world!", self.message["content"], "Message has expected content."
        )

    def test_equality(self):
        msg_same = self.message_class("Hello world!")
        msg_different_content = self.message_class("Different message!")
        msg_different_class = self.get_other_message_class()("Hello world!")
        self.assertEqual(
            msg_same, self.message, "Different instance of same message is equal."
        )
        self.assertNotEqual(
            msg_different_content,
            self.message,
            "Message with different content not equal.",
        )
        self.assertNotEqual(
            msg_different_class, self.message, "Message with different class not equal."
        )


class TestConversation(unittest.TestCase):
    """
    Test suite for the `Conversation` class.
    """

    def test_latest_base_case_system_message_returned(self):
        system = SystemMessage("You are a helpful assistant.")
        convo = Conversation(system=system)
        self.assertEqual(convo.latest, system, "Latest msg is system msg in base case.")

    def test_latest_returns_user_or_bot_messages(self):
        user_msg = UserMessage("Hello world from user!")
        convo = Conversation(system=SystemMessage("You are a helpful assistant."))
        convo.append(user_msg)
        self.assertEqual(user_msg, convo.latest, "Latest msg is user msg.")
        bot_msg = BotMessage("Hello world from bot!")
        convo.append(bot_msg)
        self.assertEqual(bot_msg, convo.latest, "Latest msg is bot msg.")

    def test_latest_returns_correct_message_class(self):
        convo = Conversation(system=SystemMessage("You are a helpful assistant."))
        user_msg = UserMessage("Hello world from user!")
        bot_msg = BotMessage("Hello world from bot!")
        convo.append(user_msg)
        convo.append(bot_msg)
        self.assertEqual(
            user_msg, convo.latest(UserMessage), "Latest user msg is user msg."
        )
        convo.append(user_msg)
        self.assertEqual(
            bot_msg, convo.latest(BotMessage), "Latest bot msg is bot msg."
        )

    def test_latest_ignores_old_messages_from_the_same_class(self):
        convo = Conversation(system=SystemMessage("You are a helpful assistant."))
        convo.append(UserMessage("User msg 1"))
        convo.append(BotMessage("Bot msg 1"))
        convo.append(UserMessage("User msg 2"))
        latest = convo.latest(UserMessage)
        self.assertEqual(UserMessage("User msg 2"), latest, "Ignores old user msg.")

    def test_latest_grabs_system_message_from_0th_index(self):
        system = SystemMessage("You are a helpful assistant.")
        convo = Conversation(system=system)
        convo.append(UserMessage("User msg 1"))
        convo.append(BotMessage("Bot msg 1"))
        convo.append(UserMessage("User msg 2"))
        latest = convo.latest(SystemMessage)
        self.assertEqual(system, latest, "Grabs system message from 0th index.")

    def test_set_system(self):
        convo = Conversation(system=SystemMessage("System message 1..."))
        convo.append(UserMessage("User msg 1"))
        convo.append(BotMessage("Bot msg 1"))
        convo.append(UserMessage("User msg 2"))
        convo.set_system(SystemMessage("System message 2!"))
        self.assertEqual(
            SystemMessage("System message 2!"),
            convo[0],
            "Set system replaces system message.",
        )

    def test_append(self):
        self.maxDiff = None
        convo = Conversation(system=SystemMessage("dummy system message"))
        convo.append(UserMessage("dummy user message"))
        convo.append(BotMessage("dummy bot message"))
        self.assertListEqual(
            list(convo),
            [
                {"role": "system", "content": "dummy system message"},
                {"role": "user", "content": "dummy user message"},
                {"role": "assistant", "content": "dummy bot message"},
            ],
            "Append appends messages to the conversation.",
        )

    def test_append_failure(self):
        convo = Conversation(system=SystemMessage("dummy system message"))
        with self.assertRaisesRegex(TypeError, "must be a Message"):
            convo.append("Not a message object!")
        with self.assertRaisesRegex(TypeError, "does not support SystemMessage"):
            convo.append(SystemMessage("dummy system message"))
        with self.assertRaisesRegex(TypeError, "Expected BotMessage, got UserMessage."):
            convo.append(UserMessage("dummy user message"))
            convo.append(UserMessage("another user message!"))
        with self.assertRaisesRegex(TypeError, "Expected UserMessage, got BotMessage."):
            convo.append(BotMessage("dummy bot message"))
            convo.append(BotMessage("another bot message!"))


class TestPersistence(unittest.TestCase):
    """
    Test suite for the persistence.py module.
    """

    def delete_app_data(self):
        for filename in os.listdir(TEST_DATA_FILEPATH):
            file_path = os.path.join(TEST_DATA_FILEPATH, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
            except Exception as e:
                print("Failed to delete %s. Reason: %s" % (file_path, e))

    def setUp(self):
        self.delete_app_data()
        self.addCleanup(self.delete_app_data)

    def test_save_conversation(self):
        convo = Conversation(system=SystemMessage("dummy system message"))
        convo.append(UserMessage("dummy user message"))
        convo.append(BotMessage("dummy bot message"))
        save_convo(convo, path=TEST_DATA_FILEPATH)
        datafiles = os.listdir(TEST_DATA_FILEPATH)
        self.assertEqual(1, len(datafiles), "A single datafile exists.")
        self.assertEqual(
            f"{str(convo.id)}.json", datafiles[0], "The datafile name is convo id."
        )

    def test_load_conversation(self):
        id = "test_conversation_id"
        with open(f"{TEST_DATA_FILEPATH}{id}.json", "wb") as file:
            file.write(
                encode(
                    {
                        "id": id,
                        "messages": [
                            {
                                "role": "system",
                                "content": "dummy system message",
                                "created_at": "2024-01-28T00:12:10.106641",
                            },
                            {
                                "role": "user",
                                "content": "dummy user message",
                                "created_at": "2024-01-28T00:12:10.106642",
                            },
                            {
                                "role": "assistant",
                                "content": "dummy bot message",
                                "created_at": "2024-01-28T00:12:10.106643",
                            },
                        ],
                    }
                )
            )
        convo = load_convo(id, path=TEST_DATA_FILEPATH)
        self.assertListEqual(
            list(convo),
            [
                {"role": "system", "content": "dummy system message"},
                {"role": "user", "content": "dummy user message"},
                {"role": "assistant", "content": "dummy bot message"},
            ],
            "Load loads messages from the conversation.",
        )
        self.assertEqual(
            convo[0].created_at, datetime.fromisoformat("2024-01-28T00:12:10.106641")
        )
        self.assertEqual(
            convo[1].created_at, datetime.fromisoformat("2024-01-28T00:12:10.106642")
        )
        self.assertEqual(
            convo[2].created_at, datetime.fromisoformat("2024-01-28T00:12:10.106643")
        )

    def test_load_conversation_fails(self):
        with self.assertRaises(FileNotFoundError):
            load_convo("not_a_real_id", path=TEST_DATA_FILEPATH)


if __name__ == "__main__":
    unittest.main()
