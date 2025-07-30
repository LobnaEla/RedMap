from py2neo import Graph, Node, Relationship
import os
import json
import glob

def build_cti_graph():
    # Connexion à Neo4j (adapté selon ton user/mot de passe)
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

    # Chemin vers les résultats RAG validés
    rag_dir = "/opt/project/cti_pipeline/data/rag_results"
    rag_files = glob.glob(os.path.join(rag_dir, "rag_*.json"))

    for file in rag_files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for chunk in data.get("rag_results", []):
                chunk_id = chunk.get("chunk_id")
                chunk_text = chunk.get("original_text", "")

                # Création du nœud Chunk
                chunk_node = Node("Chunk", id=str(chunk_id), text=chunk_text)
                graph.merge(chunk_node, "Chunk", "id")

                # Parcours des techniques extraites
                for ttp in chunk.get("mitre_techniques", []):
                    tech_id = ttp.get("id")
                    tech_name = ttp.get("name")

                    # Nœud Technique
                    tech_node = Node("Technique", id=tech_id, name=tech_name)
                    graph.merge(tech_node, "Technique", "id")

                    # Relation Chunk -> Technique
                    rel = Relationship(chunk_node, "MENTIONS", tech_node)
                    graph.merge(rel)

                    # Optionnel : création et lien avec Tactic si présent
                    tactic = ttp.get("tactic")
                    if tactic:
                        tactic_node = Node("Tactic", name=tactic)
                        graph.merge(tactic_node, "Tactic", "name")
                        graph.merge(Relationship(tech_node, "BELONGS_TO", tactic_node))

if __name__ == "__main__":
    build_cti_graph()
