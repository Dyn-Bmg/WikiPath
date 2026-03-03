""" 
This module provides functionality for ranking candidate pages based on
semantic similarity to a target page description. It uses a pre-trained
SentenceTransformer model to generate embeddings and computes cosine
similarity scores to determine the most relevant pages.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import heapq

def ranker(sentences: list[str], dic: dict[str]) -> list[str]:
    """
    Rank candidate pages by semantic similarity to the target page.

    Args:
        sentences (list[str]): A list of page descriptions with the target page description at index 0
        dic (dict[str]): A dictionary iwth key:value pair of description:page_title

    Returns:
        list[str]: list of 5 page titles most similar to the target in descending order.
    """
    model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only = True)

    embeddings = model.encode(sentences)
    ranking = {}

    for i in range(1,len(sentences)):
        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[i]]
        )
        ranking[dic[sentences[i]]] = similarity[0][0]
    top5 = heapq.nlargest(5, ranking.keys(), key=lambda x: ranking[x])
    return top5