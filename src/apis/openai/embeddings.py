from apis.openai import client


def get_embedding(input: str):
    """
    Get a vector embedding response from openai.
    """
    return (
        client.embeddings.create(input=input, model="text-embedding-ada-002")
        .data[0]
        .embedding
    )
