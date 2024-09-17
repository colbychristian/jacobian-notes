import os
from langchain_community.vectorstores import Chroma
from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"
DATA_PATH = "data"

def remove_documents(files_to_remove):
    # Load existing Chroma database
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function())

    # Get current file list in the data folder
    data_files = set(os.listdir(DATA_PATH))

    # Remove the specified files
    for file_name in files_to_remove:
        file_path = os.path.join(DATA_PATH, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed {file_path}")

    # Update database to remove documents no longer present
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])

    # Remove documents whose source file is no longer in the data folder
    documents_to_remove = [
        doc_id for doc_id in existing_ids
        if os.path.basename(doc_id.split(":")[0]) not in data_files
    ]

    if documents_to_remove:
        db.delete(ids=documents_to_remove)
        db.persist()
        print(f"Removed {len(documents_to_remove)} documents from Chroma DB")
    else:
        print("No documents to remove from the database.")
