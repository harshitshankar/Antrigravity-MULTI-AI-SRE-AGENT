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

2. KEYWORD SEARCH (fallback when no API key):
   - Counts how many words from your query appear in each document
   - Simpler but still works well for demo purposes
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
                # Modern google-genai library imports
                from google import genai
                from google.genai import types
                import chromadb
                from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
                
                # Initialize the modern Gemini client
                client = genai.Client(api_key=self.api_key)
                
                # ---- Define a custom embedding function using the new SDK ----
               # ---- Define a custom embedding function using the new SDK ----
                class GeminiEmbeddingFunction(EmbeddingFunction):
                    """Custom embedding function to fetch vectors using the modern google-genai SDK."""
                    def __call__(self, input: Documents) -> Embeddings:
                        embeddings = []
                        for text in input:
                            try:
                                # Switched from text-embedding-004 to gemini-embedding-001 with 768 output dimensions
                                result = client.models.embed_content(
                                    model="gemini-embedding-001",
                                    contents=text,
                                    config=types.EmbedContentConfig(output_dimensionality=768)
                                )
                                # Extract numbers array from the new response object structure
                                embeddings.append(result.embeddings[0].values)
                            except Exception as embed_err:
                                print(f"[KEDB] Embedding fetch failed: {embed_err}. Fallback to dummy zero-vector.")
                                embeddings.append([0.0] * 768)
                        return embeddings
                
                # ---- Create the ChromaDB client ----
                chroma_path = os.path.join(os.path.dirname(__file__), "chroma_db")
                self.client = chromadb.PersistentClient(path=chroma_path)
                
                # ---- Create or get the collection ----
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
        """Reads all .md (markdown) files from the KEDB directory."""
        if not os.path.exists(self.kedb_dir):
            os.makedirs(self.kedb_dir, exist_ok=True)
            return

        files = glob.glob(os.path.join(self.kedb_dir, "*.md"))
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = os.path.basename(filepath)
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
        """Adds all loaded documents to the ChromaDB collection via upsert."""
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
        """Searches the KEDB documents using either Vector Search or Keyword Overlap."""
        if not self.documents:
            self.load_documents()

        # ---- Method 1: ChromaDB Vector Search ----
        if not self.use_fallback:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
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
        query_words = set(re.findall(r'\w+', query.lower()))
        scored_docs = []
        
        for doc in self.documents:
            doc_words = set(re.findall(r'\w+', doc["content"].lower()))
            overlap = len(query_words.intersection(doc_words))
            score = overlap / max(len(query_words), 1)
            
            if overlap > 0:
                scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
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