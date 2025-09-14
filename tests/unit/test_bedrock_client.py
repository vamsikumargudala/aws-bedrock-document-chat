import pytest
from unittest.mock import Mock, patch
import json
import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../server'))

from bedrock_client import BedrockRAGClient


class TestBedrockRAGClient:

    def setup_method(self, method):
        """Setup test fixtures before each test method."""
        pass

    @patch('boto3.client')
    def test_initialization_with_env_vars(self, mock_boto_client):
        """Test client initialization with environment variables."""
        with patch.dict('os.environ', {
            'BEDROCK_KNOWLEDGE_BASE_ID': 'test-kb-id',
            'AWS_REGION': 'us-west-2',
            'BEDROCK_MODEL_ID': 'test-model-id'
        }):
            client = BedrockRAGClient()

            assert client.knowledge_base_id == 'test-kb-id'
            assert client.region == 'us-west-2'
            assert client.model_id == 'test-model-id'

            # Verify boto3 clients were created
            assert mock_boto_client.call_count == 2

    def test_initialization_missing_kb_id(self):
        """Test that initialization fails without knowledge base ID."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="BEDROCK_KNOWLEDGE_BASE_ID must be set"):
                BedrockRAGClient()

    @patch('boto3.client')
    def test_build_prompt(self, mock_boto_client):
        """Test the prompt building functionality."""
        with patch.dict('os.environ', {'BEDROCK_KNOWLEDGE_BASE_ID': 'test-kb-id'}):
            client = BedrockRAGClient()

            query = "What is AI?"
            context = "AI is artificial intelligence."

            prompt = client._build_prompt(query, context)

            assert query in prompt
            assert context in prompt
            assert "Answer based solely on the provided context" in prompt

    @patch('boto3.client')
    def test_query_knowledge_base_success(self, mock_boto_client):
        """Test successful knowledge base query."""
        # Mock bedrock agent client
        mock_bedrock_agent = Mock()
        mock_bedrock_runtime = Mock()

        # Mock retrieval response
        mock_bedrock_agent.retrieve.return_value = {
            'retrievalResults': [
                {
                    'content': {'text': 'Sample content about AI'},
                    'location': {'s3Location': {'uri': 's3://bucket/file.txt'}},
                    'score': 0.95
                }
            ]
        }

        # Mock generation response
        mock_response_body = {
            'content': [{'text': 'AI is artificial intelligence.'}],
            'usage': {'input_tokens': 100, 'output_tokens': 50}
        }
        mock_bedrock_runtime.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps(mock_response_body).encode())
        }

        mock_boto_client.side_effect = [mock_bedrock_agent, mock_bedrock_runtime]

        with patch.dict('os.environ', {'BEDROCK_KNOWLEDGE_BASE_ID': 'test-kb-id'}):
            client = BedrockRAGClient()

            result = client.query_knowledge_base("What is AI?")

            assert result['answer'] == 'AI is artificial intelligence.'
            assert len(result['sources']) == 1
            assert result['sources'][0]['source'] == 's3://bucket/file.txt'
            assert result['sources'][0]['score'] == 0.95
            assert 'tokens_used' in result

    @patch('boto3.client')
    def test_stream_query(self, mock_boto_client):
        """Test streaming query functionality."""
        # Mock bedrock agent and runtime clients
        mock_bedrock_agent = Mock()
        mock_bedrock_runtime = Mock()

        # Mock retrieval response
        mock_bedrock_agent.retrieve.return_value = {
            'retrievalResults': [
                {
                    'content': {'text': 'Streaming content'},
                    'location': {'s3Location': {'uri': 's3://bucket/stream.txt'}},
                    'score': 0.9
                }
            ]
        }

        # Mock streaming response
        mock_stream_response = {
            'body': [
                {'chunk': {'bytes': json.dumps({'type': 'content_block_delta', 'delta': {'text': 'Hello'}}).encode()}},
                {'chunk': {'bytes': json.dumps({'type': 'content_block_delta', 'delta': {'text': ' World'}}).encode()}}
            ]
        }
        mock_bedrock_runtime.invoke_model_with_response_stream.return_value = mock_stream_response

        mock_boto_client.side_effect = [mock_bedrock_agent, mock_bedrock_runtime]

        with patch.dict('os.environ', {'BEDROCK_KNOWLEDGE_BASE_ID': 'test-kb-id'}):
            client = BedrockRAGClient()

            chunks = list(client.stream_query("Test query"))

            # Should have metadata first, then content chunks
            assert len(chunks) >= 2
            assert chunks[0]['type'] == 'metadata'
            assert 'sources' in chunks[0]

            # Content chunks
            content_chunks = [chunk for chunk in chunks if chunk['type'] == 'content']
            assert len(content_chunks) == 2
            assert content_chunks[0]['text'] == 'Hello'
            assert content_chunks[1]['text'] == ' World'


if __name__ == '__main__':
    pytest.main([__file__])