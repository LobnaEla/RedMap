import pandas as pd
import numpy as np
import faiss
import hnswlib
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer
from InstructorEmbedding import INSTRUCTOR
from sklearn.metrics import accuracy_score, f1_score

# Chargement des données
INPUT_FILE = "data/benchmark_dataset.csv"
df = pd.read_csv(INPUT_FILE)

texts = df['text1'].tolist()
labels = df['primary_label'].tolist()

# Définition des modèles
models = {
    "mpnet": SentenceTransformer("all-mpnet-base-v2"),
    "MiniLM": SentenceTransformer("all-MiniLM-L6-v2"),
    "msmarco": SentenceTransformer("msmarco-distilbert-base-v4"),
    "e5": SentenceTransformer("intfloat/e5-base-v2"),
    "bge": SentenceTransformer("BAAI/bge-base-en-v1.5"),
    "Instructor": INSTRUCTOR("hkunlp/instructor-base"),
    "all-MiniLM-L12-v2": SentenceTransformer("all-MiniLM-L12-v2"),
    "all-MiniLM-L6-v1": SentenceTransformer("all-MiniLM-L6-v1"),
}

vector_dbs = ["faiss", "hnswlib", "annoy"]
metrics = ["cosine", "euclidean", "dot"]

def normalize_embeddings(emb):
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    return emb / norms

def faiss_search(embeddings, top_k, metric):
    dim = embeddings.shape[1]
    if metric in ["cosine", "dot"]:
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(dim)
    elif metric == "euclidean":
        index = faiss.IndexFlatL2(dim)
    else:
        raise ValueError("Métrique Faiss non supportée")
    index.add(embeddings)
    distances, indices = index.search(embeddings, top_k)
    return indices

def hnsw_search(embeddings, top_k, metric):
    dim = embeddings.shape[1]
    if metric == "cosine":
        space = "cosine"
        embeddings = normalize_embeddings(embeddings)
    elif metric == "euclidean":
        space = "l2"
    elif metric == "dot":
        space = "ip"
    else:
        raise ValueError("Métrique HNSWLib non supportée")
    index = hnswlib.Index(space=space, dim=dim)
    index.init_index(max_elements=len(embeddings), ef_construction=200, M=16)
    index.add_items(embeddings)
    index.set_ef(50)
    labels_out, distances = index.knn_query(embeddings, k=top_k)
    return labels_out

def annoy_search(embeddings, top_k, metric):
    dim = embeddings.shape[1]
    if metric == "cosine":
        metric_name = "angular"
        embeddings = normalize_embeddings(embeddings)
    elif metric == "euclidean":
        metric_name = "euclidean"
    elif metric == "dot":
        metric_name = "angular"
        embeddings = normalize_embeddings(embeddings)
    else:
        raise ValueError("Métrique Annoy non supportée")
    index = AnnoyIndex(dim, metric_name)
    for i, vector in enumerate(embeddings):
        index.add_item(i, vector)
    index.build(50)
    results = []
    for i in range(len(embeddings)):
        results.append(index.get_nns_by_item(i, top_k))
    return np.array(results)

def recall_at_k(true_labels, neighbor_indices, labels, k=5):
    hits = 0
    for i, neighbors in enumerate(neighbor_indices):
        true_label = true_labels[i]
        retrieved_labels = [labels[idx] for idx in neighbors]
        if true_label in retrieved_labels:
            hits += 1
    return hits / len(true_labels)

def predict_label(true_labels, neighbor_indices, labels):
    preds = []
    for neighbors in neighbor_indices:
        neighbor_labels = [labels[idx] for idx in neighbors]
        pred = max(set(neighbor_labels), key=neighbor_labels.count)
        preds.append(pred)
    return preds

top_k = 5

# Liste pour stocker les résultats
results = []

for model_name, model in models.items():
    print(f"\nModèle: {model_name}")
    if model_name == "Instructor":
        embeddings = model.encode([("Represent the document for retrieval:", text) for text in texts], 
                                  show_progress_bar=True)
    else:
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    
    for vector_db in vector_dbs:
        for metric in metrics:
            try:
                if vector_db == "faiss":
                    indices = faiss_search(embeddings.copy(), top_k, metric)
                elif vector_db == "hnswlib":
                    indices = hnsw_search(embeddings.copy(), top_k, metric)
                elif vector_db == "annoy":
                    indices = annoy_search(embeddings.copy(), top_k, metric)
                else:
                    raise ValueError("Vector DB non supporté")

                recall = recall_at_k(labels, indices, labels, top_k)
                preds = predict_label(labels, indices, labels)
                accuracy = accuracy_score(labels, preds)
                f1 = f1_score(labels, preds, average="macro")

                print(f" - Index: {vector_db} | Métrique: {metric} | Recall@{top_k}: {recall:.4f} | Accuracy: {accuracy:.4f} | F1: {f1:.4f}")

                # Ajouter résultat à la liste
                results.append({
                    "model": model_name,
                    "vector_db": vector_db,
                    "metric": metric,
                    "recall@5": recall,
                    "accuracy": accuracy,
                    "f1_score": f1
                })

            except Exception as e:
                print(f" - Index: {vector_db} | Métrique: {metric} | Erreur: {e}")

# Sauvegarder résultats dans un CSV
results_df = pd.DataFrame(results)
results_df.to_csv("benchmark_results.csv", index=False)
print("\nRésultats sauvegardés dans 'benchmark_results.csv'")
