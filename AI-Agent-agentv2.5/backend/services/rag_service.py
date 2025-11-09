import json
import os
import sys
import chromadb
from sentence_transformers import SentenceTransformer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log

# --- Constants ---
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'scraped_alerts.json')
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'chroma_db')
EMBEDDING_MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
COLLECTION_NAME = "adcc_alerts"

def _load_and_chunk_data():
    log.info(f"Loading data from: {DATA_FILE_PATH}")
    try:
        with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
            articles = json.load(f)
    except FileNotFoundError:
        log.error(f"Data file not found at {DATA_FILE_PATH}. Please run the scraper first.")
        return [], []

    chunks, metadatas = [], []
    for article in articles:
        content = article.get('content')
        if not content: continue
        
        paragraphs = content.split('\n')
        for para in paragraphs:
            if len(para.strip()) > 20:
                chunks.append(para.strip())
                metadatas.append({
                    'title': article.get('title', 'N/A'),
                    'link': article.get('link', 'N/A'),
                    'date': article.get('date', 'N/A')
                })
    log.info(f"Successfully loaded and chunked data into {len(chunks)} paragraphs.")
    return chunks, metadatas

def build_and_persist_db():
    """
    Build the vector database: load data -> embed -> store to ChromaDB.
    This function only needs to run once when data updates occur.
    """
    log.info("--- Starting to build the Vector DB ---")
    
    # Step 1: Load and chunk the data
    chunks, metadatas = _load_and_chunk_data()
    if not chunks:
        log.error("No chunks to process. Aborting DB build.")
        return

    # Step 2: Initialize ChromaDB client and embedding model
    # PersistentClient will persist data to disk
    client = chromadb.PersistentClient(path=DB_PATH)
    log.info(f"ChromaDB client initialized. DB will be saved to: {DB_PATH}")
    
    # This step will automatically download the model from Hugging Face (first run may take longer)
    log.info(f"Loading embedding model: '{EMBEDDING_MODEL_NAME}'...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    log.info("Embedding model loaded successfully.")

    # Step 3: Create or get a collection
    # get_or_create_collection can be safely re-run multiple times
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    log.info(f"Collection '{COLLECTION_NAME}' ready.")

    # Step 4: Embed and store data
    # To avoid processing too much at once, we do it in batches
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        log.info(f"Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}...")

        # Generate embeddings
        embeddings = embedding_model.encode(batch_chunks).tolist()

        # Generate unique IDs
        ids = [f"id_{i+j}" for j in range(len(batch_chunks))]

        # Add data to the collection
        collection.add(
            embeddings=embeddings,
            documents=batch_chunks,
            metadatas=batch_metadatas,
            ids=ids
        )
    
    log.info("--- Vector DB build complete! ---")
    log.info(f"Total documents indexed: {collection.count()}")

def query_db(query_text, n_results=3):
    """
    Query the vector database and return the top-n most relevant results.
    """
    log.info(f"--- Querying DB with: '{query_text}' ---")
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # Convert the query text into an embedding
    query_embedding = embedding_model.encode(query_text).tolist()

    # Execute the query
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results

if __name__ == "__main__":
    # When run directly, perform the following actions:

    # 1. Build the database (safe to re-run but will rebuild the index)
    build_and_persist_db()

    # 2. Perform a test query to verify DB functionality
    test_query = "HSBC points expiry"
    query_results = query_db(test_query)

    print("\n--- Test Query Results ---")
    if query_results and query_results['documents']:
        for i, doc in enumerate(query_results['documents'][0]):
            print(f"Result {i+1}:")
            try:
                print(f"  Content: {doc[:150]}...") # print a snippet of content
            except UnicodeEncodeError:
                print(f"  Content: [Content contains non-ASCII characters]")
            try:
                print(f"  Metadata: {query_results['metadatas'][0][i]}")
            except UnicodeEncodeError:
                print(f"  Metadata: [Metadata contains non-ASCII characters]")
            print(f"  Similarity Score: {query_results['distances'][0][i]}")
    else:
        print("No results found.")