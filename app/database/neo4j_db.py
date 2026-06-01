from neo4j import GraphDatabase
from app.config import settings
import requests

class Neo4jGraphManager:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        
    def close(self):
        self.driver.close()

    def update_connections_and_get_new(self, target: str, current_followers: list) -> list:
        """Neo4j में डेटा सिंक करता है और केवल 'नए' फॉलोअर्स की लिस्ट रिटर्न करता है"""
        new_followers_detected = []
        
        with self.driver.session() as session:
            # 1. सुनिश्चित करें कि टारगेट नोड मौजूद है
            session.run("MERGE (t:User {username: $target})", target=target)
            
            # 2. हर फॉलोअर को चेक करें और नया होने पर अलर्ट के लिए मार्क करें
            for follower in current_followers:
                # चेक करें कि क्या यह रिश्ता पहले से था?
                check_query = """
                MATCH (f:User {username: $follower})-[r:FOLLOWS]->(t:User {username: $target})
                RETURN r
                """
                result = session.run(check_query, follower=follower, target=target)
                
                if not result.peek():
                    # अगर रिश्ता नहीं मिला, मतलब यह नया फॉलोअर है!
                    new_followers_detected.append(follower)
                
                # अब ग्राफ में नया नोड और रिलेशनशिप बना/अपडेट कर दें
                merge_query = """
                MERGE (f:User {username: $follower})
                MERGE (f)-[r:FOLLOWS]->(t:User {username: $target})
                ON CREATE SET r.detected_at = datetime()
                """
                session.run(merge_query, follower=follower, target=target)
                
        return new_followers_detected

neo4j_manager = Neo4jGraphManager()

