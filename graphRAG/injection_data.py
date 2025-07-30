from py2neo import Graph, Node, Relationship
import os
import json
import glob
import networkx as nx
import matplotlib.pyplot as plt

def build_cti_graph():
    # Connexion à Neo4j (à adapter)
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

    rag_dir = "/opt/project/rag_pipeline/data/rag_results"#i'll change it later
    rag_files = glob.glob(os.path.join(rag_dir, "rag_*.json"))

    for file in rag_files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for chunk in data.get("rag_results", []):
                chunk_id = chunk.get("chunk_id")
                chunk_text = chunk.get("original_text", "")

                # Créer nœud Chunk
                chunk_node = Node("Chunk", id=str(chunk_id), text=chunk_text)
                graph.merge(chunk_node, "Chunk", "id")

                # Parcourir techniques extraites
                for ttp in chunk.get("mitre_techniques", []):
                    tech_id = ttp.get("id")
                    tech_name = ttp.get("name")

                    tech_node = Node("Technique", id=tech_id, name=tech_name)
                    graph.merge(tech_node, "Technique", "id")

                    rel = Relationship(chunk_node, "MENTIONS", tech_node)
                    graph.merge(rel)

                    tactic = ttp.get("tactic")
                    if tactic:
                        tactic_node = Node("Tactic", name=tactic)
                        graph.merge(tactic_node, "Tactic", "name")
                        graph.merge(Relationship(tech_node, "BELONGS_TO", tactic_node))


def draw_cti_graph():
    graph_db = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
    
    query = """
    MATCH (c:Chunk)-[r:MENTIONS]->(t:Technique)
    OPTIONAL MATCH (t)-[b:BELONGS_TO]->(a:Tactic)
    RETURN c.id AS chunk_id, t.id AS tech_id, t.name AS tech_name, a.name AS tactic_name
    """

    data = graph_db.run(query).data()

    G = nx.DiGraph()

    for record in data:
        chunk_label = f"Chunk {record['chunk_id']}"
        tech_label = f"{record['tech_name']} ({record['tech_id']})"
        G.add_node(chunk_label, type='Chunk')
        G.add_node(tech_label, type='Technique')
        G.add_edge(chunk_label, tech_label, label='MENTIONS')
        
        if record['tactic_name']:
            tactic_label = f"Tactic: {record['tactic_name']}"
            G.add_node(tactic_label, type='Tactic')
            G.add_edge(tech_label, tactic_label, label='BELONGS_TO')

    pos = nx.spring_layout(G, k=0.7, iterations=50)

    plt.figure(figsize=(14, 10))
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1500)
    nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20)
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')

    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)

    plt.title("Visualisation du Graphe CTI")
    plt.axis('off')
    plt.show()


if __name__ == "__main__":
    print("Construction du graphe CTI dans Neo4j...")
    build_cti_graph()
    print("Dessin du graphe CTI...")
    draw_cti_graph()
