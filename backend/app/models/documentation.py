"""
Data models for documentation generation feature.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DocumentationFormat(str, Enum):
    """Supported documentation output formats"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    RST = "rst"  # ReStructuredText
    JSON = "json"  # Structured JSON format


class DocumentationTemplate(BaseModel):
    """Documentation template configuration"""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    sections: Dict[str, Dict[str, Any]] = Field(..., description="Template sections configuration")
    styles: Optional[Dict[str, Any]] = Field(None, description="Styling configuration")
    
    model_config = ConfigDict(from_attributes=True)


class DocumentationSection(BaseModel):
    """Individual section within documentation"""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    order: int = Field(1, description="Display order")
    subsections: Optional[List['DocumentationSection']] = Field(None, description="Nested subsections")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Section metadata")
    
    model_config = ConfigDict(from_attributes=True)


class DocumentationConfig(BaseModel):
    """Configuration for documentation generation"""
    format: DocumentationFormat = Field(DocumentationFormat.MARKDOWN, description="Output format")
    template: str = Field("standard", description="Template to use")
    include_sql: bool = Field(True, description="Include SQL definitions")
    include_lineage: bool = Field(False, description="Include data lineage")
    include_examples: bool = Field(True, description="Include usage examples")
    include_visualizations: bool = Field(False, description="Include charts/diagrams")
    include_changelog: bool = Field(False, description="Include version changelog")
    include_relationships: bool = Field(True, description="Include model relationships")
    custom_sections: Optional[Dict[str, Any]] = Field(None, description="Custom sections to include")
    
    model_config = ConfigDict(from_attributes=True)


class DocumentationMetadata(BaseModel):
    """Metadata extracted from semantic models"""
    model_name: str = Field(..., description="Name of the model")
    description: Optional[str] = Field(None, description="Model description")
    version: Optional[str] = Field(None, description="Model version")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    created_by: Optional[str] = Field(None, description="Creator")
    last_modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Entity definitions")
    measures: List[Dict[str, Any]] = Field(default_factory=list, description="Measure definitions")
    dimensions: List[Dict[str, Any]] = Field(default_factory=list, description="Dimension definitions")
    metrics: List[Dict[str, Any]] = Field(default_factory=list, description="Metric definitions")
    relationships: Optional[List[Dict[str, Any]]] = Field(None, description="Model relationships")
    business_context: Optional[Dict[str, Any]] = Field(None, description="Business context information")
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ExportOptions(BaseModel):
    """Options for exporting documentation"""
    include_toc: bool = Field(True, description="Include table of contents")
    include_index: bool = Field(True, description="Include index")
    include_glossary: bool = Field(False, description="Include glossary")
    page_size: str = Field("A4", description="Page size for PDF")
    font_family: str = Field("Arial", description="Font family")
    font_size: int = Field(11, description="Base font size")
    include_watermark: bool = Field(False, description="Include watermark")
    watermark_text: Optional[str] = Field(None, description="Watermark text")
    
    model_config = ConfigDict(from_attributes=True)


class GeneratedDocumentation(BaseModel):
    """Generated documentation output"""
    format: DocumentationFormat = Field(..., description="Documentation format")
    content: Union[str, bytes] = Field(..., description="Documentation content")
    content_type: str = Field(..., description="MIME content type")
    metadata: Dict[str, Any] = Field(..., description="Generation metadata")
    filename: Optional[str] = Field(None, description="Suggested filename")
    size_bytes: Optional[int] = Field(None, description="Content size in bytes")
    
    model_config = ConfigDict(from_attributes=True)


class DocumentationGenerationRequest(BaseModel):
    """Request model for documentation generation"""
    model_id: str = Field(..., description="ID of the model to document")
    format: DocumentationFormat = Field(DocumentationFormat.MARKDOWN, description="Output format")
    template: str = Field("standard", description="Template to use")
    options: Optional[DocumentationConfig] = Field(None, description="Generation options")
    export_options: Optional[ExportOptions] = Field(None, description="Export options")
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class BatchDocumentationRequest(BaseModel):
    """Request for batch documentation generation"""
    model_ids: List[str] = Field(..., description="List of model IDs")
    format: DocumentationFormat = Field(DocumentationFormat.MARKDOWN, description="Output format")
    template: str = Field("standard", description="Template to use")
    combine: bool = Field(True, description="Combine into single document")
    options: Optional[DocumentationConfig] = Field(None, description="Generation options")
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class DocumentationStatus(BaseModel):
    """Status of documentation generation job"""
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    progress: float = Field(0.0, description="Progress percentage")
    models_processed: int = Field(0, description="Number of models processed")
    total_models: int = Field(0, description="Total number of models")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    result_url: Optional[str] = Field(None, description="URL to download result")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class TemplateListResponse(BaseModel):
    """Response containing available templates"""
    templates: List[DocumentationTemplate] = Field(..., description="Available templates")
    custom_templates_enabled: bool = Field(True, description="Whether custom templates are enabled")
    
    model_config = ConfigDict(from_attributes=True)
