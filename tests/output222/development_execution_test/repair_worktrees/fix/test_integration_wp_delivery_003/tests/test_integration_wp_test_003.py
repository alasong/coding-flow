import pytest
import time
import statistics
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.documentstorageservice import DocumentStorageService
from app.services.usermanagementservice import UserManagerService
from app.services.apigateway import ApiGateway

def test_document_search_preview_storage_latency():
    search_service = DocumentSearchService()
    preview_service = DocumentPreviewService()
    storage_service = DocumentStorageService()
    user_service = UserManagerService()
    api_gateway = ApiGateway()

    # Warm-up
    user_service.get_user_by_id("test-user")
    storage_service.get_document("test-doc")

    # Measure end-to-end latency for search → preview → storage interaction
    latencies = []
    for _ in range(5):
        start = time.perf_counter()
        results = search_service.search("performance test query", limit=10)
        if results:
            doc_id = results[0].get("id") or "test-doc"
            preview_service.generate_preview(doc_id, format="png")
            storage_service.get_document(doc_id)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # ms

    assert len(latencies) == 5
    avg_latency_ms = statistics.mean(latencies)
    p95_latency_ms = statistics.quantiles(latencies, n=20)[-1]
    assert avg_latency_ms < 1500.0, f"Average latency {avg_latency_ms:.2f}ms exceeds 1500ms threshold"
    assert p95_latency_ms < 3000.0, f"p95 latency {p95_latency_ms:.2f}ms exceeds 3000ms threshold"

def test_api_gateway_document_flow_throughput():
    api_gateway = ApiGateway()
    search_service = DocumentSearchService()
    preview_service = DocumentPreviewService()
    storage_service = DocumentStorageService()

    # Simulate concurrent document flow through API gateway
    durations = []
    for i in range(3):
        start = time.perf_counter()
        # Full service chain invocation mimicking API gateway routing
        search_results = search_service.search(f"benchmark-{i}", limit=5)
        for result in search_results[:2]:
            doc_id = result.get("id") or f"doc-{i}"
            preview_service.generate_preview(doc_id, format="thumbnail")
            storage_service.get_document(doc_id)
        end = time.perf_counter()
        durations.append(end - start)

    throughput_per_second = 3 / sum(durations) if durations else 0
    assert throughput_per_second > 0.5, f"Throughput {throughput_per_second:.2f} req/sec below 0.5 req/sec minimum"

def test_user_management_service_integration_latency():
    user_service = UserManagerService()
    search_service = DocumentSearchService()
    preview_service = DocumentPreviewService()

    # Measure latency impact of user context propagation across services
    latencies = []
    for _ in range(3):
        start = time.perf_counter()
        user = user_service.get_user_by_id("perf-test-user")
        if user:
            # Use user context in search and preview
            search_service.search("user-context-query", user_id=user.get("id", "perf-test-user"), limit=1)
            preview_service.generate_preview("test-doc", user_id=user.get("id", "perf-test-user"))
        end = time.perf_counter()
        latencies.append((end - start) * 1000)

    assert len(latencies) == 3
    max_latency_ms = max(latencies)
    assert max_latency_ms < 2500.0, f"Max latency {max_latency_ms:.2f}ms exceeds 2500ms threshold"