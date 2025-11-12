"""
Service for processing lineage graphs.
Handles deduplication, filtering, impact analysis, and graph operations.
"""

import logging
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import defaultdict, deque

from app.models.lineage import (
    LineageNode,
    LineageEdge,
    LineageGraph,
    NodeType,
    EdgeType
)

logger = logging.getLogger(__name__)


class LineageProcessor:
    """Processes and manipulates lineage graphs"""
    
    def process_graph(self, graph: LineageGraph) -> LineageGraph:
        """
        Process a lineage graph with deduplication and cleanup.
        
        Args:
            graph: Input lineage graph
            
        Returns:
            Processed lineage graph
        """
        # Deduplicate nodes and edges
        unique_nodes = self._deduplicate_nodes(graph.nodes)
        unique_edges = self._deduplicate_edges(graph.edges)
        
        # Remove orphaned edges (edges with missing nodes)
        valid_edges = self._remove_orphaned_edges(unique_edges, unique_nodes)
        
        # Sort nodes and edges for consistent output
        sorted_nodes = sorted(unique_nodes, key=lambda n: n.id)
        sorted_edges = sorted(valid_edges, key=lambda e: (e.source, e.target))
        
        return LineageGraph(
            nodes=sorted_nodes,
            edges=sorted_edges,
            metadata=graph.metadata
        )
    
    def filter_by_node_types(
        self, 
        graph: LineageGraph, 
        allowed_types: List[NodeType]
    ) -> LineageGraph:
        """
        Filter graph to only include specified node types.
        
        Args:
            graph: Input graph
            allowed_types: List of allowed node types
            
        Returns:
            Filtered graph
        """
        # Filter nodes
        filtered_nodes = [
            node for node in graph.nodes 
            if node.type in allowed_types
        ]
        
        # Get IDs of remaining nodes
        node_ids = {node.id for node in filtered_nodes}
        
        # Filter edges to only include edges between remaining nodes
        filtered_edges = [
            edge for edge in graph.edges
            if edge.source in node_ids and edge.target in node_ids
        ]
        
        return LineageGraph(
            nodes=filtered_nodes,
            edges=filtered_edges,
            metadata={
                **graph.metadata,
                "filtered_by_types": [t.value for t in allowed_types],
                "original_node_count": len(graph.nodes),
                "original_edge_count": len(graph.edges)
            }
        )
    
    def filter_by_depth(
        self, 
        graph: LineageGraph, 
        root_node_id: str, 
        max_depth: int
    ) -> LineageGraph:
        """
        Filter graph to only include nodes within max_depth of root node.
        
        Args:
            graph: Input graph
            root_node_id: Root node to measure depth from
            max_depth: Maximum depth to include
            
        Returns:
            Filtered graph
        """
        # Build adjacency list
        adjacency = defaultdict(list)
        for edge in graph.edges:
            adjacency[edge.source].append(edge.target)
            adjacency[edge.target].append(edge.source)  # Bidirectional for depth calculation
        
        # BFS to find nodes within max_depth
        visited = set()
        queue = deque([(root_node_id, 0)])
        nodes_within_depth = set()
        
        while queue:
            node_id, depth = queue.popleft()
            
            if node_id in visited or depth > max_depth:
                continue
                
            visited.add(node_id)
            nodes_within_depth.add(node_id)
            
            # Add neighbors
            for neighbor in adjacency[node_id]:
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))
        
        # Filter nodes and edges
        filtered_nodes = [
            node for node in graph.nodes 
            if node.id in nodes_within_depth
        ]
        
        filtered_edges = [
            edge for edge in graph.edges
            if edge.source in nodes_within_depth and edge.target in nodes_within_depth
        ]
        
        return LineageGraph(
            nodes=filtered_nodes,
            edges=filtered_edges,
            metadata={
                **graph.metadata,
                "filtered_by_depth": max_depth,
                "root_node": root_node_id
            }
        )
    
    def calculate_impact_analysis(
        self, 
        graph: LineageGraph, 
        changed_node_id: str
    ) -> Dict[str, Any]:
        """
        Calculate impact analysis for a node change.
        
        Args:
            graph: Lineage graph
            changed_node_id: ID of the node that changed
            
        Returns:
            Impact analysis results
        """
        # Build directed adjacency list (source -> targets)
        downstream_adjacency = defaultdict(list)
        for edge in graph.edges:
            if edge.type in [EdgeType.DERIVES_FROM, EdgeType.TRANSFORMS_TO]:
                # Reverse the edge direction for downstream impact
                downstream_adjacency[edge.source].append(edge.target)
        
        # Find directly impacted nodes (immediate downstream)
        directly_impacted = set(downstream_adjacency[changed_node_id])
        
        # Find indirectly impacted nodes (downstream of directly impacted)
        indirectly_impacted = set()
        queue = deque(directly_impacted)
        visited = set(directly_impacted)
        
        while queue:
            current_node = queue.popleft()
            
            for downstream_node in downstream_adjacency[current_node]:
                if downstream_node not in visited and downstream_node != changed_node_id:
                    visited.add(downstream_node)
                    indirectly_impacted.add(downstream_node)
                    queue.append(downstream_node)
        
        # Calculate impact scores by node type
        impact_by_type = defaultdict(int)
        node_lookup = {node.id: node for node in graph.nodes}
        
        all_impacted = directly_impacted.union(indirectly_impacted)
        for node_id in all_impacted:
            if node_id in node_lookup:
                node_type = node_lookup[node_id].type
                impact_by_type[node_type.value] += 1
        
        return {
            "changed_node": changed_node_id,
            "directly_impacted": list(directly_impacted),
            "indirectly_impacted": list(indirectly_impacted),
            "total_impact_count": len(all_impacted),
            "impact_by_type": dict(impact_by_type),
            "impact_score": self._calculate_impact_score(all_impacted, node_lookup)
        }
    
    def detect_cycles(self, graph: LineageGraph) -> List[List[str]]:
        """
        Detect cycles in the lineage graph.
        
        Args:
            graph: Lineage graph to analyze
            
        Returns:
            List of cycles (each cycle is a list of node IDs)
        """
        # Build adjacency list
        adjacency = defaultdict(list)
        for edge in graph.edges:
            adjacency[edge.source].append(edge.target)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in adjacency[node]:
                if dfs(neighbor, path):
                    # Cycle found in subtree
                    pass
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        # Check all nodes
        for node in graph.nodes:
            if node.id not in visited:
                dfs(node.id, [])
        
        return cycles
    
    def get_shortest_path(
        self, 
        graph: LineageGraph, 
        source_id: str, 
        target_id: str
    ) -> Optional[List[str]]:
        """
        Find shortest path between two nodes.
        
        Args:
            graph: Lineage graph
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            List of node IDs representing the shortest path, or None if no path exists
        """
        # Build bidirectional adjacency list
        adjacency = defaultdict(list)
        for edge in graph.edges:
            adjacency[edge.source].append(edge.target)
            adjacency[edge.target].append(edge.source)
        
        # BFS to find shortest path
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            current_node, path = queue.popleft()
            
            if current_node == target_id:
                return path
            
            for neighbor in adjacency[current_node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def get_connected_components(self, graph: LineageGraph) -> List[List[str]]:
        """
        Find connected components in the graph.
        
        Args:
            graph: Lineage graph
            
        Returns:
            List of connected components (each component is a list of node IDs)
        """
        # Build bidirectional adjacency list
        adjacency = defaultdict(list)
        for edge in graph.edges:
            adjacency[edge.source].append(edge.target)
            adjacency[edge.target].append(edge.source)
        
        visited = set()
        components = []
        
        def dfs(node: str, component: List[str]):
            if node in visited:
                return
            
            visited.add(node)
            component.append(node)
            
            for neighbor in adjacency[node]:
                dfs(neighbor, component)
        
        # Find all components
        for node in graph.nodes:
            if node.id not in visited:
                component = []
                dfs(node.id, component)
                if component:
                    components.append(component)
        
        return components
    
    def calculate_node_metrics(self, graph: LineageGraph) -> Dict[str, Dict[str, Any]]:
        """
        Calculate metrics for each node in the graph.
        
        Args:
            graph: Lineage graph
            
        Returns:
            Dictionary mapping node IDs to their metrics
        """
        # Build adjacency lists
        outgoing = defaultdict(list)
        incoming = defaultdict(list)
        
        for edge in graph.edges:
            outgoing[edge.source].append(edge.target)
            incoming[edge.target].append(edge.source)
        
        metrics = {}
        
        for node in graph.nodes:
            node_id = node.id
            
            # Basic degree metrics
            out_degree = len(outgoing[node_id])
            in_degree = len(incoming[node_id])
            total_degree = out_degree + in_degree
            
            # Calculate centrality measures
            # (Simplified versions - full calculations would require more complex algorithms)
            
            metrics[node_id] = {
                "node_type": node.type.value,
                "in_degree": in_degree,
                "out_degree": out_degree,
                "total_degree": total_degree,
                "is_source": in_degree == 0 and out_degree > 0,
                "is_sink": out_degree == 0 and in_degree > 0,
                "is_isolated": total_degree == 0,
                "downstream_count": self._count_downstream_nodes(node_id, outgoing),
                "upstream_count": self._count_upstream_nodes(node_id, incoming)
            }
        
        return metrics
    
    def _deduplicate_nodes(self, nodes: List[LineageNode]) -> List[LineageNode]:
        """Remove duplicate nodes based on ID"""
        seen = set()
        unique_nodes = []
        
        for node in nodes:
            if node.id not in seen:
                seen.add(node.id)
                unique_nodes.append(node)
        
        return unique_nodes
    
    def _deduplicate_edges(self, edges: List[LineageEdge]) -> List[LineageEdge]:
        """Remove duplicate edges based on source-target-type combination"""
        seen = set()
        unique_edges = []
        
        for edge in edges:
            edge_key = (edge.source, edge.target, edge.type)
            if edge_key not in seen:
                seen.add(edge_key)
                unique_edges.append(edge)
        
        return unique_edges
    
    def _remove_orphaned_edges(
        self, 
        edges: List[LineageEdge], 
        nodes: List[LineageNode]
    ) -> List[LineageEdge]:
        """Remove edges that reference non-existent nodes"""
        node_ids = {node.id for node in nodes}
        
        valid_edges = [
            edge for edge in edges
            if edge.source in node_ids and edge.target in node_ids
        ]
        
        if len(valid_edges) < len(edges):
            logger.debug(f"Removed {len(edges) - len(valid_edges)} orphaned edges")
        
        return valid_edges
    
    def _calculate_impact_score(
        self, 
        impacted_nodes: Set[str], 
        node_lookup: Dict[str, LineageNode]
    ) -> float:
        """Calculate a weighted impact score based on node types"""
        type_weights = {
            NodeType.MODEL: 10.0,
            NodeType.METRIC: 8.0,
            NodeType.VIEW: 6.0,
            NodeType.TABLE: 4.0,
            NodeType.COLUMN: 2.0,
            NodeType.FILE: 1.0
        }
        
        total_score = 0.0
        for node_id in impacted_nodes:
            if node_id in node_lookup:
                node_type = node_lookup[node_id].type
                weight = type_weights.get(node_type, 1.0)
                total_score += weight
        
        return total_score
    
    def _count_downstream_nodes(
        self, 
        node_id: str, 
        adjacency: Dict[str, List[str]]
    ) -> int:
        """Count all downstream nodes from a given node"""
        visited = set()
        queue = deque([node_id])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            
            visited.add(current)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    queue.append(neighbor)
        
        # Subtract 1 to exclude the starting node itself
        return max(0, len(visited) - 1)
    
    def _count_upstream_nodes(
        self, 
        node_id: str, 
        adjacency: Dict[str, List[str]]
    ) -> int:
        """Count all upstream nodes from a given node"""
        visited = set()
        queue = deque([node_id])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            
            visited.add(current)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    queue.append(neighbor)
        
        # Subtract 1 to exclude the starting node itself
        return max(0, len(visited) - 1)

