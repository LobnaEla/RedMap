#!/usr/bin/env python3
"""
Initialize MITRE Technique Collection in Weaviate

This script loads MITRE techniques from CSV, embeds them, and stores them in Weaviate.
Used for initial setup and re-initialization of the vector database.
"""

import logging
import warnings
import sys
import os

# Suppress all warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")

from mitre import MitreLoader
from embeddings import HuggingFaceEmbedder
from vectorstore import WeaviateVectorStore, WeaviateSchema
from config import Config

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf')

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("InitCollection")


def init_mitre_collection():
    """
    Initialize the MITRE technique collection in Weaviate.
    
    This function:
    1. Loads MITRE techniques from CSV
    2. Embeds the technique descriptions
    3. Stores them in Weaviate vector database
    4. Ensures proper schema setup
    """
    store = None
    
    try:
        logger.info("Loading configuration...")
        config = Config()

        logger.info("Loading MITRE techniques from CSV...")
        loader = MitreLoader(config.mitre_csv_path)
        documents = loader.load_techniques()
        logger.info(f"Loaded {len(documents)} MITRE techniques")

        logger.info("Initializing embedder...")
        embedder = HuggingFaceEmbedder()

        logger.info(" Embedding documents (this may take a while)...")
        # Extract text content for embedding
        texts = []
        for doc in documents:
            if hasattr(doc, 'content_for_embedding'):
                texts.append(doc.content_for_embedding)
            elif hasattr(doc, 'description'):
                texts.append(doc.description)
            else:
                texts.append("")  # fallback empty string
        
        # Generate embeddings in batch
        embeddings = embedder.embed_batch(texts)
        logger.info(f" Generated embeddings for {len(embeddings)} documents")

        # Clean up embedding attributes from documents to avoid conflicts
        for doc in documents:
            if hasattr(doc, '__dict__') and 'embedding' in doc.__dict__:
                del doc.__dict__['embedding']

        logger.info("Connecting to Weaviate...")
        store = WeaviateVectorStore()

        logger.info("Ensuring Weaviate schema exists...")
        WeaviateSchema.get_mitre_technique_schema()

        logger.info("Clearing existing collection...")
        collection = store.client.collections.get(store.class_name)
        try:
            deleted_count = collection.data.delete_many(where={})  
            logger.info(f"Deleted {deleted_count} existing objects from '{store.class_name}' collection")
        except Exception as del_err:
            logger.warning(f" Could not clear existing collection: {del_err}")

        logger.info(" Preparing metadata for insertion...")
        # Extract document IDs for the add_documents method
        document_ids = [doc.id for doc in documents]
        
        metadata = []
        for doc in documents:
            # Use the document's metadata property and add missing fields
            meta = doc.metadata.copy()
            
            # Ensure all required fields are present
            meta_safe = {
                'id': meta.get('id', doc.id),
                'name': meta.get('name', doc.name),
                'description': getattr(doc, 'description', ''),
                'url': meta.get('url', getattr(doc, 'url', '')),
                'platforms': meta.get('platforms', []),
                'kill_chain_phases': meta.get('kill_chain_phases', []),
                'data_sources': meta.get('data_sources', []),
                'detection': getattr(doc, 'detection', '')
            }
            metadata.append(meta_safe)

        # Ensure embeddings are in proper format (lists, not numpy arrays)
        embeddings = [
            emb.tolist() if hasattr(emb, 'tolist') 
            else list(emb) if not isinstance(emb, list) 
            else emb 
            for emb in embeddings
        ]

        # Ensure all metadata values are JSON-serializable
        def make_json_serializable(d):
            return {
                k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v) 
                for k, v in d.items()
            }
        metadata = [make_json_serializable(m) for m in metadata]

        logger.info("Inserting documents into Weaviate...")
        store.add_documents(document_ids, embeddings, metadata)
        logger.info("Successfully inserted all documents into collection")

        # Verify insertion
        logger.info("Verifying collection initialization...")
        try:
            agg_response = collection.aggregate.over_all(total_count=True)
            obj_count = agg_response.total_count if agg_response else 0
            logger.info(f" Collection '{store.class_name}' now contains {obj_count} objects")
            
            if obj_count != len(documents):
                logger.warning(f"Expected {len(documents)} objects, but found {obj_count}")
            else:
                logger.info("Collection initialization completed successfully!")
                
        except Exception as e:
            logger.warning(f"Could not verify object count: {e}")

        return True

    except Exception as e:
        logger.exception(f"Error during collection initialization: {e}")
        return False

    finally:
        # Clean up Weaviate connection
        if store and hasattr(store, 'client') and hasattr(store.client, 'close'):
            store.client.close()
            logger.info("Weaviate client connection closed")


def main():
    """Main entry point for the initialization script."""
    logger.info("Starting MITRE technique collection initialization...")
    
    success = init_mitre_collection()
    
    if success:
        logger.info("Collection initialization completed successfully!")
        sys.exit(0)
    else:
        logger.error("Collection initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
