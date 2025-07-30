import os
import glob
from typing import List

def load_chunk_files(chunks_dir: str) -> List[str]:
    """Charge les fichiers de chunks depuis le répertoire"""
    try:
        chunk_files = glob.glob(os.path.join(chunks_dir, "chunks_*.json"))
        if not chunk_files:
            raise FileNotFoundError(f"No chunk files found in {chunks_dir}")
        return chunk_files

    except Exception as e:
        raise RuntimeError(f"Error loading chunk files: {str(e)}")