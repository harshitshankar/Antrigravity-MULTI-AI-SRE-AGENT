"""
=============================================================================
FILE: rag/vector_store.py
PURPOSE: Manages the KEDB (Known Error Database) — loading markdown articles,
         indexing them for search, and finding the most relevant ones
         when an incident occurs.
=============================================================================

TWO SEARCH MODES:
1. VECTOR SEARCH (when GEMINI_API_KEY is set):
   - Uses ChromaDB (a vector database) + Google Gemini Embeddings
   - Converts text into "embeddings" (lists of numbers representing meaning)
   - Finds documents with similar meaning, not just matching words
   - Example: searching "connection pool full" would find an article about
     "HikariPool exhausted" even though the words are different!

2. KEYWORD SEARCH (fallback when no API key):
   - Counts how many words from your query appear in each document
   - Simpler but still works well for demo purposes
   - No internet or API key required

WHAT IS ChromaDB?
ChromaDB is a "vector database" — a special database designed to store
text as numbers (embeddings) and find similar text quickly.
Think of it like Google search but for your own documents.

WHAT ARE EMBEDDINGS?
Embeddings convert text into a long list of numbers (e.g., 768 numbers).
Similar texts get similar numbers. This lets us do "semantic search" —
finding documents by meaning rather than exact word matching.
=============================================================================
"""

