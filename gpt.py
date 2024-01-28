import config
import openai


client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

def stream(conversation, model='gpt-4', **kwargs):
    for chunk in client.chat.completions.create(
        model=model,
        messages=list(conversation),
        stream=True,
        **kwargs,
    ):
        if content := chunk.choices[0].delta.content:
            #print('')
            yield content


def create(prompt=None, messages=None, stream=False, model='gpt-4', **kwargs):
    """
    Handles stream v.s. non-stream creation and prompt v.s. messages creation, while
    still allowing any arbitrary parameters to enter the API call.
    """
    create_function = response_stream if stream else _create_flat
    messages = messages if messages else [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]
    return create_function(model=model, messages=messages)


def _request_completion(*args, **kwargs):
    """
    Create a chat-completion using the OpenAI API.
    """
    try:
        return client.chat.completions.create(*args, **kwargs)
    except openai.APIError as e:
        print('Error generating GPT completion.')


def _create_flat(*args, **kwargs):
    """
    Create a chat-completion and return a "flat" string with the result.
    """
    try:
        return _request_completion(*args, **kwargs).choices[0].message.content
    except Exception as e:
        print('Error parsing GPT completion.')


def response_stream(*args, **kwargs):
    """
    Create a chat-completion stream and return a generator yielding the string results.
    """
    try:
        for chunk in client.chat.completions.create(*args, **kwargs, stream=True):
            if content := chunk.choices[0].delta.content:
                yield content
    except Exception as e:
        raise openai.OpenAIError from e
