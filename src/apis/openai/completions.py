from apis.openai import client
import asyncio
from typing import List, Dict, Any, Generator, Union


def get_completion(
    messages: List[Dict[str, Any]], model: str, stream: bool = False, **kwargs
) -> Union[Generator[str, None, None], str]:
    """
    Get a 'chat completion' response from OpenAI. If `stream=True`, data
    will be streamed back immediately; otherwise, this method will wait
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
        return "".join(streamed_response())


# Asynchronous method using asyncio and OpenAI API
async def async_get_completion(
    messages: List[Dict[str, Any]], model: str, **kwargs
) -> str:
    """
    Async function for getting a chat completion from OpenAI.
    Returns the entire response as a string.
    """
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, get_completion, messages, model, False, **kwargs
    )
    return response
