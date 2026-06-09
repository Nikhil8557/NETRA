# backend/app/graph_analytics.py
import logging
from typing import List, Dict, Any
from app.database import db_manager
from ksp_netra_ingestion.schemas_api import PathSegment, NodeRepresentation, EdgeRepresentation

logger = logging.getLogger("ksp_netra.graph_analytics")

class GraphAnalyticsEngine:
    def __init__(self):
        self.manager = db_manager

    async def get_betweenness_centrality(self, projection_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Executes Cypher on active Neo4j driver pools, streaming dynamic node scores.
        """
        query = """
        CALL gds.betweenness.stream($projection_name)
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).guid AS guid, 
               gds.util.asNode(nodeId).full_name AS full_name, 
               labels(gds.util.asNode(nodeId))[0] AS label,
               score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        if not self.manager.neo4j_driver:
            logger.error("GDS stream aborted: Neo4j connection pool is offline.")
            return []
            
        try:
            async with self.manager.neo4j_driver.session() as session:
                result = await session.run(query, projection_name=projection_name, limit=limit)
                records = await result.data()
                return records
        except Exception as e:
            logger.error(f"GDS Centrality execution error on projection '{projection_name}': {e}")
            return []

    async def find_shortest_path(self, suspect_a_guid: str, suspect_b_guid: str, max_depth: int = 4) -> PathSegment:
        """
        Queries relational path connection metrics linking two distinct guidelines targets.
        """
        query = f"""
        MATCH path = shortestPath(
            (startNode:Suspect {{guid: $guid_a}})-[*..{max_depth}]-(endNode:Suspect {{guid: $guid_b}})
        )
        RETURN path
        """
        
        if not self.manager.neo4j_driver:
            logger.error("Path extraction aborted: Neo4j connection pool is offline.")
            return PathSegment()

        try:
            async with self.manager.neo4j_driver.session() as session:
                result = await session.run(query, guid_a=suspect_a_guid, guid_b=suspect_b_guid)
                record = await result.single()
                
                if not record:
                    return PathSegment()

                path = record["path"]
                nodes_dict = {}
                edges_list = []
                
                for node in path.nodes:
                    nid = str(node.element_id)
                    label = list(node.labels)[0] if node.labels else "Unknown"
                    nodes_dict[nid] = NodeRepresentation(id=nid, label=label, properties=dict(node))
                    
                for rel in path.relationships:
                    edges_list.append(EdgeRepresentation(
                        source_id=str(rel.start_node.element_id),
                        target_id=str(rel.end_node.element_id),
                        relationship_type=rel.type,
                        properties=dict(rel)
                    ))
                    
                return PathSegment(nodes=list(nodes_dict.values()), edges=edges_list)
        except Exception as e:
            logger.error(f"Error querying path connection: {e}")
            return PathSegment()
