"""
Main app logic lives here.
"""

import asyncio
import enum
import random
import apis.openai as openai
import applogging
import models
import settings
import time

logger = applogging.get_logger(__name__)

with open("memories.md", "r") as file:
    MEMORIES = file.read()

with open("personality.md", "r") as file:
    PERSONALITY = file.read()


def find_or_create_chat(session) -> models.Chat:
    """
    Load a chat from the flask session, or create a new one
    and save it's id to the session for future retrieval.
    """
    if chat_id := session.get(settings.SESSION_CHAT_KEY, None):
        if chat := models.Chat.objects.retrieve(chat_id):
            logger.debug(f"Found session chat with ID: {chat_id}.")
            return chat
        logger.warning(f"Failed to retrieve session chat with ID: {chat_id}.")

    logger.debug("Creating new chat and adding to the session...")
    chat = models.Chat.objects.create()
    session[settings.SESSION_CHAT_KEY] = str(chat.id)
    return chat


class Strategy(enum.Enum):
    """
    Enum representation of how sambot should respond to the user.
    """

    DUMMY = 'dummy'  # fake message returned because dummy responses are enabled
    DEFAULT = "default"  # normal conversation
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
        if settings.ENABLE_DUMMY_RESPONSES:
            # short circuit API calls if we want to return a dummy response
            return {
                Strategy.DUMMY: True,
            }
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

    with logger.logtime("Getting sambot strategy"):
        strategy = asyncio.run(get_strategy())
        logger.debug(strategy)

    # return the first strategy
    for key, value in strategy.items():
        if value:
            return key
    return Strategy.DEFAULT


def resolve_response_strategy(content: str, chat: models.Chat, response_strategy: Strategy):
    """
    Generate a sambot response given the user's input, their chat history,
    and a strategy to use while responding. NOTE: This method will potentially
    perform additional actions, e.g., sending emails, etc. The return type of this function
    is a generator that spits out partially updating `Chat` instances.
    """
    logger.debug(f"Using {response_strategy}...")

    if settings.ENABLE_DUMMY_RESPONSES:
        current_message = ""
        chat.append_assistant(current_message)
        time.sleep(2)
        lorem = """
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus.
            Suspendisse lectus tortor, dignissim sit amet, adipiscing nec, ultricies sed, dolor. Cras
            elementum ultrices diam.
        """.split(" ")
        lorem.sort(key=lambda _: random.random())
        for token in lorem:
            current_message += token + ' '
            chat.messages[len(chat.messages) - 1] = models.Chat.Message(
                content=current_message,
                role=models.Chat.ASSISTANT,
            )
            chat.save()
            yield chat
            time.sleep(0.05)
        return

    if Strategy.DEFAULT == response_strategy:
        # summarize the knowledge-base using gpt3 and inject as system prompt for gpt4.
        with logger.logtime("Summarizing sambot knowledge"):
            summarized_knowledge = openai.get_completion(
                openai.flat_messages(
                    f"""
                    Summarize relevant information using bullet points from the following content to answer the given
                    quesiton. Keep your summary as short as possible. Only respond with "NO INFO" if none of the information
                    available is relevant. Use a single bullet-point if the question is not very specific. \n\n
                    CONTENT: {MEMORIES}. \n\n
                    QUESTION: {content}.
                    """
                ),
                "gpt-3.5-turbo",
            )

        # build system message
        system_message = f"""
            # {PERSONALITY}.\n\n
            # Instructions: Respond to all user messages using the information provided in your knowledge
            as your main source of truth.\n\n
            # Knowledge: {summarized_knowledge}.
            """

    elif Strategy.GREET == response_strategy:
        system_message = f"""
            # Personality: {PERSONALITY}.\n\n
            # Instructions: Respond to the user with a casual greeting, integrating as appropriate with
            the current context of the conversation.
            """

    else:
        logger.error(f"Unsupported strategy: {response_strategy}")
        return

    # stream back partially-updating chat objects
    logger.debug("Streaming sambot message...")
    logger.debug(f'System message: "{system_message}".')
    chat.set_system_message(system_message)
    current_message = ""
    chat.append_assistant(current_message)
    for token in openai.get_completion(
        model="gpt-4-1106-preview",
        stream=True,
        messages=[msg.dict() for msg in chat.messages],
    ):
        current_message += token
        chat.messages[len(chat.messages) - 1] = models.Chat.Message(
            content=current_message,
            role=models.Chat.ASSISTANT,
        )
        chat.save()
        yield chat

