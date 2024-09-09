from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_aws import BedrockEmbeddings


def get_embedding_function():
    #embeddings = BedrockEmbeddings(
        #credentials_profile_name="default", region_name="Global"
    #)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings
