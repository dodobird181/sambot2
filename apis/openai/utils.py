import asyncio
import math

import apis.openai as openai


def best_similarity(user_input, *sentences):
    """
    Calculate the best similarity (Euclidean distance) between
    the user input and a list of sentences using openai's embeddings endpoint.
    """

    def euclidean_distance(vec1, vec2):
        return math.sqrt(sum((p - q) ** 2 for p, q in zip(vec1, vec2)))

    async def best():
        embeddings = await asyncio.gather(
            # get all sentence embeddings the same time
            asyncio.to_thread(openai.get_embedding, user_input),
            *[asyncio.to_thread(openai.get_embedding, sentence) for sentence in sentences]
        )
        user_embedding = embeddings[0]
        sentence_embeddings = embeddings[1:]

        # min distance between user_input and any of the sentences
        return min(euclidean_distance(user_embedding, e) for e in sentence_embeddings)

    # await the return
    return asyncio.run(best())


def flat_messages(text):
    """
    Transform a string of text into a list of message dictionaries
    containing a single user message with the given text.
    """
    return [{"role": "user", "content": text}]
