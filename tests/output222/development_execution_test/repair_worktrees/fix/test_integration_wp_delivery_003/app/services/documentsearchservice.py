class DocumentSearchService:
    def __init__(self):
        self._documents = {
            "doc_001": {"id": "doc_001", "title": "Annual Report 2023", "content": "This report summarizes financial performance and strategic initiatives for fiscal year 2023.", "tags": ["finance", "report"], "created_at": "2023-12-15"},
            "doc_002": {"id": "doc_002", "title": "API Integration Guide", "content": "Step-by-step instructions for integrating with our RESTful API endpoints.", "tags": ["api", "developer"], "created_at": "2024-01-22"},
            "doc_003": {"id": "doc_003", "title": "Security Policy Handbook", "content": "Outlines access controls, encryption standards, and incident response procedures.", "tags": ["security", "compliance"], "created_at": "2024-02-10"},
            "doc_004": {"id": "doc_004", "title": "Onboarding Checklist", "content": "New employee onboarding tasks including HR forms, system access, and training modules.", "tags": ["hr", "onboarding"], "created_at": "2024-03-05"}
        }
        self._next_id = 1001

    def search_documents(self, query: str, tags: list = None, limit: int = 10) -> list:
        if not isinstance(query, str):
            raise TypeError("Query must be a string")
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer")
        
        results = []
        query_lower = query.strip().lower()
        
        for doc in self._documents.values():
            # Full-text match in title or content
            matches_text = query_lower in doc["title"].lower() or query_lower in doc["content"].lower()
            
            # Tag match if tags provided
            matches_tags = True
            if tags and isinstance(tags, list):
                matches_tags = any(tag.lower() in [t.lower() for t in doc.get("tags", [])] for tag in tags)
            
            if matches_text and matches_tags:
                results.append(doc.copy())
                
        # Sort by relevance: prioritize title matches, then recency
        def sort_key(doc):
            title_score = 2 if query_lower in doc["title"].lower() else 1
            # Convert created_at to ordinal for sorting (simplified date parsing)
            try:
                y, m, d = map(int, doc["created_at"].split("-"))
                date_score = y * 10000 + m * 100 + d
            except (ValueError, AttributeError):
                date_score = 0
            return (-title_score, -date_score)
        
        results.sort(key=sort_key)
        return results[:limit]

    def get_document_by_id(self, doc_id: str) -> dict:
        if not isinstance(doc_id, str) or not doc_id.strip():
            raise ValueError("Document ID must be a non-empty string")
        doc = self._documents.get(doc_id.strip())
        if doc is None:
            raise KeyError(f"Document with ID '{doc_id}' not found")
        return doc.copy()

    def add_document(self, title: str, content: str, tags: list = None) -> str:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Title must be a non-empty string")
        if not isinstance(content, str):
            raise ValueError("Content must be a string")
        
        doc_id = f"doc_{self._next_id:03d}"
        self._next_id += 1
        
        new_doc = {
            "id": doc_id,
            "title": title.strip(),
            "content": content.strip(),
            "tags": tags if isinstance(tags, list) else [],
            "created_at": self._get_current_date_string()
        }
        
        self._documents[doc_id] = new_doc
        return doc_id

    def _get_current_date_string(self) -> str:
        import datetime
        return datetime.date.today().isoformat()