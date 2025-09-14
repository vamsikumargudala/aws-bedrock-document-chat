import pytest
import asyncio
from httpx import AsyncClient
import sys
import os
from unittest.mock import patch, Mock

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../server'))

from main import app


class TestAPIEndpoints:

    @pytest.fixture
    def client(self):
        """Create test client for API endpoints."""
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct message."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Personal RAG API is running"

    
    def test_health_endpoint_no_client(self, client):
        """Test health endpoint when no client is initialized."""
        with patch('main.client', None):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["client_type"] == "not initialized"
            assert data["bedrock_client"] == "not initialized"

    
    def test_health_endpoint_with_client(self, client):
        """Test health endpoint when client is initialized."""
        mock_client = Mock()

        with patch('main.client', mock_client), \
             patch('main.client_type', 'agent'):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["client_type"] == "agent"
            assert data["bedrock_client"] == "initialized"

    
    def test_query_endpoint_no_client(self, client):
        """Test query endpoint returns error when no client is initialized."""
        with patch('main.client', None):
            response = client.post("/query", json={
                "question": "What is AI?",
                "max_results": 5,
                "stream": False
            })

            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"]

    
    def test_query_endpoint_non_streaming_agent(self, client):
        """Test non-streaming query with agent client."""
        mock_client = Mock()
        mock_client.query_agent.return_value = {
            'answer': 'AI is artificial intelligence.',
            'sources': [
                {
                    'source': 'https://example.com/ai-doc',
                    'score': 0.95,
                    'snippet': 'AI explanation...',
                    'url': 'https://example.com/ai-doc',
                    'title': 'AI Guide',
                    'author': 'Test Author'
                }
            ]
        }

        with patch('main.client', mock_client), \
             patch('main.client_type', 'agent'):
            response = client.post("/query", json={
                "question": "What is AI?",
                "max_results": 5,
                "stream": False,
                "session_id": "test-session"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "AI is artificial intelligence."
            assert len(data["sources"]) == 1
            assert data["sources"][0]["source"] == "https://example.com/ai-doc"

            # Verify client was called correctly
            mock_client.query_agent.assert_called_once_with(
                question="What is AI?",
                session_id="test-session"
            )

    
    def test_query_endpoint_non_streaming_kb(self, client):
        """Test non-streaming query with knowledge base client."""
        mock_client = Mock()
        mock_client.query_knowledge_base.return_value = {
            'answer': 'Knowledge base response.',
            'sources': [
                {
                    'source': 's3://bucket/doc.txt',
                    'score': 0.9,
                    'snippet': 'KB content...'
                }
            ]
        }

        with patch('main.client', mock_client), \
             patch('main.client_type', 'knowledge_base'):
            response = client.post("/query", json={
                "question": "Test question",
                "max_results": 3,
                "stream": False
            })

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Knowledge base response."

            # Verify client was called correctly
            mock_client.query_knowledge_base.assert_called_once_with(
                query="Test question",
                max_results=3
            )

    
    def test_query_endpoint_streaming_agent(self, client):
        """Test streaming query with agent client."""
        mock_client = Mock()

        def mock_stream():
            yield {'type': 'metadata', 'sources': []}
            yield {'type': 'content', 'text': 'Hello '}
            yield {'type': 'content', 'text': 'World'}

        mock_client.stream_query.return_value = mock_stream()

        with patch('main.client', mock_client), \
             patch('main.client_type', 'agent'):
            response = client.post("/query", json={
                "question": "Stream test",
                "stream": True,
                "session_id": "stream-session"
            })

            assert response.status_code == 200
            assert response.headers['content-type'] == 'text/event-stream; charset=utf-8'

            # For streaming response, we can't easily test the content
            # in this setup, but we can verify the client was called
            mock_client.stream_query.assert_called_once_with(
                "Stream test",
                "stream-session"
            )

    
    def test_query_endpoint_validation_error(self, client):
        """Test query endpoint with invalid request data."""
        # Missing required question field
        response = client.post("/query", json={
            "max_results": 5,
            "stream": False
        })

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    
    def test_query_endpoint_client_error(self, client):
        """Test query endpoint handles client errors properly."""
        mock_client = Mock()
        mock_client.query_agent.side_effect = Exception("Bedrock error")

        with patch('main.client', mock_client), \
             patch('main.client_type', 'agent'):
            response = client.post("/query", json={
                "question": "Error test",
                "stream": False
            })

            assert response.status_code == 500
            data = response.json()
            assert "Bedrock error" in data["detail"]

    
    def test_query_endpoint_default_values(self, client):
        """Test query endpoint uses default values correctly."""
        mock_client = Mock()
        mock_client.query_knowledge_base.return_value = {
            'answer': 'Default test response',
            'sources': []
        }

        with patch('main.client', mock_client), \
             patch('main.client_type', 'knowledge_base'):
            # Only provide required question field
            response = client.post("/query", json={
                "question": "Default test"
            })

            assert response.status_code == 200

            # Verify defaults were used
            mock_client.query_knowledge_base.assert_called_once_with(
                query="Default test",
                max_results=5  # default value
            )


if __name__ == '__main__':
    pytest.main([__file__])
