import config
import openai


client = openai.OpenAI(api_key=config.OPENAI_API_KEY)


def create(prompt=None, messages=None, stream=False, model='gpt-4', **kwargs):
    """
    Handles stream v.s. non-stream creation and prompt v.s. messages creation, while
    still allowing any arbitrary parameters to enter the API call.
    """
    create_function = _create_stream if stream else _create_flat
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


def _create_stream(*args, **kwargs):
    """
    Create a chat-completion stream and return a generator yielding the string results.
    """
    try:
        for chunk in _request_completion(*args, stream=True, **kwargs):
            if content := chunk.choices[0].delta.content:
                yield content
    except Exception as e:
        print('Error parsing GPT completion stream.')
