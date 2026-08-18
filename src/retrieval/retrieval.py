import os
import sys

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

import chromadb
try:
    import chromadb.telemetry.product.posthog
    chromadb.telemetry.product.posthog.Posthog.capture = lambda *args, **kwargs: None
    chromadb.telemetry.product.posthog.Posthog.start = lambda *args, **kwargs: None
    chromadb.telemetry.product.posthog.Posthog.stop = lambda *args, **kwargs: None
except Exception:
    pass

try:
    import chromadb.telemetry.events as _events
    _events.ClientStartEvent = lambda *args, **kwargs: None
    _events.ClientCreateCollectionEvent = lambda *args, **kwargs: None
    _events.CollectionAddEvent = lambda *args, **kwargs: None
    _events.CollectionQueryEvent = lambda *args, **kwargs: None
except Exception:
    pass
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import llm_provider
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from llm_provider.provider import GeminiProvider

load_dotenv()

from concurrent.futures import ThreadPoolExecutor

class RetrievalEngine:
    def __init__(self):
        default_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "db"))
        self.chroma_db_path = os.getenv("CHROMA_DB_PATH", default_db)
        
        # Connect to ChromaDB with telemetry disabled
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_db_path,
            settings=chromadb.config.Settings(anonymized_telemetry=False)
        )
        
        # Connect to Dual Multi-Index Collections (REAPER Architecture)
        try:
            self.legal_collection = self.chroma_client.get_collection("kenya_employment_act_index")
            self.handbook_collection = self.chroma_client.get_collection("kenya_career_handbook_index")
            self.has_multi_index = True
        except Exception:
            try:
                self.collection = self.chroma_client.get_collection("bridge_ai_corpus")
                self.has_multi_index = False
            except Exception:
                self.legal_collection = self.chroma_client.get_or_create_collection("kenya_employment_act_index")
                self.handbook_collection = self.chroma_client.get_or_create_collection("kenya_career_handbook_index")
                self.collection = self.chroma_client.get_or_create_collection("bridge_ai_corpus")
                self.has_multi_index = True
        
        # Initialize Gemini Provider for query embedding
        self.provider = GeminiProvider()

        # Adaptive Neighbor Retrieval Feature Flag
        self.enable_neighbor_retrieval = os.getenv("ENABLE_NEIGHBOR_RETRIEVAL", "true").lower() == "true"
        self._neighbor_retriever = None

    def _init_neighbor_retriever(self):
        """Lazy-initializes in-memory neighbor retriever lookup map."""
        if self._neighbor_retriever is None:
            try:
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                from evaluation.adaptive_neighbor_retriever import AdaptiveNeighborRetriever
                all_chunks = []
                target_coll = self.collection if not self.has_multi_index else self.legal_collection
                res = target_coll.get(include=["documents", "metadatas"])
                if res and res.get("ids"):
                    for cid, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
                        all_chunks.append({"id": cid, "document": doc, "metadata": meta})
                if self.has_multi_index:
                    res_h = self.handbook_collection.get(include=["documents", "metadatas"])
                    if res_h and res_h.get("ids"):
                        for cid, doc, meta in zip(res_h["ids"], res_h["documents"], res_h["metadatas"]):
                            all_chunks.append({"id": cid, "document": doc, "metadata": meta})
                self._neighbor_retriever = AdaptiveNeighborRetriever(all_chunks)
            except Exception as e:
                print(f"[Neighbor Retriever Warning] Failed to build neighbor map: {e}")

    def _query_single_collection(self, collection, query_vector: List[float], top_k: int, distance_threshold: float) -> List[Dict[str, Any]]:
        try:
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k
            )
            formatted = []
            if results and results.get('ids') and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    dist = results['distances'][0][i]
                    if dist <= distance_threshold:
                        formatted.append({
                            "id": results['ids'][0][i],
                            "distance": dist,
                            "metadata": results['metadatas'][0][i],
                            "document": results['documents'][0][i]
                        })
            return formatted
        except Exception as e:
            print(f"[MultiIndex Search Warning] Sub-index search error: {e}")
            return []

    def retrieve(self, query: str, top_k: int = 5, distance_threshold: float = 0.75) -> List[Dict[str, Any]]:
        """
        Executes Multi-Index Vector Search across Legal and Career Handbook indexes sequentially.
        Adaptively expands adjacent chunks (N±1) if statutory or boundary triggers fire.
        """
        if top_k <= 0:
            return []

        try:
            query_embeddings = self.provider.embed_texts([query], task_type="retrieval_query")
            if not query_embeddings:
                return []
            query_vector = query_embeddings[0]

            if not self.has_multi_index:
                base_hits = self._query_single_collection(self.collection, query_vector, top_k, distance_threshold)
            else:
                legal_hits = self._query_single_collection(self.legal_collection, query_vector, 2, distance_threshold)
                handbook_hits = self._query_single_collection(self.handbook_collection, query_vector, 2, distance_threshold)
                merged = legal_hits + handbook_hits
                merged.sort(key=lambda x: x["distance"])
                base_hits = merged[:top_k]

            # Apply Adaptive Neighbor Retrieval if enabled
            if self.enable_neighbor_retrieval and base_hits:
                self._init_neighbor_retriever()
                if self._neighbor_retriever:
                    expanded_hits, _ = self._neighbor_retriever.retrieve_adaptive(query, base_hits, mode="Adaptive_N_pm_1")
                    # Ensure formatted hit structures preserve distance metadata
                    final_hits = []
                    seen_ids = set()
                    for chunk in expanded_hits:
                        cid = chunk.get("id", "")
                        if cid not in seen_ids:
                            seen_ids.add(cid)
                            final_hits.append({
                                "id": cid,
                                "distance": chunk.get("distance", 0.0),
                                "metadata": chunk.get("metadata", {}),
                                "document": chunk.get("document", "")
                            })
                    return final_hits

            return base_hits

        except Exception as e:
            print(f"[Retrieval Fallback Warning] Vector search failed: {e}")
            return []

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
