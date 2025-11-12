"""
Comprehensive unit tests for lineage visualization feature.
Tests cover lineage extraction, processing, and API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from app.models.lineage import (
    LineageNode,
    LineageEdge,
    LineageGraph,
    NodeType,
    EdgeType,
    LineageDirection,
    LineageRequest,
    LineageResponse,
    LineageMetadata
)
from app.services.lineage_extractor import LineageExtractor
from app.services.lineage_processor import LineageProcessor
from app.services.lineage_visualizer import LineageVisualizer
from app.api.lineage import router


class TestLineageModels:
    """Test Pydantic models for lineage data structures"""
    
    def test_lineage_node_creation(self):
        """Test creating a lineage node"""
        node = LineageNode(
            id="table.catalog.schema.table1",
            name="table1",
            type=NodeType.TABLE,
            catalog="catalog",
            schema="schema",
            metadata={
                "row_count": 1000,
                "size_mb": 50.5,
                "last_modified": "2024-01-01T00:00:00Z"
            }
        )
        
        assert node.id == "table.catalog.schema.table1"
        assert node.name == "table1"
        assert node.type == NodeType.TABLE
        assert node.catalog == "catalog"
        assert node.schema == "schema"
        assert node.metadata["row_count"] == 1000
    
    def test_lineage_edge_creation(self):
        """Test creating a lineage edge"""
        edge = LineageEdge(
            id="edge1",
            source="table1",
            target="table2",
            type=EdgeType.DERIVES_FROM,
            metadata={
                "transformation": "SELECT * FROM table1",
                "created_at": "2024-01-01T00:00:00Z"
            }
        )
        
        assert edge.id == "edge1"
        assert edge.source == "table1"
        assert edge.target == "table2"
        assert edge.type == EdgeType.DERIVES_FROM
        assert edge.metadata["transformation"] == "SELECT * FROM table1"
    
    def test_lineage_graph_creation(self):
        """Test creating a lineage graph"""
        nodes = [
            LineageNode(
                id="node1",
                name="table1",
                type=NodeType.TABLE
            ),
            LineageNode(
                id="node2",
                name="table2",
                type=NodeType.TABLE
            )
        ]
        
        edges = [
            LineageEdge(
                id="edge1",
                source="node1",
                target="node2",
                type=EdgeType.DERIVES_FROM
            )
        ]
        
        graph = LineageGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "generated_at": "2024-01-01T00:00:00Z"
            }
        )
        
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.metadata["generated_at"] == "2024-01-01T00:00:00Z"


class TestLineageExtractor:
    """Test the LineageExtractor service"""
    
    @pytest.fixture
    def mock_connector(self):
        """Create a mock Databricks connector"""
        return Mock()
    
    @pytest.fixture
    def extractor(self, mock_connector):
        """Create a LineageExtractor instance with mock connector"""
        return LineageExtractor(mock_connector)
    
    def test_extract_table_lineage_upstream(self, extractor, mock_connector):
        """Test extracting upstream lineage for a table"""
        # Mock Unity Catalog lineage response
        mock_connector.execute_query.return_value = [
            {
                "source_type": "TABLE",
                "source_name": "catalog.schema.source_table1",
                "target_type": "TABLE", 
                "target_name": "catalog.schema.target_table",
                "edge_type": "DERIVES_FROM",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "source_type": "TABLE",
                "source_name": "catalog.schema.source_table2",
                "target_type": "TABLE",
                "target_name": "catalog.schema.target_table",
                "edge_type": "DERIVES_FROM",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        result = extractor.extract_table_lineage(
            catalog="catalog",
            schema="schema",
            table="target_table",
            direction=LineageDirection.UPSTREAM,
            depth=1
        )
        
        assert isinstance(result, LineageGraph)
        assert len(result.nodes) == 3  # target_table + 2 source tables
        assert len(result.edges) == 2
        
        # Verify the query was called correctly
        mock_connector.execute_query.assert_called_once()
        query = mock_connector.execute_query.call_args[0][0]
        assert "catalog.schema.target_table" in query
    
    def test_extract_table_lineage_downstream(self, extractor, mock_connector):
        """Test extracting downstream lineage for a table"""
        mock_connector.execute_query.return_value = [
            {
                "source_type": "TABLE",
                "source_name": "catalog.schema.source_table",
                "target_type": "TABLE",
                "target_name": "catalog.schema.downstream_table1",
                "edge_type": "DERIVES_FROM",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        result = extractor.extract_table_lineage(
            catalog="catalog",
            schema="schema",
            table="source_table",
            direction=LineageDirection.DOWNSTREAM,
            depth=1
        )
        
        assert len(result.nodes) == 2
        assert len(result.edges) == 1
    
    def test_extract_model_lineage(self, extractor, mock_connector):
        """Test extracting lineage for a semantic model"""
        # Mock model metadata
        mock_connector.execute_query.side_effect = [
            # First call: Get model tables
            [
                {"table_name": "catalog.schema.fact_sales"},
                {"table_name": "catalog.schema.dim_customer"}
            ],
            # Second call: Get lineage for fact_sales
            [
                {
                    "source_type": "TABLE",
                    "source_name": "catalog.schema.raw_sales",
                    "target_type": "TABLE",
                    "target_name": "catalog.schema.fact_sales",
                    "edge_type": "DERIVES_FROM",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            # Third call: Get lineage for dim_customer
            [
                {
                    "source_type": "TABLE",
                    "source_name": "catalog.schema.raw_customer",
                    "target_type": "TABLE",
                    "target_name": "catalog.schema.dim_customer",
                    "edge_type": "DERIVES_FROM",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        ]
        
        result = extractor.extract_model_lineage(
            model_id="sales_model",
            include_upstream=True,
            include_downstream=False
        )
        
        assert isinstance(result, LineageGraph)
        # Should have model node + 2 model tables + 2 upstream tables
        assert len(result.nodes) >= 4
        assert any(node.type == NodeType.MODEL for node in result.nodes)
    
    def test_extract_column_lineage(self, extractor, mock_connector):
        """Test extracting column-level lineage"""
        mock_connector.execute_query.return_value = [
            {
                "source_column": "catalog.schema.source_table.col1",
                "target_column": "catalog.schema.target_table.result_col",
                "transformation": "CAST(col1 AS STRING)",
                "confidence": 0.95
            }
        ]
        
        result = extractor.extract_column_lineage(
            catalog="catalog",
            schema="schema",
            table="target_table",
            column="result_col"
        )
        
        assert isinstance(result, LineageGraph)
        # Should have nodes for both columns
        assert any(node.type == NodeType.COLUMN for node in result.nodes)
        assert len(result.edges) == 1
        assert result.edges[0].metadata["transformation"] == "CAST(col1 AS STRING)"


class TestLineageProcessor:
    """Test the LineageProcessor service"""
    
    @pytest.fixture
    def processor(self):
        """Create a LineageProcessor instance"""
        return LineageProcessor()
    
    def test_process_graph_deduplication(self, processor):
        """Test that processor deduplicates nodes and edges"""
        # Create graph with duplicate nodes
        nodes = [
            LineageNode(id="node1", name="table1", type=NodeType.TABLE),
            LineageNode(id="node1", name="table1", type=NodeType.TABLE),  # Duplicate
            LineageNode(id="node2", name="table2", type=NodeType.TABLE)
        ]
        
        edges = [
            LineageEdge(id="edge1", source="node1", target="node2", type=EdgeType.DERIVES_FROM),
            LineageEdge(id="edge1", source="node1", target="node2", type=EdgeType.DERIVES_FROM)  # Duplicate
        ]
        
        graph = LineageGraph(nodes=nodes, edges=edges)
        processed = processor.process_graph(graph)
        
        assert len(processed.nodes) == 2  # Duplicates removed
        assert len(processed.edges) == 1  # Duplicates removed
    
    def test_filter_by_node_types(self, processor):
        """Test filtering graph by node types"""
        nodes = [
            LineageNode(id="table1", name="table1", type=NodeType.TABLE),
            LineageNode(id="view1", name="view1", type=NodeType.VIEW),
            LineageNode(id="model1", name="model1", type=NodeType.MODEL)
        ]
        
        graph = LineageGraph(nodes=nodes, edges=[])
        
        # Filter to only tables and views
        filtered = processor.filter_by_node_types(
            graph, 
            [NodeType.TABLE, NodeType.VIEW]
        )
        
        assert len(filtered.nodes) == 2
        assert all(node.type in [NodeType.TABLE, NodeType.VIEW] for node in filtered.nodes)
    
    def test_calculate_impact_analysis(self, processor):
        """Test calculating impact analysis for lineage changes"""
        nodes = [
            LineageNode(id="source", name="source", type=NodeType.TABLE),
            LineageNode(id="intermediate", name="intermediate", type=NodeType.TABLE),
            LineageNode(id="target", name="target", type=NodeType.TABLE)
        ]
        
        edges = [
            LineageEdge(id="e1", source="source", target="intermediate", type=EdgeType.DERIVES_FROM),
            LineageEdge(id="e2", source="intermediate", target="target", type=EdgeType.DERIVES_FROM)
        ]
        
        graph = LineageGraph(nodes=nodes, edges=edges)
        
        # Calculate impact of changing source table
        impact = processor.calculate_impact_analysis(graph, "source")
        
        assert len(impact["directly_impacted"]) == 1  # intermediate
        assert len(impact["indirectly_impacted"]) == 1  # target
        assert impact["total_impact_count"] == 2
    
    def test_detect_cycles(self, processor):
        """Test detecting cycles in lineage graph"""
        nodes = [
            LineageNode(id="node1", name="table1", type=NodeType.TABLE),
            LineageNode(id="node2", name="table2", type=NodeType.TABLE),
            LineageNode(id="node3", name="table3", type=NodeType.TABLE)
        ]
        
        # Create a cycle: node1 -> node2 -> node3 -> node1
        edges = [
            LineageEdge(id="e1", source="node1", target="node2", type=EdgeType.DERIVES_FROM),
            LineageEdge(id="e2", source="node2", target="node3", type=EdgeType.DERIVES_FROM),
            LineageEdge(id="e3", source="node3", target="node1", type=EdgeType.DERIVES_FROM)
        ]
        
        graph = LineageGraph(nodes=nodes, edges=edges)
        cycles = processor.detect_cycles(graph)
        
        assert len(cycles) > 0
        assert "node1" in cycles[0]
        assert "node2" in cycles[0]
        assert "node3" in cycles[0]


class TestLineageVisualizer:
    """Test the LineageVisualizer service"""
    
    @pytest.fixture
    def visualizer(self):
        """Create a LineageVisualizer instance"""
        return LineageVisualizer()
    
    def test_generate_visualization_data(self, visualizer):
        """Test generating visualization data from lineage graph"""
        nodes = [
            LineageNode(
                id="table1",
                name="fact_sales",
                type=NodeType.TABLE,
                catalog="prod",
                schema="gold"
            ),
            LineageNode(
                id="table2", 
                name="dim_customer",
                type=NodeType.TABLE,
                catalog="prod",
                schema="gold"
            )
        ]
        
        edges = [
            LineageEdge(
                id="e1",
                source="table1",
                target="table2",
                type=EdgeType.JOINS_WITH
            )
        ]
        
        graph = LineageGraph(nodes=nodes, edges=edges)
        viz_data = visualizer.generate_visualization_data(graph)
        
        assert "nodes" in viz_data
        assert "edges" in viz_data
        assert "layout" in viz_data
        assert len(viz_data["nodes"]) == 2
        assert len(viz_data["edges"]) == 1
    
    def test_apply_layout_algorithm(self, visualizer):
        """Test applying different layout algorithms"""
        nodes = [
            LineageNode(id=f"node{i}", name=f"table{i}", type=NodeType.TABLE)
            for i in range(5)
        ]
        
        edges = [
            LineageEdge(id=f"e{i}", source=f"node{i}", target=f"node{i+1}", type=EdgeType.DERIVES_FROM)
            for i in range(4)
        ]
        
        graph = LineageGraph(nodes=nodes, edges=edges)
        
        # Test hierarchical layout
        hierarchical = visualizer.apply_layout_algorithm(graph, "hierarchical")
        assert all("x" in node and "y" in node for node in hierarchical["nodes"])
        
        # Test force-directed layout  
        force = visualizer.apply_layout_algorithm(graph, "force-directed")
        assert all("x" in node and "y" in node for node in force["nodes"])
    
    def test_generate_export_formats(self, visualizer):
        """Test exporting lineage visualization in different formats"""
        graph = LineageGraph(
            nodes=[
                LineageNode(id="n1", name="table1", type=NodeType.TABLE)
            ],
            edges=[]
        )
        
        # Test SVG export
        svg = visualizer.export_as_svg(graph)
        assert svg.startswith("<svg")
        assert "</svg>" in svg
        
        # Test DOT export (Graphviz)
        dot = visualizer.export_as_dot(graph)
        assert "digraph" in dot
        assert "table1" in dot
        
        # Test JSON export
        json_export = visualizer.export_as_json(graph)
        data = json.loads(json_export)
        assert "nodes" in data
        assert "edges" in data


class TestLineageAPI:
    """Test the lineage API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    @patch('app.api.lineage.LineageExtractor')
    @patch('app.api.lineage.require_auth')
    def test_get_table_lineage_endpoint(self, mock_auth, mock_extractor_class, client):
        """Test GET /api/v1/lineage/table endpoint"""
        # Mock authentication
        mock_auth.return_value = {"user_id": "test_user"}
        
        # Mock extractor
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        
        # Mock lineage response
        mock_graph = LineageGraph(
            nodes=[
                LineageNode(id="t1", name="table1", type=NodeType.TABLE)
            ],
            edges=[]
        )
        mock_extractor.extract_table_lineage.return_value = mock_graph
        
        response = client.get(
            "/api/v1/lineage/table",
            params={
                "catalog": "prod",
                "schema": "gold",
                "table": "fact_sales",
                "direction": "both",
                "depth": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 1
    
    @patch('app.api.lineage.LineageExtractor')
    @patch('app.api.lineage.require_auth')
    def test_get_model_lineage_endpoint(self, mock_auth, mock_extractor_class, client):
        """Test GET /api/v1/lineage/model/{model_id} endpoint"""
        mock_auth.return_value = {"user_id": "test_user"}
        
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        
        mock_graph = LineageGraph(
            nodes=[
                LineageNode(id="m1", name="sales_model", type=NodeType.MODEL)
            ],
            edges=[]
        )
        mock_extractor.extract_model_lineage.return_value = mock_graph
        
        response = client.get("/api/v1/lineage/model/sales_model")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["type"] == "MODEL"
    
    @patch('app.api.lineage.LineageProcessor')
    @patch('app.api.lineage.require_auth')
    def test_analyze_impact_endpoint(self, mock_auth, mock_processor_class, client):
        """Test POST /api/v1/lineage/impact endpoint"""
        mock_auth.return_value = {"user_id": "test_user"}
        
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        mock_processor.calculate_impact_analysis.return_value = {
            "directly_impacted": ["table2", "table3"],
            "indirectly_impacted": ["table4"],
            "total_impact_count": 3
        }
        
        response = client.post(
            "/api/v1/lineage/impact",
            json={
                "entity_id": "table1",
                "entity_type": "TABLE",
                "change_type": "schema_change"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_impact_count"] == 3
        assert len(data["directly_impacted"]) == 2
    
    @patch('app.api.lineage.LineageVisualizer')
    @patch('app.api.lineage.require_auth')
    def test_export_lineage_endpoint(self, mock_auth, mock_visualizer_class, client):
        """Test POST /api/v1/lineage/export endpoint"""
        mock_auth.return_value = {"user_id": "test_user"}
        
        mock_visualizer = Mock()
        mock_visualizer_class.return_value = mock_visualizer
        
        # Mock export methods
        mock_visualizer.export_as_svg.return_value = "<svg>test</svg>"
        mock_visualizer.export_as_dot.return_value = "digraph { test }"
        mock_visualizer.export_as_json.return_value = '{"nodes": [], "edges": []}'
        
        # Test SVG export
        response = client.post(
            "/api/v1/lineage/export",
            json={
                "graph": {"nodes": [], "edges": []},
                "format": "svg"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        
        # Test DOT export
        response = client.post(
            "/api/v1/lineage/export",
            json={
                "graph": {"nodes": [], "edges": []},
                "format": "dot"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain"


class TestLineageIntegration:
    """Integration tests for lineage visualization"""
    
    @pytest.fixture
    def mock_databricks(self):
        """Mock Databricks environment"""
        with patch('app.integrations.databricks.DatabricksConnector') as mock:
            yield mock
    
    def test_end_to_end_table_lineage(self, mock_databricks):
        """Test complete flow from API to visualization"""
        # Setup mock responses
        mock_connector = Mock()
        mock_databricks.return_value = mock_connector
        
        # Mock Unity Catalog lineage data
        mock_connector.execute_query.return_value = [
            {
                "source_type": "TABLE",
                "source_name": "raw.events.user_activity",
                "target_type": "TABLE",
                "target_name": "silver.events.cleaned_activity",
                "edge_type": "DERIVES_FROM",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "source_type": "TABLE", 
                "source_name": "silver.events.cleaned_activity",
                "target_type": "TABLE",
                "target_name": "gold.analytics.user_metrics",
                "edge_type": "DERIVES_FROM",
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        
        # Create services
        extractor = LineageExtractor(mock_connector)
        processor = LineageProcessor()
        visualizer = LineageVisualizer()
        
        # Extract lineage
        graph = extractor.extract_table_lineage(
            catalog="gold",
            schema="analytics", 
            table="user_metrics",
            direction=LineageDirection.UPSTREAM,
            depth=3
        )
        
        # Process graph
        processed = processor.process_graph(graph)
        
        # Generate visualization
        viz_data = visualizer.generate_visualization_data(processed)
        
        # Verify complete lineage chain
        assert len(viz_data["nodes"]) >= 3
        assert any(n["name"] == "user_activity" for n in viz_data["nodes"])
        assert any(n["name"] == "cleaned_activity" for n in viz_data["nodes"])
        assert any(n["name"] == "user_metrics" for n in viz_data["nodes"])
        
        # Verify edges connect the chain
        assert len(viz_data["edges"]) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

