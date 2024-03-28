"""
Main app logic lives here.
"""

import asyncio
import datetime as dt
import enum

import flask

import apis.openai as openai
import config
import logs
import templates
import utils
from chat import Chat

with open("memories.md", "r") as file:
    MEMORIES = file.read()

with open("personality.md", "r") as file:
    PERSONALITY = file.read()


def find_or_create_chat(session) -> Chat:
    """
    Load a chat from the flask session, or create a new one
    and save it's id to the session for future retrieval.
    """
    if chat_id := session.get(config.CHAT_SESSION_KEY, None):
        if chat := Chat.objects.retrieve(chat_id):
            return chat
        logs.warning("session key failed to retrieve chat from database!")

    chat = Chat()
    chat.save()
    session[config.CHAT_SESSION_KEY] = str(chat.id)
    return chat


class Strategy(enum.Enum):
    """
    Enum representation of how sambot should respond to the user.
    """

    DEFAULT = "default"
    GREET = "greet"  # greet the user
    TOPICS = "topics"  # propose conversation topics
    INQUIRE_EMAIL = "inquire-email"  # inquire if sambot should send an email to the user
    SEND_EMAIL = "send-email"  # send an email to the user


def choose_response_strategy(user_input, user_chat) -> Strategy:
    """
    Uses some fuzzy heuristics powered by openai to determine what strategy
    to use when responding to the user.
    """

    async def get_strategy():
        strategy = await asyncio.gather(
            asyncio.to_thread(
                openai.get_completion,
                openai.flat_messages(
                    f"""
                    Based on this question should a greeting be generated in response to the following input?
                    Think carefully and consider informal greetings in the input to still be greetings.
                    Respond with either 'Yes', or 'No'. INPUT: {user_input}
                    """
                ),
                "gpt-3.5-turbo",
            ),
            asyncio.to_thread(
                openai.best_similarity,
                user_input,
                *[
                    "Can i see your resume?",
                    "What is your job experience like?",
                    "What is your educational background like?",
                ],
            ),
            asyncio.to_thread(
                openai.get_completion,
                [
                    *(message.dict() for message in user_chat.messages),
                    *openai.flat_messages(
                        f"""
                        Based on this question and the history of this chat, is it appropriate to generate a selection
                        of conversation topics as a response? Think carefully and consider what direction, if any, the
                        conversation is headed. If we seem to be going in circles, or remaining only on surface level
                        conversation topics, then it is appropriate to generate a selection of topics as a response. If,
                        however, the conversation if going somewhere interesting, then it is not appropriate to generate
                        a selection of topics because it might derail the interesting conversation.
                        Respond with either 'Yes', or 'No'. INPUT: {user_input}
                        """,
                    ),
                ],
                "gpt-3.5-turbo",
            ),
        )
        return {
            Strategy.GREET: strategy[0].upper() == "YES",
            Strategy.INQUIRE_EMAIL: strategy[1] < 0.5,
            Strategy.TOPICS: strategy[2] == "YES",
        }

    with utils.LogTime("Processed strategy in {seconds} seconds."):
        strategy = asyncio.run(get_strategy())
    utils.log_dict(strategy, ":: ")

    for key, value in strategy.items():
        if value:
            return key

    return Strategy.DEFAULT


def perform_response(user_input: str, user_chat: Chat, response_strategy: Strategy):
    """
    Generate a sambot response given the user's input, their chat history,
    and a strategy to use while responding. NOTE: This method will potentially
    perform additional actions, e.g., sending emails, etc.
    """
    if Strategy.DEFAULT == response_strategy:
        # perform default sambot response -> summarize the knowledge-base using
        # gpt3 and inject as system prompt for gpt4.
        # TODO: create proper system message here...
        logs.debug("Using default strategy...")
        with utils.LogTime("Summarized knowledge in {seconds} seconds."):
            summarized_knowledge = openai.get_completion(
                openai.flat_messages(
                    f"""
                    Summarize relevant information using bullet points from the following content to answer the given
                    quesiton. Keep your summary as short as possible. Respond with "NO INFO" if none of the information
                    available is relevant. Use a single bullet-point if the question is not very specific. \n\n
                    CONTENT: {MEMORIES}. \n\n
                    QUESTION: {user_input}.
                    """
                ),
                "gpt-3.5-turbo",
            )
        utils.log_large_string(summarized_knowledge, ":: ", line_length=70)
        # user_chat.messages[0] = Chat.Message("SYSTEM MSG", Chat.SYSTEM)
        exit(0)
        return openai.get_completion(
            model="gpt4",
            stream=True,
            messages=[msg.dict() for msg in user_chat.messages],
        )
    ...
