import networkx as nx
from app.database.neo4j_db import neo4j_manager

def run_networkx_analysis(target: str):
    """Neo4j से सब-ग्राफ निकालकर NetworkX में लाइव एनालिसिस करना"""
    G = nx.DiGraph()
    
    # टारगेट के आसपास का 1st-degree नेटवर्क लोड करें (पूरी DB लोड करने की जरूरत नहीं)
    query = """
    MATCH (f:User)-[:FOLLOWS]->(t:User {username: $target})
    RETURN f.username as source, t.username as target
    """
    with neo4j_manager.driver.session() as session:
        results = session.run(query, target=target)
        for record in results:
            G.add_edge(record["source"], record["target"])
            
    if len(G) == 0:
        return {"status": "empty_graph"}
        
    # NetworkX Centrality & Analytics
    degrees = dict(G.in_degree())
    highest_influence_node = max(degrees, key=degrees.get) if degrees else None
    density = nx.density(G)
    
    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "highest_influence_node": highest_influence_node,
        "graph_density": density
    }
  
