"""
Volume-based metric store using Unity Catalog Volumes for scalable YAML storage.
"""

import os
import json
import hashlib
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import structlog
from databricks.sdk import WorkspaceClient
# from databricks.sdk.service.files import DownloadFormat  # Not available in this SDK version
from pydantic import BaseModel

from ..models.semantic import SemanticModel
from ..core.config import settings

logger = structlog.get_logger(__name__)


class CacheConfig(BaseModel):
    """Configuration for metric caching behavior."""
    ttl: str = "1h"
    refresh_frequency: str = "15m" 
    pre_aggregate: bool = False
    dimensions: List[str] = []


class GovernanceMetadata(BaseModel):
    """Governance metadata for metrics."""
    access_level: str = "internal"  # public, internal, confidential, restricted
    approval_required: bool = False
    approved_by: Optional[str] = None
    approved_date: Optional[str] = None
    tags: List[str] = []


class EnhancedMetricModel(SemanticModel):
    """Enhanced semantic model with caching and governance metadata."""
    cache_config: Optional[CacheConfig] = None
    governance: Optional[GovernanceMetadata] = None
    usage_count: int = 0
    last_accessed: Optional[datetime] = None


class VolumeMetricStore:
    """
    Unity Catalog Volume-based storage for semantic models with intelligent caching.
    """
    
    def __init__(self):
        self.client = WorkspaceClient()
        self.volume_base_path = "/Volumes/semantic_layer/metrics"
        self.cache: Dict[str, EnhancedMetricModel] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl = timedelta(minutes=30)
        
        # Initialize volume structure
        self._ensure_volume_structure()
        
    def _ensure_volume_structure(self):
        """Ensure the required volume directory structure exists."""
        try:
            volumes = [
                f"{self.volume_base_path}/production_models",
                f"{self.volume_base_path}/staging_models", 
                f"{self.volume_base_path}/templates",
                f"{self.volume_base_path}/archives"
            ]
            
            for volume_path in volumes:
                try:
                    self.client.files.get_directory_metadata(directory_path=volume_path)
                    logger.info(f"Volume directory exists: {volume_path}")
                except Exception:
                    logger.info(f"Volume directory needs to be created: {volume_path}")
                    
        except Exception as e:
            logger.warning(f"Could not verify volume structure: {e}")
    
    def _get_volume_path(self, category: str = "production_models") -> str:
        """Get the appropriate volume path for a category."""
        return f"{self.volume_base_path}/{category}"
    
    def _generate_cache_key(self, metric_id: str, category: str) -> str:
        """Generate cache key for a metric."""
        return f"{category}:{metric_id}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached item is still valid."""
        if cache_key not in self.cache_timestamps:
            return False
        return datetime.now() - self.cache_timestamps[cache_key] < self.cache_ttl
    
    def _load_metric_from_volume(self, metric_id: str, category: str = "production_models") -> Optional[EnhancedMetricModel]:
        """Load a metric from Unity Catalog Volume."""
        try:
            volume_path = self._get_volume_path(category)
            file_path = f"{volume_path}/{metric_id}.yml"
            
            # Download file from volume
            response = self.client.files.download(
                file_path=file_path,
                # format=DownloadFormat.AUTO  # Not available in this SDK version
            )
            
            # Parse YAML content
            yaml_content = response.contents.decode('utf-8')
            metric_data = yaml.safe_load(yaml_content)
            
            # Convert to enhanced model
            enhanced_metric = EnhancedMetricModel(**metric_data)
            
            logger.info(f"Loaded metric {metric_id} from volume {category}")
            return enhanced_metric
            
        except Exception as e:
            logger.error(f"Failed to load metric {metric_id} from volume: {e}")
            return None
    
    def get_metric(self, metric_id: str, category: str = "production_models") -> Optional[EnhancedMetricModel]:
        """
        Get a metric with intelligent caching.
        
        Args:
            metric_id: Unique metric identifier
            category: Volume category (production_models, staging_models, etc.)
            
        Returns:
            Enhanced metric model if found, None otherwise
        """
        cache_key = self._generate_cache_key(metric_id, category)
        
        # Check cache first
        if cache_key in self.cache and self._is_cache_valid(cache_key):
            metric = self.cache[cache_key]
            metric.last_accessed = datetime.now()
            metric.usage_count += 1
            logger.debug(f"Cache hit for metric {metric_id}")
            return metric
        
        # Load from volume
        metric = self._load_metric_from_volume(metric_id, category)
        if metric:
            # Update cache
            self.cache[cache_key] = metric
            self.cache_timestamps[cache_key] = datetime.now()
            metric.last_accessed = datetime.now()
            metric.usage_count = getattr(metric, 'usage_count', 0) + 1
            logger.debug(f"Cache miss - loaded metric {metric_id} from volume")
            
        return metric
    
    def save_metric(self, metric: EnhancedMetricModel, category: str = "production_models") -> bool:
        """
        Save a metric to Unity Catalog Volume.
        
        Args:
            metric: Enhanced metric model to save
            category: Target volume category
            
        Returns:
            True if successful, False otherwise
        """
        try:
            volume_path = self._get_volume_path(category)
            file_path = f"{volume_path}/{metric.name}.yml"
            
            # Convert to YAML
            metric_dict = metric.model_dump(exclude_unset=True)
            yaml_content = yaml.safe_dump(metric_dict, default_flow_style=False, sort_keys=False)
            
            # Upload to volume
            self.client.files.upload(
                file_path=file_path,
                contents=yaml_content.encode('utf-8'),
                overwrite=True
            )
            
            # Update cache
            cache_key = self._generate_cache_key(metric.name, category)
            self.cache[cache_key] = metric
            self.cache_timestamps[cache_key] = datetime.now()
            
            logger.info(f"Saved metric {metric.name} to volume {category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save metric {metric.name}: {e}")
            return False
    
    def list_metrics(self, category: str = "production_models") -> List[str]:
        """
        List all metrics in a volume category.
        
        Args:
            category: Volume category to list
            
        Returns:
            List of metric names
        """
        try:
            volume_path = self._get_volume_path(category)
            
            # List files in volume directory
            files = self.client.files.list_directory_contents(directory_path=volume_path)
            
            # Filter YAML files and extract metric names
            metric_names = []
            for file_info in files:
                if file_info.name.endswith('.yml') or file_info.name.endswith('.yaml'):
                    metric_name = file_info.name.rsplit('.', 1)[0]
                    metric_names.append(metric_name)
            
            logger.info(f"Found {len(metric_names)} metrics in {category}")
            return sorted(metric_names)
            
        except Exception as e:
            logger.error(f"Failed to list metrics in {category}: {e}")
            return []
    
    def delete_metric(self, metric_id: str, category: str = "production_models") -> bool:
        """
        Delete a metric from volume and cache.
        
        Args:
            metric_id: Metric to delete
            category: Volume category
            
        Returns:
            True if successful, False otherwise
        """
        try:
            volume_path = self._get_volume_path(category)
            file_path = f"{volume_path}/{metric_id}.yml"
            
            # Delete from volume
            self.client.files.delete(file_path=file_path)
            
            # Remove from cache
            cache_key = self._generate_cache_key(metric_id, category)
            if cache_key in self.cache:
                del self.cache[cache_key]
            if cache_key in self.cache_timestamps:
                del self.cache_timestamps[cache_key]
            
            logger.info(f"Deleted metric {metric_id} from {category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete metric {metric_id}: {e}")
            return False
    
    def move_metric(self, metric_id: str, from_category: str, to_category: str) -> bool:
        """
        Move a metric between volume categories.
        
        Args:
            metric_id: Metric to move
            from_category: Source category
            to_category: Destination category
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load metric from source
            metric = self.get_metric(metric_id, from_category)
            if not metric:
                return False
            
            # Save to destination
            if not self.save_metric(metric, to_category):
                return False
            
            # Delete from source
            if not self.delete_metric(metric_id, from_category):
                # Rollback - delete from destination
                self.delete_metric(metric_id, to_category)
                return False
            
            logger.info(f"Moved metric {metric_id} from {from_category} to {to_category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move metric {metric_id}: {e}")
            return False
    
    def get_metrics_with_cache_config(self) -> List[EnhancedMetricModel]:
        """Get all metrics that have caching configuration."""
        all_metrics = []
        
        for category in ["production_models", "staging_models"]:
            metric_names = self.list_metrics(category)
            for metric_name in metric_names:
                metric = self.get_metric(metric_name, category)
                if metric and metric.cache_config:
                    all_metrics.append(metric)
        
        return all_metrics
    
    def refresh_cache_from_volume(self) -> int:
        """
        Refresh the entire cache from volume changes.
        
        Returns:
            Number of metrics refreshed
        """
        refreshed_count = 0
        
        try:
            for category in ["production_models", "staging_models"]:
                metric_names = self.list_metrics(category)
                
                for metric_name in metric_names:
                    cache_key = self._generate_cache_key(metric_name, category)
                    
                    # Force reload from volume
                    if cache_key in self.cache:
                        del self.cache[cache_key]
                    if cache_key in self.cache_timestamps:
                        del self.cache_timestamps[cache_key]
                    
                    # Reload metric
                    metric = self.get_metric(metric_name, category)
                    if metric:
                        refreshed_count += 1
            
            logger.info(f"Refreshed {refreshed_count} metrics from volumes")
            return refreshed_count
            
        except Exception as e:
            logger.error(f"Failed to refresh cache from volumes: {e}")
            return refreshed_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return {
            "cached_metrics": len(self.cache),
            "cache_size_mb": sum(len(str(metric).encode('utf-8')) for metric in self.cache.values()) / 1024 / 1024,
            "oldest_cache_entry": min(self.cache_timestamps.values()) if self.cache_timestamps else None,
            "newest_cache_entry": max(self.cache_timestamps.values()) if self.cache_timestamps else None
        }