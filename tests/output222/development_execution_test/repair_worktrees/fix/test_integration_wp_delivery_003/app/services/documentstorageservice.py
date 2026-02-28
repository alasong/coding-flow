class DocumentStorageService:
    def __init__(self):
        self._storage = {}
        self._next_id = 1

    def store_document(self, content: str, metadata: dict = None) -> str:
        doc_id = f"doc_{self._next_id}"
        self._next_id += 1
        if metadata is None:
            metadata = {}
        self._storage[doc_id] = {
            "content": content,
            "metadata": metadata,
            "created_at": self._get_timestamp()
        }
        return doc_id

    def retrieve_document(self, doc_id: str) -> dict:
        if doc_id not in self._storage:
            raise KeyError(f"Document with ID '{doc_id}' not found")
        return {
            "id": doc_id,
            "content": self._storage[doc_id]["content"],
            "metadata": self._storage[doc_id]["metadata"].copy(),
            "created_at": self._storage[doc_id]["created_at"]
        }

    def update_document(self, doc_id: str, content: str = None, metadata: dict = None) -> bool:
        if doc_id not in self._storage:
            return False
        if content is not None:
            self._storage[doc_id]["content"] = content
        if metadata is not None:
            self._storage[doc_id]["metadata"].update(metadata)
        self._storage[doc_id]["updated_at"] = self._get_timestamp()
        return True

    def delete_document(self, doc_id: str) -> bool:
        if doc_id in self._storage:
            del self._storage[doc_id]
            return True
        return False

    def list_document_ids(self) -> list:
        return list(self._storage.keys())

    def get_document_count(self) -> int:
        return len(self._storage)

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()