import os
import glob  # For finding files matching a pattern (e.g., *.md)
import re
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class KEDBIndex:
    """
    Manages the indexing and search of Known Error Database (KEDB) documents.
    Uses ChromaDB + Google Gemini Embeddings if configured, otherwise falls back
    to a robust keyword-overlap search to operate fully offline or without API keys.
    """
    
    def __init__(self, kedb_dir: str):
        """
        Initialize the KEDB index.
        
        Args:
            kedb_dir: Path to the folder containing .md files (e.g., "kedb/")
        """
        self.kedb_dir = kedb_dir
        self.api_key = os.getenv("GEMINI_API_KEY")  # Check if we have an API key
        self.use_fallback = True    # Start assuming we need fallback (keyword search)
        self.documents = []         # Will store all loaded documents
        
        # ---- Load all markdown files into memory ----
        self.load_documents()
        
        # ---- Try to set up ChromaDB with Gemini Embeddings ----
        if self.api_key:
            try:
                import google.generativeai as genai
                import chromadb
                # EmbeddingFunction is an interface ChromaDB uses to convert text → numbers
                from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
                
                # Configure Gemini with our API key
                genai.configure(api_key=self.api_key)
                
                # ---- Define a custom embedding function ----
                # ChromaDB needs a function that converts text into number arrays.
                # We create one that uses Google's Gemini embedding model.
                class GeminiEmbeddingFunction(EmbeddingFunction):
                    """Custom embedding function to fetch vectors using Gemini Embeddings API."""
                    def __call__(self, input: Documents) -> Embeddings:
                        embeddings = []
                        for text in input:
                            try:
                                # This API call converts text → list of 768 numbers
                                result = genai.embed_content(
                                    model="models/text-embedding-004",  # Google's embedding model
                                    content=text,
                                    task_type="retrieval_document"  # Optimized for document search
                                )
                                embeddings.append(result['embedding'])
                            except Exception as embed_err:
                                print(f"[KEDB] Embedding fetch failed: {embed_err}. Fallback to dummy zero-vector.")
                                # If the API fails, use a dummy vector (all zeros)
                                embeddings.append([0.0] * 768)
                        return embeddings
                
                # ---- Create the ChromaDB client ----
                # PersistentClient saves the database to disk so we don't have to
                # re-embed documents every time the app starts
                chroma_path = os.path.join(os.path.dirname(__file__), "chroma_db")
                self.client = chromadb.PersistentClient(path=chroma_path)
                
                # ---- Create or get the collection ----
                # A "collection" in ChromaDB is like a table in a regular database
                self.collection = self.client.get_or_create_collection(
                    name="kedb_collection",
                    embedding_function=GeminiEmbeddingFunction()
                )
                
                # ---- Index all documents ----
                self.populate_chroma()
                self.use_fallback = False  # ChromaDB is ready — no fallback needed!
                print("[KEDB] Vector DB initialized successfully using Gemini Embeddings.")
                
            except Exception as e:
                print(f"[KEDB] Could not initialize ChromaDB: {e}. Falling back to keyword search.")
                self.use_fallback = True
        else:
            print("[KEDB] GEMINI_API_KEY not found. Using keyword search fallback.")
            self.use_fallback = True

    def load_documents(self):
        """
        Reads all .md (markdown) files from the KEDB directory.
        Each file becomes a document with an ID, title, content, and path.
        """
        if not os.path.exists(self.kedb_dir):
            os.makedirs(self.kedb_dir, exist_ok=True)
            return

        # glob.glob finds all files matching a pattern
        # os.path.join(kedb_dir, "*.md") matches all markdown files
        files = glob.glob(os.path.join(self.kedb_dir, "*.md"))
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = os.path.basename(filepath)  # e.g., "db_pool_exhausted.md"
                    # Create a human-readable title from the filename
                    title = filename.replace(".md", "").replace("_", " ").title()
                    self.documents.append({
                        "id": filename,
                        "title": title,
                        "content": content,
                        "path": filepath
                    })
            except Exception as e:
                print(f"[KEDB] Error loading {filepath}: {e}")

    def populate_chroma(self):
        """
        Adds all loaded documents to the ChromaDB collection.
        ChromaDB will automatically convert each document's content into
        embeddings using our GeminiEmbeddingFunction.
        
        'upsert' = insert if new, update if already exists
        """
        if len(self.documents) > 0:
            ids = [doc["id"] for doc in self.documents]
            contents = [doc["content"] for doc in self.documents]
            metadatas = [{"title": doc["title"], "path": doc["path"]} for doc in self.documents]
            self.collection.upsert(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )

    def search(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Searches the KEDB documents for matches to the query.
        
        Args:
            query: The incident description to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents with scores
        """
        # If no documents exist, try loading them
        if not self.documents:
            self.load_documents()

        # ---- Method 1: ChromaDB Vector Search ----
        if not self.use_fallback:
            try:
                # ChromaDB converts our query into an embedding (numbers)
                # and finds the documents with the most similar embeddings
                results = self.collection.query(
                    query_texts=[query],    # What we're searching for
                    n_results=limit          # How many results we want
                )
                formatted = []
                if results and 'documents' in results and results['documents'] and results['documents'][0]:
                    for i in range(len(results['documents'][0])):
                        formatted.append({
                            "id": results['ids'][0][i],
                            "title": results['metadatas'][0][i].get("title", ""),
                            "content": results['documents'][0][i],
                            "score": float(results['distances'][0][i]) if 'distances' in results and results['distances'] else 0.0,
                            "method": "Vector Search"
                        })
                    return formatted
            except Exception as e:
                print(f"[KEDB] Chroma search query failed: {e}. Executing keyword-based search fallback.")

        # ---- Method 2: Keyword Overlap Search (Fallback) ----
        # This is simpler but effective: count how many words from the query
        # appear in each document, and rank by that count
        
        # Split query into individual words (lowercase)
        # re.findall(r'\w+', ...) extracts all "word" characters
        query_words = set(re.findall(r'\w+', query.lower()))
        scored_docs = []
        
        for doc in self.documents:
            # Get all words from the document
            doc_words = set(re.findall(r'\w+', doc["content"].lower()))
            
            # Count how many query words appear in the document
            overlap = len(query_words.intersection(doc_words))
            
            # Calculate a score: fraction of query words found in the document
            score = overlap / max(len(query_words), 1)  # max() prevents division by zero
            
            if overlap > 0:  # Only include documents with at least 1 matching word
                scored_docs.append((score, doc))
        
        # Sort by score (highest first)
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Return the top 'limit' results
        results = []
        for score, doc in scored_docs[:limit]:
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "score": float(score),
                "method": "Keyword Matching"
            })
            
        return results


# ---- Self-Testing Block ----
# This code only runs if you execute this file directly:
#   python rag/vector_store.py
# It does NOT run when this file is imported by other files
if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    sample_kedb_dir = os.path.abspath(os.path.join(current_dir, "..", "kedb"))
    print(f"Loading KEDB from: {sample_kedb_dir}")
    index = KEDBIndex(sample_kedb_dir)
    print("Searching for 'HikariPool exhausted'...")
    search_results = index.search("HikariPool exhausted")
    for doc in search_results:
        print(f"\nMatch Found: {doc['title']} (Score: {doc['score']:.4f}, Method: {doc['method']})")
        print(f"Content Preview:\n{doc['content'][:150]}...")
