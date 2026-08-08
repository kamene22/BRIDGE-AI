import os
from typing import List, Dict, Any
import chromadb
from dotenv import load_dotenv

# Import llm_provider
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from llm_provider.provider import GeminiProvider

load_dotenv()

class RetrievalEngine:
    def __init__(self):
        self.chroma_db_path = os.getenv("CHROMA_DB_PATH", "/home/monic/projects/BridgeAI/db")
        self.collection_name = "bridge_ai_corpus"
        
        # Connect to existing ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_db_path)
        self.collection = self.chroma_client.get_collection(name=self.collection_name)
        
        # Initialize Gemini Provider for query embedding
        self.provider = GeminiProvider()

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Embeds the query and searches the ChromaDB collection for the top_k most similar chunks.
        Returns a list of structured results.
        """
        # Embed the query
        query_embeddings = self.provider.embed_texts([query], task_type="retrieval_query")
        if not query_embeddings:
            return []
            
        query_vector = query_embeddings[0]
        
        # Query ChromaDB collection
        # Note: ChromaDB returns distance scores (L2 distance by default, smaller is more similar)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        
        formatted_results = []
        if not results or not results['ids'] or not results['ids'][0]:
            return []
            
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "distance": results['distances'][0][i],
                "metadata": results['metadatas'][0][i],
                "document": results['documents'][0][i]
            })
            
        return formatted_results

def test_retrieval_queries():
    print("Initializing Retrieval Engine...")
    engine = RetrievalEngine()
    
    test_queries = [
        "How long is the probation period legally capped at in Kenya?",
        "What are the red flags of a job scam regarding payment?",
        "What are the mandatory deductions like SHA and NSSF on my first payslip?",
        "What is the dress code for a bank job vs a startup?"
    ]
    
    print("\n" + "="*80)
    print("RUNNING RETRIEVAL VALIDATION TESTS")
    print("="*80 + "\n")
    
    for idx, query in enumerate(test_queries):
        print(f"Test Query {idx+1}: '{query}'")
        print("-" * 50)
        
        results = engine.retrieve(query, top_k=3)
        if not results:
            print("No relevant chunks retrieved.")
        else:
            for rank, res in enumerate(results):
                meta = res['metadata']
                source = meta.get('source', 'Unknown')
                title = meta.get('title', 'Unknown')
                chunk_idx = meta.get('chunk_index', 'Unknown')
                line_info = ""
                if 'start_line' in meta and 'end_line' in meta:
                    line_info = f", Lines {meta['start_line']}-{meta['end_line']}"
                elif 'page' in meta:
                    line_info = f", Page {meta['page']}"
                    
                print(f"[{rank+1}] Source: {source} ({title}{line_info}) | Distance: {res['distance']:.4f}")
                snippet = res['document'][:200].replace('\n', ' ')
                print(f"    Snippet: {snippet}...")
                print()
        print("="*80 + "\n")

if __name__ == "__main__":
    test_retrieval_queries()
