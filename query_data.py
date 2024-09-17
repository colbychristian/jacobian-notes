import openai
from langchain_community.vectorstores import Chroma
from concurrent.futures import ThreadPoolExecutor
import tiktoken
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from get_embedding_function import get_embedding_function
import os

CHROMA_PATH = "chroma"
PROMPT_TEMPLATE = """
Using the data in CHROMA_PATH, create study notes for each concept and include the following sections: "Concept Explanation", "Key Terms and Notation", "Usages and Examples", "Practice Questions", "Pre-requisite Concepts", and "References" (the references are provided by the meta data created by the RAG).

---

Context: {context}

---

Include the metadata reference for this content: {metadata}.
"""

# Set your OpenAI API key
openai.api_key = "sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Replace with your OpenAI API key

MAX_INPUT_TOKENS = 900  # Adjust based on the model's max token limit minus desired output tokens

def call_openai_api(chunk, metadata):
    """Send a query to OpenAI's ChatCompletion API with metadata."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert assistant who creates structured study notes based on provided context."},
                {"role": "user", "content": PROMPT_TEMPLATE.format(context=chunk, metadata=metadata)},
            ],
            max_tokens=500,  # Adjust max tokens if necessary
            n=1,
            stop=None,
            temperature=0.5,
        )
        return response.choices[0]['message']['content'].strip()
    except Exception as e:
        print(f"Error during API call: {e}")
        return ""

def split_into_chunks(text, tokens=500):
    """Split the input text into chunks based on token count."""
    encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')
    words = encoding.encode(text)
    chunks = []
    for i in range(0, len(words), tokens):
        chunks.append(encoding.decode(words[i:i + tokens]))
    return chunks

def process_chunks(context_chunks):
    """Process text chunks in parallel and query OpenAI API with metadata."""
    with ThreadPoolExecutor() as executor:
        responses = list(executor.map(lambda chunk_data: call_openai_api(chunk_data[0], chunk_data[1]), context_chunks))
    return ' '.join(responses)

def save_to_pdf(text, output_path):
    """Save the given text to a PDF file."""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    c.drawString(72, height - 72, text)
    c.save()

def generate_study_notes():
    """Generate study notes based on all documents in the vector store and save as PDF."""
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    results = db._collection.get(include=['documents', 'metadatas'])  # Fetch all documents and their metadata
    
    context_chunks = []
    for doc, metadata in zip(results['documents'], results['metadatas']):
        chunks = split_into_chunks(doc)
        for chunk in chunks:
            context_chunks.append((chunk, metadata.get("id", "unknown reference")))

    response_text = process_chunks(context_chunks)
    formatted_response = f"Study Notes:\n{response_text}\n"

    pdf_path = "notes/study_notes.pdf"  # Specify the path to save the PDF
    save_to_pdf(formatted_response, pdf_path)
    print(f"Study notes saved to {pdf_path}")

if __name__ == "__main__":
    generate_study_notes()