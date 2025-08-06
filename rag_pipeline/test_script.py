import logging
import warnings
import sys

# Suppress all warnings
if not sys.warnoptions:
    import warnings

    warnings.simplefilter("ignore")
import sys
import os
from mitre import MitreLoader
from embeddings import HuggingFaceEmbedder
from vectorstore import WeaviateVectorStore, WeaviateSchema
from rag import RAGEngine
from config import Config

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("RAGTest")


def main():
    try:
        logger.info("🔧 Loading config...")
        config = Config()

        logger.info("📄 Loading MITRE techniques from CSV...")
        loader = MitreLoader(config.mitre_csv_path)
        documents = loader.load_techniques()
        logger.info(f"✅ Loaded {len(documents)} techniques")

        logger.info("🔢 Loading embedder...")
        embedder = HuggingFaceEmbedder()

        logger.info("🧠 Embedding documents...")
        texts = []
        for doc in documents:
            if hasattr(doc, "text"):
                texts.append(doc.text())
            elif hasattr(doc, "description"):
                texts.append(doc.description)
            else:
                texts.append("")  # fallback empty string
        embeddings = embedder.embed_batch(texts)
        for doc, emb in zip(documents, embeddings):
            doc.embedding = emb

        # Remove 'embedding' key from document dicts if present
        for doc in documents:
            if hasattr(doc, "__dict__") and "embedding" in doc.__dict__:
                del doc.__dict__["embedding"]

        logger.info("🔗 Connecting to Weaviate...")
        store = WeaviateVectorStore(url="http://localhost:5000")

        logger.info("📐 Ensuring schema...")
        WeaviateSchema.get_mitre_technique_schema()

        logger.info("🧹 Deleting existing objects in collection...")
        collection = store.client.collections.get(store.class_name)
        try:
            deleted_count = collection.data.delete_many(where={})  # Delete all
            logger.info(
                f"🗑️ Deleted {deleted_count} existing objects in '{store.class_name}' collection."
            )
        except Exception as del_err:
            logger.warning(f"⚠️ Could not clear collection: {del_err}")

        logger.info("💾 Inserting documents into Weaviate...")
        metadata = []
        for doc in documents:
            meta = getattr(doc, "metadata", {})
            # Remove 'embedding' key if present in metadata
            if "embedding" in meta:
                del meta["embedding"]
            meta_safe = {
                "technique_id": meta.get("technique_id", getattr(doc, "id", "")),
                "name": meta.get("name", getattr(doc, "name", "")),
                "description": meta.get("description", getattr(doc, "description", "")),
                "detection": meta.get("detection", getattr(doc, "detection", "")),
            }
            metadata.append(meta_safe)

        # Debug: Print types and samples before insertion
        import json

        logger.info(
            f"Sample document: {getattr(documents[0], '__dict__', str(documents[0]))}"
        )
        logger.info(
            f"Sample embedding: {embeddings[0][:5]}... (len={len(embeddings[0])})"
        )
        logger.info(f"Sample metadata: {metadata[0]}")
        logger.info(
            f"Embedding type: {type(embeddings[0])}, Metadata type: {type(metadata[0])}"
        )

        # Ensure embeddings are lists (not numpy arrays)
        embeddings = [
            (
                emb.tolist()
                if hasattr(emb, "tolist")
                else list(emb) if not isinstance(emb, list) else emb
            )
            for emb in embeddings
        ]

        # Ensure all metadata values are JSON-serializable (str, int, float, bool, None)
        def make_json_serializable(d):
            return {
                k: (
                    str(v)
                    if not isinstance(v, (str, int, float, bool, type(None)))
                    else v
                )
                for k, v in d.items()
            }

        metadata = [make_json_serializable(m) for m in metadata]

        store.add_documents(documents, embeddings, metadata)
        logger.info("✅ Insertion complete")

        logger.info("🔍 Verifying insertion...")
        try:
            agg_response = collection.aggregate.over_all(total_count=True)
            obj_count = agg_response.total_count if agg_response else 0
            logger.info(
                f"✅ Verified {obj_count} objects now present in collection '{store.class_name}'"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not verify object count: {e}")

        # Manual vector search using the embedding of the first inserted document
        logger.info(
            "🔎 Manual vector search using the embedding of the first inserted document..."
        )
        if embeddings and len(embeddings) > 0:
            engine = RAGEngine(embedder=embedder, vector_store=store)
            manual_results = engine.vector_store.search(embeddings[0], top_k=10)
            if not manual_results:
                logger.warning("⚠️ No results retrieved for manual vector search!")
            else:
                logger.info(
                    f"✅ Retrieved {len(manual_results)} result(s) for manual vector search (should include the first document). Similarity scores:"
                )
                for i, result in enumerate(manual_results, 1):
                    logger.info(
                        f"{i}. {result.metadata.get('technique_id', result.metadata.get('id', ''))} - {result.metadata.get('name', '')}"
                    )
                    logger.info(f"    Score: {getattr(result, 'score', 0):.4f}")
                    logger.info(
                        f"    Description: {result.metadata.get('description', '')[:150]}...\n"
                    )

        logger.info("🔎 Testing retrieval on an inserted description...")
        if metadata and metadata[0].get("description"):
            test_desc = metadata[0]["description"]
            engine = RAGEngine(embedder=embedder, vector_store=store)
            results = engine.retrieve_techniques(query=test_desc)

            if not results:
                logger.warning("⚠️ No results retrieved from inserted document query!")
            else:
                logger.info(
                    f"✅ Retrieved {len(results)} result(s) for a known description."
                )
                for i, result in enumerate(results, 1):
                    logger.info(
                        f"{i}. {result.metadata.get('technique_id', result.metadata.get('id', ''))} - {result.metadata.get('name', '')}"
                    )
                    logger.info(f"    Score: {getattr(result, 'score', 0):.4f}")
                    logger.info(
                        f"    Description: {result.metadata.get('description', '')[:150]}...\n"
                    )
        else:
            logger.warning("⚠️ No description available in metadata to test retrieval.")

        logger.info("🔍 Running test query...")
        query = "can obtain system information such as OS version and disk space."
        engine = RAGEngine(embedder=embedder, vector_store=store)
        results = engine.retrieve_techniques(query=query)

        if not results:
            logger.warning("⚠️ No results retrieved for test query!")
        else:
            logger.info(f"🎯 Top results for query: '{query}'")
            for i, result in enumerate(results, 1):
                logger.info(
                    f"{i}. {result.metadata.get('technique_id', result.metadata.get('id', ''))} - {result.metadata.get('name', '')}"
                )
                logger.info(f"    Score: {getattr(result, 'score', 0):.4f}")
                logger.info(
                    f"    Description: {result.metadata.get('description', '')[:150]}...\n"
                )

    except Exception as e:
        logger.exception(f"❌ Error during test script execution: {e}")

    finally:
        if (
            "store" in locals()
            and hasattr(store, "client")
            and hasattr(store.client, "close")
        ):
            store.client.close()
            logger.info("🔚 Weaviate client closed")


if __name__ == "__main__":
    main()
