from typing import *

import openai

import config

client = openai.OpenAI(api_key=config.OPENAI_API_KEY)


def request(messages, model, stream=False, **kwargs):
    """
    Send a request to chat gpt.
    """

    def streamed_response():
        for chunk in client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs,
        ):
            if content := chunk.choices[0].delta.content:
                yield content

    if stream:
        for chunk in streamed_response():
            yield chunk
    else:
        all_data = "".join(chunk for chunk in streamed_response())
        return all_data


def chat_stream(convo, model="gpt-4", **kwargs):
    """
    TODO: DEPRECATED, REMOVE ME
    Send a chat request to OpenAI and stream back the response.
    This function returns a generator containing string-chunks,
    which eventually compose the entire OpenAI response.
    """
    for chunk in client.chat.completions.create(
        model=model,
        messages=list(convo),
        stream=True,
        **kwargs,
    ):
        if content := chunk.choices[0].delta.content:
            yield content


def chat(convo, model="gpt-4", **kwargs):
    """
    TODO: DEPRECATED, REMOVE ME
    Send a chat request to OpenAI and return a string response.
    """
    return (
        client.chat.completions.create(
            model=model,
            messages=list(convo),
            stream=False,
            **kwargs,
        )
        .choices[0]
        .message.content
    )
