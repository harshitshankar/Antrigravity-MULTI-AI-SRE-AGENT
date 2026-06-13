"""
=============================================================================
FILE: agents/RAG_agent.py
PURPOSE: The FOURTH agent in the pipeline. It searches the Known Error
         Database (KEDB) to find past incidents similar to the current one,
         along with their documented fixes.
=============================================================================

WHAT IS RAG?
RAG = Retrieval Augmented Generation
It's a technique where we FIRST search a knowledge base for relevant documents,
THEN give those documents to the AI so it can generate a better answer.

Example:
  User says: "HikariPool exhausted"
  RAG searches KEDB → finds "db_pool_exhausted.md" article
  AI reads the article → gives specific fix: "Increase pool size to 150"

Without RAG, the AI would have to guess the fix from general knowledge.
With RAG, it gives you YOUR company's specific documented procedure.

WHAT IS KEDB?
KEDB = Known Error Database
It's a collection of articles describing past problems and their solutions.
Think of it like a FAQ or troubleshooting guide for your systems.
=============================================================================
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Import our custom vector store that handles the KEDB search
# This is defined in rag/vector_store.py
from rag.vector_store import KEDBIndex

load_dotenv()


def run_rag_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAG/KEDB Agent Node:
    Queries the vector database or keyword-index to locate runbooks
    matching the incident description, summarizing remediation steps.
    """
    print("\n[Node: RAG Agent] Querying KEDB...")
    query = state.get("query", "")  # The original incident description
    
    # ---- Step 1: Initialize the KEDB search index ----
    # This creates the ChromaDB vector index (or falls back to keyword search)
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    kedb_dir = os.path.join(project_dir, "kedb")
    
    index = KEDBIndex(kedb_dir)  # Load and index all .md files in kedb/ folder
    
    # ---- Step 2: Search for matching KEDB articles ----
    # "limit=2" means return the top 2 most relevant articles
    results = index.search(query, limit=2)
    print(f"[RAGAgent] Located {len(results)} matching entries in KEDB.")
    
    summary = ""
    
    # ---- Step 3: Summarize the search results (AI or fallback) ----
    if results:
        api_key = os.getenv("GEMINI_API_KEY")
        
        if api_key:
            try:
                # Build a text block containing all matched documents
                docs_joined = ""
                for idx, doc in enumerate(results):
                    docs_joined += f"--- Match #{idx+1}: {doc['title']} (Source: {doc['id']}) ---\n{doc['content']}\n\n"
                
                prompt = f"""
                You are an SRE KEDB/RAG Agent.
                The user reported this incident: "{query}"
                
                We found the following matching Known Error Database (KEDB) runbooks:
                
                {docs_joined}
                
                Analyze these KEDB documents in relation to the reported incident and summarize:
                1. Which KEDB entries are most relevant and why.
                2. The recommended resolution steps from the relevant runbooks.
                
                Keep your response clear, structured, and concise.
                """
                from utils.gemini_helper import generate

                # CHANGE THIS LINE: Assign directly to summary
                summary = generate(prompt).strip()
         
                
            except Exception as e:
                print(f"[RAGAgent] Gemini API error: {e}. Falling back to standard summary.")
                api_key = None
        
        # ---- Fallback: Format the raw search results as markdown ----
        if not api_key:
            summary = "### Known Error Database (KEDB) Runbook Recommendations\n"
            summary += f"Performed search for reference documents matching: *\"{query}\"*\n\n"
            for doc in results:
                summary += f"#### [{doc['title']}](file:///C:/Users/ravi3_3e8ym6i/.gemini/antigravity/scratch/enterprise-ai-sre/kedb/{doc['id']})\n"
                summary += f"- **Match Method**: {doc['method']} (score: {doc['score']:.2f})\n"
                summary += f"- **Key Recommendations**:\n"
                # Indent and quote the document content
                content_indented = "\n".join([f"  > {line}" for line in doc['content'].split("\n") if line.strip()])
                summary += content_indented + "\n\n"
    else:
        summary = "No matching entries found in the Known Error Database (KEDB) for this query."
    
    # ---- Step 4: Return updates to the state ----
    return {
        "rag_results": results,    # Raw search results (list of dicts)
        "rag_summary": summary,     # Human-readable summary of recommendations
        "current_step": "rag"       # Track progress
    }
