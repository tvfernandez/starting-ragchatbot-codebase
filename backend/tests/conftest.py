"""
Shared test fixtures for the RAG system tests.

This module provides reusable fixtures for mocking dependencies
and setting up test data across all test modules.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from pydantic import BaseModel


# ============================================================================
# Pydantic Models (duplicated to avoid import issues with app.py static files)
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None


class Source(BaseModel):
    """Model for a source citation with optional URL"""
    text: str
    url: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[Source]
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]


# ============================================================================
# Mock Classes
# ============================================================================

class MockSessionManager:
    """Mock session manager for testing"""

    def __init__(self):
        self.sessions: Dict[str, List] = {}
        self.session_counter = 0

    def create_session(self) -> str:
        self.session_counter += 1
        session_id = f"test_session_{self.session_counter}"
        self.sessions[session_id] = []
        return session_id

    def get_conversation_history(self, session_id: Optional[str]) -> Optional[str]:
        if not session_id or session_id not in self.sessions:
            return None
        return "Mock conversation history"

    def add_exchange(self, session_id: str, user_message: str, assistant_message: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({
            "user": user_message,
            "assistant": assistant_message
        })


class MockRAGSystem:
    """Mock RAG system for testing API endpoints"""

    def __init__(self):
        self.session_manager = MockSessionManager()
        self._query_response = "This is a mock response about RAG systems."
        self._query_sources = [
            {"text": "Course A - Lesson 1", "url": "https://example.com/course-a/lesson-1"},
            {"text": "Course A - Lesson 2", "url": None}
        ]
        self._course_analytics = {
            "total_courses": 3,
            "course_titles": ["Course A", "Course B", "Course C"]
        }
        self._should_raise_error = False
        self._error_message = "Mock error"

    def query(self, query: str, session_id: Optional[str] = None):
        if self._should_raise_error:
            raise Exception(self._error_message)
        return self._query_response, self._query_sources

    def get_course_analytics(self) -> Dict:
        if self._should_raise_error:
            raise Exception(self._error_message)
        return self._course_analytics

    def set_query_response(self, response: str, sources: List[Dict]):
        """Configure mock query response for testing"""
        self._query_response = response
        self._query_sources = sources

    def set_course_analytics(self, analytics: Dict):
        """Configure mock course analytics for testing"""
        self._course_analytics = analytics

    def set_error(self, should_raise: bool, message: str = "Mock error"):
        """Configure mock to raise errors"""
        self._should_raise_error = should_raise
        self._error_message = message


# ============================================================================
# Test App Factory
# ============================================================================

def create_test_app(rag_system: MockRAGSystem) -> FastAPI:
    """
    Create a test FastAPI app with mocked dependencies.

    This avoids importing the main app.py which mounts static files
    that don't exist in the test environment.
    """
    app = FastAPI(title="Test RAG System")

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()

            answer, sources_list = rag_system.query(request.query, session_id)
            sources = [Source(**s) for s in sources_list] if sources_list else []

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        """Root endpoint - in production serves static files"""
        return {"message": "RAG System API", "status": "healthy"}

    return app


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_rag_system() -> MockRAGSystem:
    """Provide a fresh mock RAG system for each test"""
    return MockRAGSystem()


@pytest.fixture
def test_app(mock_rag_system: MockRAGSystem) -> FastAPI:
    """Provide a test FastAPI app with mocked dependencies"""
    return create_test_app(mock_rag_system)


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Provide a synchronous test client"""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app: FastAPI) -> AsyncClient:
    """Provide an async test client for async tests"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_query_request() -> dict:
    """Sample query request data"""
    return {
        "query": "What is RAG?",
        "session_id": None
    }


@pytest.fixture
def sample_query_with_session() -> dict:
    """Sample query request with existing session"""
    return {
        "query": "Tell me more about embeddings",
        "session_id": "existing_session_123"
    }


@pytest.fixture
def mock_sources() -> List[Dict]:
    """Sample source citations"""
    return [
        {"text": "Introduction to RAG - Lesson 1", "url": "https://example.com/rag/1"},
        {"text": "Vector Databases - Lesson 2", "url": "https://example.com/rag/2"},
        {"text": "Embeddings Overview - Lesson 3", "url": None}
    ]


@pytest.fixture
def mock_course_titles() -> List[str]:
    """Sample course titles"""
    return [
        "Introduction to RAG",
        "Advanced NLP Techniques",
        "Building AI Applications"
    ]
