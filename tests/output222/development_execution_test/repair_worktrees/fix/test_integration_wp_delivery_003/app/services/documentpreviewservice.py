class DocumentPreviewService:
    def __init__(self):
        self._cache = {}
        self._supported_formats = {"pdf", "txt", "md", "csv", "json", "xml"}

    def preview(self, document_id: str, content: str, format_type: str) -> dict:
        if not document_id or not content or not format_type:
            raise ValueError("document_id, content, and format_type must be provided")
        
        format_type = format_type.lower().strip()
        if format_type not in self._supported_formats:
            raise ValueError(f"Unsupported format: {format_type}")

        # Generate truncated preview (first 500 chars, or full if shorter)
        preview_text = content[:500] if len(content) > 500 else content
        line_count = content.count('\n') + 1
        word_count = len(content.split())
        
        # Store in memory cache with metadata
        preview_data = {
            "document_id": document_id,
            "format": format_type,
            "preview_text": preview_text,
            "line_count": line_count,
            "word_count": word_count,
            "truncated": len(content) > 500
        }
        self._cache[document_id] = preview_data

        return preview_data

    def get_preview(self, document_id: str) -> dict:
        if not document_id:
            raise ValueError("document_id must be provided")
        
        if document_id not in self._cache:
            raise KeyError(f"No preview found for document_id: {document_id}")
        
        return self._cache[document_id].copy()

    def clear_preview(self, document_id: str) -> bool:
        if not document_id:
            raise ValueError("document_id must be provided")
        
        if document_id in self._cache:
            del self._cache[document_id]
            return True
        return False

    def list_cached_previews(self) -> list:
        return [
            {
                "document_id": doc_id,
                "format": data["format"],
                "line_count": data["line_count"],
                "word_count": data["word_count"]
            }
            for doc_id, data in self._cache.items()
        ]