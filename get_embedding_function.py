import openai
from langchain_openai import OpenAIEmbeddings

def get_embedding_function():
    # Use OpenAI's embedding model (e.g., text-embedding-ada-002)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    return embeddings