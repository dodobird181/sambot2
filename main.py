import file
import config
import gpt
from messages import Message, SystemMessage, UserMessage, BotMessage, Conversation

c = Conversation(system=SystemMessage('You are a helpful assistant.'))
c.append(UserMessage(content='Hello world from user!'))
c.latest_message(SystemMessage)
print(c)
exit(0)

"""
This is what an API request flow should look like for sambot...
    1. user request containing content and an optional conversation id;
    2. create new and save, or load existing, conversation from database;
    3. send a request to chat GPT using the conversation;
    4. as the request resolves, package and send back conversation json objects to the client;
    5. when the request is finished resolving, save the conversation as a json object using the
        same encoding method as exporting the json object to the client (maybe think about security).
    6. done!
"""

print('reading data...')
bot_memories = file.read(config.MEMORIES_FILEPATH)
bot_personality = file.read(config.PERSONALITY_FILEPATH)



def call_bot(user_prompt: str, messages: Messages, bot_personality: str):
    """
    Submit a user_prompt to Sambot and update the given messages object
    with the user_prompt and the bot's response. TODO: Decide if this function
    will also perform bot-side effects like sending emails.
    """

    # extract relevant info to answer the prompt
    extracted_info = gpt.create(
        model='gpt-3.5-turbo',
        prompt=f'''
            Please extract and summarize using bullet points any relevant information in: "{bot_memories}"
            to answer the following user quesiton: "{user_prompt}". Respond with only a bullet-point saying
            there is no information if no relevant information exists to answer the question, or if the question
            seems unintelligable.
        ''',
    )

    # append the user_prompt to the messages and update the system data
    messages.append({"role": "user", "content": user_prompt})
    messages.set_system_data(f'''{bot_personality}
        Please answer any questions assuming you only know the following information: {extracted_info}
    ''')

    # stream GPT4's response
    # TODO: gpt.create doesn't work here even though i had originally meant for it to.
    # this is because `create` waits for `_create_stream` to compute everything before
    # returning and I can't figure out how to yeild on the non-streaming calls. I think
    # i might just split these out into two separate functions...
    response_stream = gpt._create_stream(messages=messages.all(), model='gpt-4')

    response_flat = ''
    for token in response_stream:
        response_flat += token
        print(token, end='')

    messages.append({'role': 'assistant', 'content': response_flat})

messages = Messages()
while True:
    user_prompt = input()
    call_bot(user_prompt, messages, bot_personality)
