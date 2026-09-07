import os
import json
from sqlalchemy.orm import Session
from backend.app.database import session, models
from backend.app.retrieval import hybrid, chroma

# Simple curated evaluation dataset
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

def calculate_metrics(results_list, expected_doc):
    """Calculate Recall@5, Precision@5, and Reciprocal Rank for a single query."""
    hits = [1 if expected_doc in res['metadata']['source'] else 0 for res in results_list[:5]]
    
    recall_at_5 = 1 if sum(hits) > 0 else 0
    precision_at_5 = sum(hits) / 5.0
    
    rr = 0.0
    for rank, hit in enumerate(hits, 1):
        if hit:
            rr = 1.0 / rank
            break
            
    return recall_at_5, precision_at_5, rr

def evaluate_retrieval():
    print("Starting Full Retrieval Evaluation...")
    db = session.SessionLocal()
    
    configs = {
        "Vector-only": [],
        "BM25-only": [],
        "Hybrid RRF": [],
        "Hybrid + CrossEncoder": []
    }
    
    try:
        for item in EVAL_DATASET:
            query = item["query"]
            expected_doc = item["expected_document"]
            
            # 1. Vector Search
            vec_res = chroma.retrieve(query, n_results=15)
            # 2. BM25 Search
            bm25_res = hybrid.get_bm25_results(query, db, top_k=15)
            # 3. Hybrid RRF
            rrf_res = hybrid.reciprocal_rank_fusion(vec_res, bm25_res)
            # 4. Hybrid + CrossEncoder
            ce_res = hybrid.cross_encoder_rerank(query, rrf_res, top_k=5)
            
            # Calculate metrics for each config
            configs["Vector-only"].append(calculate_metrics(vec_res, expected_doc))
            configs["BM25-only"].append(calculate_metrics(bm25_res, expected_doc))
            configs["Hybrid RRF"].append(calculate_metrics(rrf_res, expected_doc))
            configs["Hybrid + CrossEncoder"].append(calculate_metrics(ce_res, expected_doc))
            
        print("\n=== EVALUATION REPORT ===")
        print(f"Total Queries Evaluated: {len(EVAL_DATASET)}\n")
        
        final_report = {}
        for config_name, metrics in configs.items():
            avg_recall = sum(m[0] for m in metrics) / len(metrics)
            avg_precision = sum(m[1] for m in metrics) / len(metrics)
            mrr = sum(m[2] for m in metrics) / len(metrics)
            
            final_report[config_name] = {
                "Recall@5": avg_recall,
                "Precision@5": avg_precision,
                "MRR": mrr
            }
            
            print(f"[{config_name}]")
            print(f"  Recall@5:    {avg_recall * 100:.2f}%")
            print(f"  Precision@5: {avg_precision * 100:.2f}%")
            print(f"  MRR:         {mrr:.4f}\n")
            
        with open("retrieval_evaluation.json", "w") as f:
            json.dump(final_report, f, indent=2)
            
        print("Evaluation complete. Report saved to retrieval_evaluation.json")
            
    finally:
        db.close()

if __name__ == "__main__":
    evaluate_retrieval()
