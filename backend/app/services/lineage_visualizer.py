"""
Service for generating lineage visualizations.
Handles layout algorithms, export formats, and visualization data preparation.
"""

import json
import logging
import math
from typing import Dict, List, Any, Tuple, Optional
from xml.etree.ElementTree import Element, SubElement, tostring

from app.models.lineage import LineageGraph, LineageNode, LineageEdge, NodeType, EdgeType

logger = logging.getLogger(__name__)


class LineageVisualizer:
    """Generates visualization data and exports for lineage graphs"""
    
    def __init__(self):
        self.node_colors = {
            NodeType.TABLE: "#3B82F6",      # Blue
            NodeType.VIEW: "#10B981",       # Green
            NodeType.MODEL: "#F59E0B",      # Amber
            NodeType.METRIC: "#EF4444",     # Red
            NodeType.DIMENSION: "#8B5CF6",  # Violet
            NodeType.COLUMN: "#6B7280",     # Gray
            NodeType.FILE: "#F97316",       # Orange
            NodeType.EXTERNAL: "#6366F1"    # Indigo
        }
        
        self.edge_colors = {
            EdgeType.DERIVES_FROM: "#374151",      # Dark gray
            EdgeType.JOINS_WITH: "#059669",        # Green
            EdgeType.FILTERS_FROM: "#DC2626",      # Red
            EdgeType.AGGREGATES_FROM: "#7C3AED",   # Purple
            EdgeType.REFERENCES: "#2563EB",        # Blue
            EdgeType.CONTAINS: "#F59E0B",          # Amber
            EdgeType.TRANSFORMS_TO: "#0891B2"      # Cyan
        }
    
    def generate_visualization_data(
        self, 
        graph: LineageGraph,
        layout_algorithm: str = "hierarchical",
        include_positions: bool = True
    ) -> Dict[str, Any]:
        """
        Generate visualization data from lineage graph.
        
        Args:
            graph: Lineage graph to visualize
            layout_algorithm: Algorithm to use for node positioning
            include_positions: Whether to calculate node positions
            
        Returns:
            Visualization data ready for frontend consumption
        """
        logger.info(f"Generating visualization data with {layout_algorithm} layout")
        
        # Prepare nodes for visualization
        viz_nodes = []
        for node in graph.nodes:
            viz_node = {
                "id": node.id,
                "name": node.name,
                "type": node.type,
                "catalog": node.catalog,
                "schema": node.schema,
                "description": node.description,
                "metadata": node.metadata,
                "color": self.node_colors.get(node.type, "#6B7280"),
                "icon": self._get_node_icon(node.type),
                "size": self._get_node_size(node),
                "shape": self._get_node_shape(node.type)
            }
            
            # Add existing position if available
            if node.x is not None and node.y is not None:
                viz_node["x"] = node.x
                viz_node["y"] = node.y
            
            viz_nodes.append(viz_node)
        
        # Prepare edges for visualization
        viz_edges = []
        for edge in graph.edges:
            viz_edge = {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "type": edge.type,
                "label": edge.label or self._get_edge_label(edge.type),
                "metadata": edge.metadata,
                "color": self.edge_colors.get(edge.type, "#6B7280"),
                "style": edge.style or self._get_edge_style(edge.type),
                "weight": edge.weight or 1.0,
                "animated": self._should_animate_edge(edge.type)
            }
            viz_edges.append(viz_edge)
        
        # Apply layout algorithm if positions needed
        if include_positions:
            layout_data = self.apply_layout_algorithm(graph, layout_algorithm)
            # Update positions in viz_nodes
            for viz_node in viz_nodes:
                layout_node = next(
                    (n for n in layout_data["nodes"] if n["id"] == viz_node["id"]), 
                    None
                )
                if layout_node:
                    viz_node["x"] = layout_node["x"]
                    viz_node["y"] = layout_node["y"]
        
        # Calculate graph statistics
        stats = self._calculate_graph_stats(graph)
        
        return {
            "nodes": viz_nodes,
            "edges": viz_edges,
            "layout": {
                "algorithm": layout_algorithm,
                "direction": graph.direction or "LR",
                "spacing": self._calculate_spacing(len(viz_nodes))
            },
            "statistics": stats,
            "metadata": graph.metadata,
            "bounds": self._calculate_bounds(viz_nodes) if include_positions else None
        }
    
    def apply_layout_algorithm(
        self, 
        graph: LineageGraph, 
        algorithm: str = "hierarchical"
    ) -> Dict[str, Any]:
        """
        Apply a layout algorithm to position nodes.
        
        Args:
            graph: Lineage graph
            algorithm: Layout algorithm to use
            
        Returns:
            Layout data with node positions
        """
        if algorithm == "hierarchical":
            return self._apply_hierarchical_layout(graph)
        elif algorithm == "force-directed":
            return self._apply_force_directed_layout(graph)
        elif algorithm == "circular":
            return self._apply_circular_layout(graph)
        elif algorithm == "tree":
            return self._apply_tree_layout(graph)
        else:
            logger.warning(f"Unknown layout algorithm: {algorithm}, using hierarchical")
            return self._apply_hierarchical_layout(graph)
    
    def export_as_svg(
        self, 
        graph: LineageGraph,
        width: int = 1200,
        height: int = 800
    ) -> str:
        """
        Export lineage graph as SVG.
        
        Args:
            graph: Lineage graph to export
            width: SVG width
            height: SVG height
            
        Returns:
            SVG string
        """
        # Generate visualization data with positions
        viz_data = self.generate_visualization_data(graph, "hierarchical", True)
        
        # Create SVG root element
        svg = Element("svg", {
            "width": str(width),
            "height": str(height),
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": f"0 0 {width} {height}"
        })
        
        # Add styles
        style = SubElement(svg, "style")
        style.text = """
        .node { cursor: pointer; }
        .node text { font-family: Arial, sans-serif; font-size: 12px; }
        .edge { stroke-width: 2; fill: none; }
        .edge-label { font-family: Arial, sans-serif; font-size: 10px; fill: #666; }
        """
        
        # Scale positions to fit SVG
        nodes = viz_data["nodes"]
        if nodes and any("x" in node for node in nodes):
            # Calculate scaling
            x_coords = [node["x"] for node in nodes if "x" in node]
            y_coords = [node["y"] for node in nodes if "y" in node]
            
            if x_coords and y_coords:
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                # Add padding
                padding = 50
                scale_x = (width - 2 * padding) / max(1, x_max - x_min)
                scale_y = (height - 2 * padding) / max(1, y_max - y_min)
                scale = min(scale_x, scale_y, 2.0)  # Cap scaling
                
                # Draw edges first (so they appear behind nodes)
                for edge in viz_data["edges"]:
                    source_node = next(n for n in nodes if n["id"] == edge["source"])
                    target_node = next(n for n in nodes if n["id"] == edge["target"])
                    
                    if "x" in source_node and "x" in target_node:
                        x1 = (source_node["x"] - x_min) * scale + padding
                        y1 = (source_node["y"] - y_min) * scale + padding
                        x2 = (target_node["x"] - x_min) * scale + padding
                        y2 = (target_node["y"] - y_min) * scale + padding
                        
                        # Draw edge line
                        line = SubElement(svg, "line", {
                            "x1": str(x1), "y1": str(y1),
                            "x2": str(x2), "y2": str(y2),
                            "stroke": edge["color"],
                            "class": "edge"
                        })
                        
                        # Add arrowhead
                        self._add_svg_arrowhead(svg, x1, y1, x2, y2, edge["color"])
                
                # Draw nodes
                for node in nodes:
                    if "x" in node:
                        x = (node["x"] - x_min) * scale + padding
                        y = (node["y"] - y_min) * scale + padding
                        
                        # Node group
                        g = SubElement(svg, "g", {"class": "node"})
                        
                        # Node circle
                        circle = SubElement(g, "circle", {
                            "cx": str(x), "cy": str(y),
                            "r": str(node.get("size", 20)),
                            "fill": node["color"],
                            "stroke": "#ffffff",
                            "stroke-width": "2"
                        })
                        
                        # Node label
                        text = SubElement(g, "text", {
                            "x": str(x), "y": str(y + node.get("size", 20) + 15),
                            "text-anchor": "middle"
                        })
                        text.text = node["name"][:20]  # Truncate long names
        
        return tostring(svg, encoding="unicode")
    
    def export_as_dot(self, graph: LineageGraph) -> str:
        """
        Export lineage graph as DOT format (Graphviz).
        
        Args:
            graph: Lineage graph to export
            
        Returns:
            DOT format string
        """
        lines = ["digraph lineage {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=filled];")
        lines.append("")
        
        # Add nodes
        for node in graph.nodes:
            color = self.node_colors.get(node.type, "#6B7280")
            shape = "box" if node.type == NodeType.TABLE else "ellipse"
            
            lines.append(f'  "{node.id}" [')
            lines.append(f'    label="{node.name}",')
            lines.append(f'    fillcolor="{color}",')
            lines.append(f'    shape="{shape}",')
            lines.append(f'    tooltip="{node.description or node.name}"')
            lines.append("  ];")
        
        lines.append("")
        
        # Add edges
        for edge in graph.edges:
            style = "solid"
            if edge.type == EdgeType.JOINS_WITH:
                style = "dashed"
            elif edge.type == EdgeType.REFERENCES:
                style = "dotted"
            
            lines.append(f'  "{edge.source}" -> "{edge.target}" [')
            lines.append(f'    label="{edge.label or edge.type}",')
            lines.append(f'    style="{style}",')
            lines.append(f'    color="{self.edge_colors.get(edge.type, "#6B7280")}"')
            lines.append("  ];")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def export_as_json(self, graph: LineageGraph) -> str:
        """
        Export lineage graph as JSON.
        
        Args:
            graph: Lineage graph to export
            
        Returns:
            JSON string
        """
        viz_data = self.generate_visualization_data(graph, include_positions=False)
        return json.dumps(viz_data, indent=2, default=str)
    
    def _apply_hierarchical_layout(self, graph: LineageGraph) -> Dict[str, Any]:
        """Apply hierarchical layout algorithm"""
        # Build adjacency list and find root nodes
        adjacency = {}
        in_degree = {}
        
        for node in graph.nodes:
            adjacency[node.id] = []
            in_degree[node.id] = 0
        
        for edge in graph.edges:
            if edge.source in adjacency and edge.target in adjacency:
                adjacency[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        # Topological sort to assign levels
        levels = {}
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        current_level = 0
        
        while queue:
            next_queue = []
            for node_id in queue:
                levels[node_id] = current_level
                for neighbor in adjacency[node_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            
            queue = next_queue
            current_level += 1
        
        # Assign positions
        level_width = 200
        node_height = 80
        level_counts = {}
        
        for node_id, level in levels.items():
            level_counts[level] = level_counts.get(level, 0) + 1
        
        level_positions = {}
        for level in level_counts:
            level_positions[level] = 0
        
        positioned_nodes = []
        for node in graph.nodes:
            level = levels.get(node.id, 0)
            x = level * level_width
            y = level_positions[level] * node_height
            level_positions[level] += 1
            
            positioned_nodes.append({
                "id": node.id,
                "x": x,
                "y": y
            })
        
        return {"nodes": positioned_nodes, "algorithm": "hierarchical"}
    
    def _apply_force_directed_layout(self, graph: LineageGraph) -> Dict[str, Any]:
        """Apply simple force-directed layout algorithm"""
        import random
        
        # Initialize positions randomly
        positions = {}
        for node in graph.nodes:
            positions[node.id] = {
                "x": random.uniform(0, 800),
                "y": random.uniform(0, 600)
            }
        
        # Simple force-directed algorithm
        iterations = 100
        k = 50  # Optimal distance
        
        for _ in range(iterations):
            forces = {node.id: {"x": 0, "y": 0} for node in graph.nodes}
            
            # Repulsive forces between all nodes
            for i, node1 in enumerate(graph.nodes):
                for node2 in graph.nodes[i+1:]:
                    dx = positions[node2.id]["x"] - positions[node1.id]["x"]
                    dy = positions[node2.id]["y"] - positions[node1.id]["y"]
                    distance = math.sqrt(dx*dx + dy*dy) or 1
                    
                    force = k * k / distance
                    fx = force * dx / distance
                    fy = force * dy / distance
                    
                    forces[node1.id]["x"] -= fx
                    forces[node1.id]["y"] -= fy
                    forces[node2.id]["x"] += fx
                    forces[node2.id]["y"] += fy
            
            # Attractive forces between connected nodes
            for edge in graph.edges:
                if edge.source in positions and edge.target in positions:
                    dx = positions[edge.target]["x"] - positions[edge.source]["x"]
                    dy = positions[edge.target]["y"] - positions[edge.source]["y"]
                    distance = math.sqrt(dx*dx + dy*dy) or 1
                    
                    force = distance * distance / k
                    fx = force * dx / distance
                    fy = force * dy / distance
                    
                    forces[edge.source]["x"] += fx
                    forces[edge.source]["y"] += fy
                    forces[edge.target]["x"] -= fx
                    forces[edge.target]["y"] -= fy
            
            # Apply forces
            for node_id in positions:
                positions[node_id]["x"] += forces[node_id]["x"] * 0.1
                positions[node_id]["y"] += forces[node_id]["y"] * 0.1
        
        positioned_nodes = [
            {"id": node_id, "x": pos["x"], "y": pos["y"]}
            for node_id, pos in positions.items()
        ]
        
        return {"nodes": positioned_nodes, "algorithm": "force-directed"}
    
    def _apply_circular_layout(self, graph: LineageGraph) -> Dict[str, Any]:
        """Apply circular layout algorithm"""
        nodes = graph.nodes
        if not nodes:
            return {"nodes": [], "algorithm": "circular"}
        
        center_x, center_y = 400, 300
        radius = min(300, 200 + len(nodes) * 10)
        
        positioned_nodes = []
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            positioned_nodes.append({
                "id": node.id,
                "x": x,
                "y": y
            })
        
        return {"nodes": positioned_nodes, "algorithm": "circular"}
    
    def _apply_tree_layout(self, graph: LineageGraph) -> Dict[str, Any]:
        """Apply tree layout algorithm"""
        # Similar to hierarchical but with tree-specific spacing
        return self._apply_hierarchical_layout(graph)
    
    def _get_node_icon(self, node_type: NodeType) -> str:
        """Get icon identifier for node type"""
        icon_map = {
            NodeType.TABLE: "table",
            NodeType.VIEW: "view",
            NodeType.MODEL: "model",
            NodeType.METRIC: "metric",
            NodeType.DIMENSION: "dimension",
            NodeType.COLUMN: "column",
            NodeType.FILE: "file",
            NodeType.EXTERNAL: "external"
        }
        return icon_map.get(node_type, "default")
    
    def _get_node_size(self, node: LineageNode) -> int:
        """Calculate node size based on importance"""
        size_map = {
            NodeType.MODEL: 30,
            NodeType.METRIC: 25,
            NodeType.TABLE: 20,
            NodeType.VIEW: 18,
            NodeType.DIMENSION: 16,
            NodeType.COLUMN: 14,
            NodeType.FILE: 12,
            NodeType.EXTERNAL: 15
        }
        return size_map.get(node.type, 16)
    
    def _get_node_shape(self, node_type: NodeType) -> str:
        """Get shape for node type"""
        shape_map = {
            NodeType.TABLE: "rectangle",
            NodeType.VIEW: "ellipse",
            NodeType.MODEL: "diamond",
            NodeType.METRIC: "hexagon",
            NodeType.DIMENSION: "triangle",
            NodeType.COLUMN: "circle",
            NodeType.FILE: "rectangle",
            NodeType.EXTERNAL: "star"
        }
        return shape_map.get(node_type, "circle")
    
    def _get_edge_label(self, edge_type: EdgeType) -> str:
        """Get display label for edge type"""
        label_map = {
            EdgeType.DERIVES_FROM: "derives from",
            EdgeType.JOINS_WITH: "joins with",
            EdgeType.FILTERS_FROM: "filters",
            EdgeType.AGGREGATES_FROM: "aggregates",
            EdgeType.REFERENCES: "references",
            EdgeType.CONTAINS: "contains",
            EdgeType.TRANSFORMS_TO: "transforms to"
        }
        return label_map.get(edge_type, edge_type)
    
    def _get_edge_style(self, edge_type: EdgeType) -> str:
        """Get line style for edge type"""
        style_map = {
            EdgeType.DERIVES_FROM: "solid",
            EdgeType.JOINS_WITH: "dashed",
            EdgeType.FILTERS_FROM: "solid",
            EdgeType.AGGREGATES_FROM: "solid",
            EdgeType.REFERENCES: "dotted",
            EdgeType.CONTAINS: "solid",
            EdgeType.TRANSFORMS_TO: "solid"
        }
        return style_map.get(edge_type, "solid")
    
    def _should_animate_edge(self, edge_type: EdgeType) -> bool:
        """Determine if edge should be animated"""
        return edge_type in [EdgeType.TRANSFORMS_TO, EdgeType.DERIVES_FROM]
    
    def _calculate_graph_stats(self, graph: LineageGraph) -> Dict[str, Any]:
        """Calculate statistics about the graph"""
        node_types = {}
        edge_types = {}
        
        for node in graph.nodes:
            node_types[node.type] = node_types.get(node.type, 0) + 1
        
        for edge in graph.edges:
            edge_types[edge.type] = edge_types.get(edge.type, 0) + 1
        
        return {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "node_types": node_types,
            "edge_types": edge_types,
            "density": len(graph.edges) / max(1, len(graph.nodes) * (len(graph.nodes) - 1))
        }
    
    def _calculate_spacing(self, node_count: int) -> Dict[str, int]:
        """Calculate optimal spacing based on node count"""
        base_spacing = 100
        scaling_factor = min(2.0, 1.0 + node_count / 50)
        
        return {
            "node_spacing": int(base_spacing * scaling_factor),
            "level_spacing": int(base_spacing * 1.5 * scaling_factor),
            "edge_spacing": int(base_spacing * 0.5)
        }
    
    def _calculate_bounds(self, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """Calculate bounding box for positioned nodes"""
        if not nodes or not any("x" in node for node in nodes):
            return None
        
        x_coords = [node["x"] for node in nodes if "x" in node]
        y_coords = [node["y"] for node in nodes if "y" in node]
        
        if not x_coords or not y_coords:
            return None
        
        return {
            "minX": min(x_coords),
            "maxX": max(x_coords),
            "minY": min(y_coords),
            "maxY": max(y_coords),
            "width": max(x_coords) - min(x_coords),
            "height": max(y_coords) - min(y_coords)
        }
    
    def _add_svg_arrowhead(
        self, 
        svg: Element, 
        x1: float, 
        y1: float, 
        x2: float, 
        y2: float, 
        color: str
    ):
        """Add arrowhead to SVG line"""
        # Calculate arrowhead position and angle
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            # Normalize direction
            dx /= length
            dy /= length
            
            # Arrowhead size
            size = 8
            
            # Calculate arrowhead points
            x_back = x2 - dx * size
            y_back = y2 - dy * size
            
            # Perpendicular direction
            px = -dy * size * 0.5
            py = dx * size * 0.5
            
            # Arrowhead polygon
            points = f"{x2},{y2} {x_back + px},{y_back + py} {x_back - px},{y_back - py}"
            
            polygon = SubElement(svg, "polygon", {
                "points": points,
                "fill": color,
                "stroke": color
            })
