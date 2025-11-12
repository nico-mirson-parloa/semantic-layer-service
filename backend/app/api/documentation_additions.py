# Temporary file to add new endpoint - will be added to documentation.py

@demo_router.get("/recent")
async def get_recent_documentations_demo() -> Dict[str, Any]:
    """Get list of recently generated documentations (demo - no auth required)."""
    try:
        # Convert cache to list format with model info
        recent_docs = []
        for model_id, doc_data in demo_documentation_cache.items():
            recent_docs.append({
                "model_id": model_id,
                "model_name": doc_data.get("metadata", {}).get("model_name", model_id),
                "format": doc_data.get("format", "markdown"),
                "template": doc_data.get("template", "standard"),
                "generated_at": doc_data.get("generated_at"),
                "size_bytes": doc_data.get("size_bytes", 0)
            })
        
        # Sort by generated_at (most recent first)
        recent_docs.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        
        # Limit to last 10
        recent_docs = recent_docs[:10]
        
        return {
            "success": True,
            "documentations": recent_docs,
            "total": len(recent_docs)
        }
        
    except Exception as e:
        logger.error(f"Error getting recent documentations: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "documentations": []
        }
