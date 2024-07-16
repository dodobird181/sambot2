from __future__ import annotations
from apis.openai import client
from dataclasses import dataclass
from typing import List
import json
import settings
import logger
import os
import math

_logger = logger.get_logger(__name__)


@dataclass
class Embedding:
    """
    A pair of 1. string content and, 2. floating-point vector describing
    the string content in an N-dimensional vector-space.
    """
    content: str
    vector: List[float]

    @staticmethod
    def load_list(path: str) -> List[Embedding]:
        """
        Load a list of embeddings from a JSON file.
        """
        with open(f'../{settings.LOCAL_RESOURCE_DIR}/{path}', 'r') as file:
            _logger.debug(f'Loading embeddings from {settings.LOCAL_RESOURCE_DIR}/{path}..')
            json_embeddings = json.load(file)
            embeddings = [
                Embedding(
                    content=obj['content'],
                    vector=obj['vector'],
                )
                for obj in json_embeddings['embeddings']
            ]
            _logger.debug(f'Loaded {len(embeddings)} embeddings!')
            return embeddings

    @staticmethod
    def save_list(embeddings: List[Embedding], path) -> None:
        """
        Save a list of embeddings to a JSON file.
        """
        os.makedirs(f'../{settings.LOCAL_RESOURCE_DIR}', exist_ok=True)
        with open(f'../{settings.LOCAL_RESOURCE_DIR}/{path}', 'w') as file:
            _logger.debug(f'Saving {len(embeddings)} embeddings to {settings.LOCAL_RESOURCE_DIR}/{path}..')
            json.dump({
                'embeddings': [
                    {
                        'content': e.content,
                        'vector': e.vector,
                    }
                    for e in embeddings
                ],
            }, file)
            _logger.debug(f'Saved!')

    @staticmethod
    def gen(content: str) -> Embedding:
        """
        Generate an embedding from openai given some string content.
        """
        return Embedding(
            content=content,
            vector=(
                client
                .embeddings
                .create(input=content, model="text-embedding-ada-002")
                .data[0]
                .embedding
            ),
        )

    @staticmethod
    def gen_list(content_list: List[str]) -> List[Embedding]:
        embeddings = []
        for i, content in enumerate(content_list):
            embeddings.append(Embedding.gen(content))
            _logger.debug(f'Generated {i}/{len(content_list)} embeddings.')
        return embeddings


@dataclass
class EmbeddingDist:
    """
    A datapoint measuring the floating-point distance between
    two Embedding objects.
    """
    e1: Embedding
    e2: Embedding
    dist: float

    @staticmethod
    def get(e1, e2) -> EmbeddingDist:
        dist = math.sqrt(sum((p - q) ** 2 for p, q in zip(e1.vector, e2.vector)))
        return EmbeddingDist(e1=e1, e2=e2, dist=dist)


def k_nearest(content: str, embeddings: List[Embedding], k: int) -> List[EmbeddingDist]:
    """Get the `k` nearest embeddings to the given `content`."""
    content_embedding = Embedding.gen(content)
    distances = [EmbeddingDist.get(content_embedding, e) for e in embeddings]
    nearest = sorted(distances, key=lambda d: d.dist)[:k]
    _logger.debug(f'Found k-nearest distances: {[n.dist for n in nearest]}')
    return nearest
