import os
import gc
import numpy as np
import pandas as pd
import faiss
import hnswlib
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer
from InstructorEmbedding import INSTRUCTOR
from sklearn.metrics.pairwise import cosine_similarity

INPUT_FILE = "data/enterprise-attack150.csv"

# Chargement dataset complet
df = pd.read_csv(INPUT_FILE)
print(f"📊 {len(df)} techniques chargées")

queries = df['id'].tolist()
docs = df['description'].tolist()
id2desc = dict(zip(queries, docs))

# Modèles à tester
MODELS = {
    "mpnet": SentenceTransformer("all-mpnet-base-v2"),
    "MiniLM": SentenceTransformer("all-MiniLM-L6-v2"),
    "msmarco": SentenceTransformer("msmarco-distilbert-base-v4"),
    "e5": SentenceTransformer("intfloat/e5-base-v2"),
    "bge": SentenceTransformer("BAAI/bge-base-en-v1.5"),
    "Instructor": INSTRUCTOR("hkunlp/instructor-base")
}

def get_embeddings(model_name, model, texts):
    if model_name == "Instructor":
        return model.encode([["Represent the MITRE technique:", t] for t in texts], show_progress_bar=False)
    elif "e5" in model_name:
        return model.encode(["query: " + t for t in texts], show_progress_bar=False)
    elif "bge" in model_name:
        return model.encode([t + " </s>" for t in texts], show_progress_bar=False)
    else:
        return model.encode(texts, show_progress_bar=False)

def compute_metric_name(metric):
    return {"cosine": "angular", "dot": "dot", "euclidean": "euclidean"}[metric]

top_k = 3

results = []

for model_name, model in MODELS.items():
    print(f"\n🚀 Modèle : {model_name}")
    embeddings = get_embeddings(model_name, model, docs)
    embeddings = np.array(embeddings).astype("float32")

    for metric in ["cosine", "dot", "euclidean"]:
        for vec_type in ["faiss", "annoy", "hnswlib"]:
            print(f"🔎 Index : {vec_type} | Métrique : {metric}")

            if vec_type == "faiss":
                emb = embeddings.copy()
                if metric == "cosine":
                    faiss.normalize_L2(emb)
                index = faiss.IndexFlatIP(emb.shape[1]) if metric != "euclidean" else faiss.IndexFlatL2(emb.shape[1])
                index.add(emb)
                D, I = index.search(emb, top_k)

            elif vec_type == "annoy":
                index = AnnoyIndex(embeddings.shape[1], compute_metric_name(metric))
                for i, vec in enumerate(embeddings):
                    index.add_item(i, vec)
                index.build(10)
                I = [index.get_nns_by_item(i, top_k) for i in range(len(embeddings))]

            elif vec_type == "hnswlib":
                metric_map = {"cosine": "cosine", "dot": "ip", "euclidean": "l2"}
                index = hnswlib.Index(space=metric_map[metric], dim=embeddings.shape[1])
                index.init_index(max_elements=len(embeddings), ef_construction=100, M=16)
                index.add_items(embeddings)
                I = index.knn_query(embeddings, k=top_k)[0]

            recall_at_3 = 0
            accuracy = 0
            for idx, neighbors in enumerate(I):
                true_id = queries[idx]
                pred_ids = [queries[n] for n in neighbors]
                if true_id in pred_ids:
                    recall_at_3 += 1
                    if true_id == pred_ids[0]:
                        accuracy += 1

            recall_at_3 /= len(queries)
            accuracy /= len(queries)

            # Precision = accuracy (car premières positions prédites)
            precision = accuracy
            recall = recall_at_3

            # F1 = 2 * (precision * recall) / (precision + recall)
            if precision + recall == 0:
                f1 = 0
            else:
                f1 = 2 * (precision * recall) / (precision + recall)

            result = {
                "model": model_name,
                "vector_db": vec_type,
                "metric": metric,
                "accuracy": round(accuracy, 4),
                "recall@3": round(recall_at_3, 4),
                "f1_score": round(f1, 4)
            }

            print(f"✅ Résultat : {result}")
            results.append(result)
            gc.collect()

# Affichage final du top 5
df_res = pd.DataFrame(results).sort_values(by=["accuracy", "recall@3", "f1_score"], ascending=False)
print("\n🔝 Top 5 combinaisons:\n")
print(df_res.head(5))
