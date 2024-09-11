import argparse
import requests
import time
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate

from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

# Hugging Face Inference API Information
API_URL = "https://api-inference.huggingface.co/models/openai-community/gpt2-medium"
API_KEY = "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"  # Replace with your actual Hugging Face API key
headers = {"Authorization": f"Bearer {API_KEY}"}

MAX_INPUT_TOKENS = 900  # Adjust based on the model's max token limit minus desired output tokens

def query_huggingface_api(prompt, max_tokens=100, retries=5, delay=10):
    """Send a query to Hugging Face's model inference API with retries and wait_for_model."""
    payload = {
        "inputs": prompt,
        "options": {
            "wait_for_model": True  # Wait for the model if it's not ready
        },
        "parameters": {
            "max_tokens": max_tokens  # Set the maximum number of tokens to generate
        }
    }
    for attempt in range(retries):
        response = requests.post(API_URL, headers=headers, json=payload)
        response_json = response.json()
        
        # Debugging: print the API response
        print(f"API Response: {response_json}")
        
        if isinstance(response_json, dict) and 'error' in response_json:
            if "Model is currently loading" in response_json['error']:
                print(f"Model is loading, retrying in {delay} seconds...")
                time.sleep(delay)  # Wait before retrying
                continue
            else:
                raise Exception(f"Error from Hugging Face API: {response_json['error']}")
        elif isinstance(response_json, list) and all('generated_text' in item for item in response_json):
            # Handle the response if it's a list of dictionaries with 'generated_text'
            return ' '.join(item.get('generated_text', '') for item in response_json)
        else:
            raise Exception("Unexpected response format from Hugging Face API")
    
    raise Exception("Failed to get a response from Hugging Face API after several attempts.")

def truncate_context(context_text, max_length):
    """Truncate the context to ensure it fits within the max length."""
    if len(context_text) > max_length:
        return context_text[-max_length:]  # Truncate to the last max_length tokens
    return context_text

def main():
    # Create CLI.
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    parser.add_argument("--max_tokens", type=int, default=100, help="Maximum number of tokens to generate.")
    args = parser.parse_args()
    query_text = args.query_text
    max_tokens = args.max_tokens
    query_rag(query_text, max_tokens)

def query_rag(query_text: str, max_tokens: int):
    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=5)

    # Combine context for the model
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    context_text = truncate_context(context_text, MAX_INPUT_TOKENS)

    # Format the prompt for Hugging Face model
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # Query the Hugging Face API
    response_text = query_huggingface_api(prompt, max_tokens=max_tokens)

    # Retrieve document sources
    sources = [doc.metadata.get("id", None) for doc, _score in results]
    
    # Print the formatted response and sources
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response.encode('utf-8', errors='replace').decode('utf-8'))
    return response_text

if __name__ == "__main__":
    main()