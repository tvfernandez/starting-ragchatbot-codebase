"""
API endpoint tests for the RAG system.

Tests cover:
- POST /api/query - Query processing endpoint
- GET /api/courses - Course statistics endpoint
- GET / - Root endpoint (health check in test mode)
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from conftest import MockRAGSystem, create_test_app


class TestQueryEndpoint:
    """Tests for POST /api/query endpoint"""

    def test_query_success_without_session(self, client: TestClient, mock_rag_system: MockRAGSystem):
        """Test successful query without providing session_id"""
        response = client.post("/api/query", json={"query": "What is RAG?"})

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"].startswith("test_session_")
        assert data["answer"] == "This is a mock response about RAG systems."

    def test_query_success_with_session(self, client: TestClient, mock_rag_system: MockRAGSystem):
        """Test successful query with existing session_id"""
        response = client.post(
            "/api/query",
            json={"query": "Tell me more", "session_id": "existing_session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "existing_session"

    def test_query_returns_sources(self, client: TestClient, mock_rag_system: MockRAGSystem):
        """Test that query returns properly formatted sources"""
        response = client.post("/api/query", json={"query": "What courses exist?"})

        assert response.status_code == 200
        data = response.json()
        sources = data["sources"]
        assert len(sources) == 2
        assert sources[0]["text"] == "Course A - Lesson 1"
        assert sources[0]["url"] == "https://example.com/course-a/lesson-1"
        assert sources[1]["text"] == "Course A - Lesson 2"
        assert sources[1]["url"] is None

    def test_query_with_custom_response(self, client: TestClient, mock_rag_system: MockRAGSystem):
        """Test query with configured mock response"""
        mock_rag_system.set_query_response(
            response="Custom test response",
            sources=[{"text": "Custom Source", "url": "https://custom.url"}]
        )

        # Need to recreate app with updated mock
        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.post("/api/query", json={"query": "Test query"})

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Custom test response"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["text"] == "Custom Source"

    def test_query_empty_sources(self, client: TestClient, mock_rag_system: MockRAGSystem):
        """Test query when no sources are returned"""
        mock_rag_system.set_query_response(
            response="Response without sources",
            sources=[]
        )
        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.post("/api/query", json={"query": "General question"})

        assert response.status_code == 200
        data = response.json()
        assert data["sources"] == []

    def test_query_missing_query_field(self, client: TestClient):
        """Test query with missing required field"""
        response = client.post("/api/query", json={})

        assert response.status_code == 422  # Validation error

    def test_query_empty_query_string(self, client: TestClient):
        """Test query with empty string"""
        response = client.post("/api/query", json={"query": ""})

        # Empty string is technically valid per the schema
        assert response.status_code == 200

    def test_query_internal_error(self, client: TestClient, mock_rag_system: MockRAGSystem):
        """Test query endpoint error handling"""
        mock_rag_system.set_error(True, "Database connection failed")
        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.post("/api/query", json={"query": "This will fail"})

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    def test_query_long_text(self, client: TestClient, mock_rag_system: MockRAGSystem):
        """Test query with long text input"""
        long_query = "What is " + "very " * 100 + "important about RAG?"

        response = client.post("/api/query", json={"query": long_query})

        assert response.status_code == 200

    def test_query_special_characters(self, client: TestClient, mock_rag_system: MockRAGSystem):
        """Test query with special characters"""
        response = client.post(
            "/api/query",
            json={"query": "What about <script>alert('xss')</script> and SQL' OR '1'='1?"}
        )

        assert response.status_code == 200


class TestCoursesEndpoint:
    """Tests for GET /api/courses endpoint"""

    def test_get_courses_success(self, client: TestClient):
        """Test successful course statistics retrieval"""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3

    def test_get_courses_returns_titles(self, client: TestClient):
        """Test that course titles are returned correctly"""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert "Course A" in data["course_titles"]
        assert "Course B" in data["course_titles"]
        assert "Course C" in data["course_titles"]

    def test_get_courses_custom_analytics(self, mock_rag_system: MockRAGSystem):
        """Test with custom course analytics"""
        mock_rag_system.set_course_analytics({
            "total_courses": 5,
            "course_titles": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
        })
        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 5
        assert "Alpha" in data["course_titles"]

    def test_get_courses_empty(self, mock_rag_system: MockRAGSystem):
        """Test when no courses exist"""
        mock_rag_system.set_course_analytics({
            "total_courses": 0,
            "course_titles": []
        })
        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_get_courses_internal_error(self, mock_rag_system: MockRAGSystem):
        """Test courses endpoint error handling"""
        mock_rag_system.set_error(True, "Vector store unavailable")
        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert "Vector store unavailable" in response.json()["detail"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_returns_health_status(self, client: TestClient):
        """Test root endpoint returns health status"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data


class TestAsyncEndpoints:
    """Async tests for API endpoints using httpx AsyncClient"""

    @pytest.mark.asyncio
    async def test_async_query(self, async_client: AsyncClient):
        """Test query endpoint with async client"""
        response = await async_client.post(
            "/api/query",
            json={"query": "What is machine learning?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    @pytest.mark.asyncio
    async def test_async_courses(self, async_client: AsyncClient):
        """Test courses endpoint with async client"""
        response = await async_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data

    @pytest.mark.asyncio
    async def test_async_root(self, async_client: AsyncClient):
        """Test root endpoint with async client"""
        response = await async_client.get("/")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_concurrent_queries(self, async_client: AsyncClient):
        """Test multiple concurrent queries"""
        import asyncio

        queries = [
            {"query": f"Question {i}"} for i in range(5)
        ]

        tasks = [
            async_client.post("/api/query", json=q)
            for q in queries
        ]

        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code == 200
            assert "answer" in response.json()


class TestRequestValidation:
    """Tests for request validation and edge cases"""

    def test_invalid_json(self, client: TestClient):
        """Test with invalid JSON payload"""
        response = client.post(
            "/api/query",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_wrong_content_type(self, client: TestClient):
        """Test with wrong content type"""
        response = client.post(
            "/api/query",
            data="query=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 422

    def test_extra_fields_ignored(self, client: TestClient):
        """Test that extra fields in request are ignored"""
        response = client.post(
            "/api/query",
            json={
                "query": "Valid query",
                "extra_field": "should be ignored",
                "another_extra": 123
            }
        )

        assert response.status_code == 200

    def test_null_session_id(self, client: TestClient):
        """Test with explicit null session_id"""
        response = client.post(
            "/api/query",
            json={"query": "Test", "session_id": None}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"].startswith("test_session_")


class TestResponseFormat:
    """Tests for response format and structure"""

    def test_query_response_structure(self, client: TestClient):
        """Test that query response has correct structure"""
        response = client.post("/api/query", json={"query": "Test"})

        data = response.json()

        # Check all required fields exist
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data

        # Check types
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)

    def test_courses_response_structure(self, client: TestClient):
        """Test that courses response has correct structure"""
        response = client.get("/api/courses")

        data = response.json()

        # Check all required fields exist
        assert "total_courses" in data
        assert "course_titles" in data

        # Check types
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

    def test_source_structure(self, client: TestClient):
        """Test that source objects have correct structure"""
        response = client.post("/api/query", json={"query": "Test"})

        data = response.json()
        sources = data["sources"]

        for source in sources:
            assert "text" in source
            assert "url" in source
            assert isinstance(source["text"], str)
            assert source["url"] is None or isinstance(source["url"], str)
