"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, patch

# Add server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../server'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        'AWS_REGION': 'us-east-1',
        'BEDROCK_AGENT_ID': 'test-agent-id',
        'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id',
        'BEDROCK_KNOWLEDGE_BASE_ID': 'test-kb-id',
        'BEDROCK_MODEL_ID': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'USE_AGENT': 'true'
    }

    with patch.dict('os.environ', env_vars):
        yield env_vars


@pytest.fixture
def mock_bedrock_agent_client():
    """Mock Bedrock Agent client."""
    mock_client = Mock()
    mock_client.query_agent.return_value = {
        'answer': 'Mock agent response',
        'sources': [
            {
                'source': 'https://example.com/doc1',
                'score': 0.95,
                'snippet': 'Mock content snippet',
                'url': 'https://example.com/doc1',
                'title': 'Mock Document',
                'author': 'Mock Author'
            }
        ],
        'session_id': 'mock-session-id',
        'agent_id': 'test-agent-id'
    }

    def mock_stream():
        yield {'type': 'metadata', 'sources': mock_client.query_agent.return_value['sources']}
        yield {'type': 'content', 'text': 'Mock '}
        yield {'type': 'content', 'text': 'streaming '}
        yield {'type': 'content', 'text': 'response'}

    mock_client.stream_query.return_value = mock_stream()
    return mock_client


@pytest.fixture
def mock_bedrock_kb_client():
    """Mock Bedrock Knowledge Base client."""
    mock_client = Mock()
    mock_client.query_knowledge_base.return_value = {
        'answer': 'Mock knowledge base response',
        'sources': [
            {
                'source': 's3://test-bucket/doc.txt',
                'score': 0.9,
                'snippet': 'Mock KB content'
            }
        ],
        'tokens_used': {'input_tokens': 100, 'output_tokens': 50}
    }

    def mock_stream():
        yield {'type': 'metadata', 'sources': mock_client.query_knowledge_base.return_value['sources']}
        yield {'type': 'content', 'text': 'Mock KB '}
        yield {'type': 'content', 'text': 'streaming'}

    mock_client.stream_query.return_value = mock_stream()
    return mock_client


@pytest.fixture
def sample_query_request():
    """Sample query request data."""
    return {
        'question': 'What is artificial intelligence?',
        'max_results': 5,
        'stream': False,
        'session_id': 'test-session-123'
    }


@pytest.fixture
def sample_confluence_source():
    """Sample Confluence source data."""
    return {
        'url': 'https://company.atlassian.net/wiki/pages/123/AI-Guide',
        'title': 'AI Implementation Guide',
        'author': 'John Doe',
        'source': 'https://company.atlassian.net/wiki/pages/123/AI-Guide',
        'score': 0.95,
        'snippet': 'Artificial intelligence (AI) is the simulation of human intelligence...',
        'content_preview': 'Artificial intelligence (AI) is the simulation of human intelligence processes by machines, especially computer systems...'
    }


@pytest.fixture
def sample_s3_source():
    """Sample S3 source data."""
    return {
        'source': 's3://my-bucket/documents/ai-research.pdf',
        'score': 0.87,
        'snippet': 'Research on AI applications in enterprise environments...',
        'url': None
    }


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "aws: mark test as requiring AWS credentials"
    )


# Skip AWS tests if no credentials
def pytest_collection_modifyitems(config, items):
    """Skip AWS integration tests if credentials are not available."""
    skip_aws = pytest.mark.skip(reason="AWS credentials not available")

    for item in items:
        if "aws" in item.keywords:
            # Check if AWS credentials are available
            if not (os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('AWS_PROFILE')):
                item.add_marker(skip_aws)