import os
import json
import asyncio
from sqlalchemy.orm import Session
from backend.app.database import session, models
from backend.app.retrieval import hybrid, chroma

# Simple curated evaluation dataset
# In a real environment, this would load from a JSON/JSONL file curated by humans.
EVAL_DATASET = [
    {
        "query": "What is Aditya Maurya's LinkedIn ID?",
        "expected_document": "Resume.pdf"
    },
    {
        "query": "What are Aditya's key skills?",
        "expected_document": "Resume.pdf"
    }
]

def evaluate_retrieval():
    print("Starting Retrieval Evaluation...")
    db = session.SessionLocal()
    
    try:
        results = []
        for item in EVAL_DATASET:
            query = item["query"]
            expected_doc = item["expected_document"]
            
            # Hybrid search with Reranker
            hybrid_res = hybrid.hybrid_search(query, db, top_k=5)
            
            # Simple binary success metrics (Recall@5)
            hit = any(expected_doc in res['metadata']['source'] for res in hybrid_res)
            
            results.append({
                "query": query,
                "hit": hit,
                "top_result": hybrid_res[0]['metadata']['source'] if hybrid_res else None
            })
            
        success_rate = sum(1 for r in results if r["hit"]) / len(results) if results else 0
        
        print("\n=== EVALUATION REPORT ===")
        print(f"Total Queries Evaluated: {len(results)}")
        print(f"Recall@5 (Hybrid + Reranker): {success_rate * 100:.2f}%\n")
        
        for r in results:
            status = "PASS" if r["hit"] else "FAIL"
            print(f"[{status}] Query: {r['query']}")
            
        # Write report
        with open("retrieval_evaluation.json", "w") as f:
            json.dump({"recall_at_5": success_rate, "details": results}, f, indent=2)
            
        print("\nEvaluation complete. Report saved to retrieval_evaluation.json")
            
    finally:
        db.close()

if __name__ == "__main__":
    # Chroma needs async loop to be active if using some async features in backend, but here it's sync.
    evaluate_retrieval()
