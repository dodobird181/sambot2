from typing import *

from apis.openai import client


def get_completion(messages, model, stream=False, **kwargs):
    """
    Get a 'chat completion' response from openai. If `stream=True`, data
    will be streamed back immediately, otherwise this method will wait
    until all the response data has been generated before returning.
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
        return streamed_response()
    else:
        # collect all data before returning
        all_data = "".join(chunk for chunk in streamed_response())
        return all_data
