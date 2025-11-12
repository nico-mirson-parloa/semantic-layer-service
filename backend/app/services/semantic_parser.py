"""
Semantic model parser and validator
"""
from typing import Dict, Any, List
import structlog
from app.models.semantic import Entity, Dimension, Measure, Metric

logger = structlog.get_logger()


class SemanticModelParser:
    """Parse and validate semantic model YAML"""
    
    def parse(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse semantic model data"""
        if "semantic_model" not in model_data:
            raise ValueError("Invalid model format: missing 'semantic_model' key")
        
        model = model_data["semantic_model"]
        
        # Validate required fields
        required_fields = ["name", "model"]
        for field in required_fields:
            if field not in model:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse components
        parsed = {
            "name": model["name"],
            "description": model.get("description", ""),
            "model": model["model"],
            "entities": self._parse_entities(model.get("entities", [])),
            "dimensions": self._parse_dimensions(model.get("dimensions", [])),
            "measures": self._parse_measures(model.get("measures", [])),
            "metrics": self._parse_metrics(model.get("metrics", []))
        }
        
        # Validate references
        self._validate_references(parsed)
        
        return parsed
    
    def _parse_entities(self, entities: List[Dict[str, Any]]) -> List[Entity]:
        """Parse entity definitions"""
        parsed_entities = []
        for entity in entities:
            parsed_entities.append(Entity(
                name=entity["name"],
                type=entity["type"],
                expr=entity.get("expr", entity["name"])
            ))
        return parsed_entities
    
    def _parse_dimensions(self, dimensions: List[Dict[str, Any]]) -> List[Dimension]:
        """Parse dimension definitions"""
        parsed_dimensions = []
        for dim in dimensions:
            parsed_dimensions.append(Dimension(
                name=dim["name"],
                type=dim["type"],
                expr=dim.get("expr", dim["name"]),
                time_granularity=dim.get("time_granularity")
            ))
        return parsed_dimensions
    
    def _parse_measures(self, measures: List[Dict[str, Any]]) -> List[Measure]:
        """Parse measure definitions"""
        parsed_measures = []
        for measure in measures:
            parsed_measures.append(Measure(
                name=measure["name"],
                agg=measure["agg"],
                expr=measure["expr"],
                description=measure.get("description")
            ))
        return parsed_measures
    
    def _parse_metrics(self, metrics: List[Dict[str, Any]]) -> List[Metric]:
        """Parse metric definitions"""
        parsed_metrics = []
        for metric in metrics:
            parsed_metrics.append(Metric(
                name=metric["name"],
                type=metric["type"],
                measure=metric.get("measure"),
                numerator=metric.get("numerator"),
                denominator=metric.get("denominator"),
                expr=metric.get("expr"),
                description=metric.get("description")
            ))
        return parsed_metrics
    
    def _validate_references(self, parsed_model: Dict[str, Any]):
        """Validate that metrics reference existing measures"""
        measure_names = {m.name for m in parsed_model["measures"]}
        
        for metric in parsed_model["metrics"]:
            if metric.type == "simple" and metric.measure not in measure_names:
                raise ValueError(f"Metric '{metric.name}' references unknown measure '{metric.measure}'")
            
            if metric.type == "ratio":
                if metric.numerator not in measure_names:
                    raise ValueError(f"Metric '{metric.name}' references unknown numerator '{metric.numerator}'")
                if metric.denominator not in measure_names:
                    raise ValueError(f"Metric '{metric.name}' references unknown denominator '{metric.denominator}'")
