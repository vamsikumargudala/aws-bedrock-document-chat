import pytest
from unittest.mock import Mock, patch
import json
import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../server'))

from bedrock_agent_client import BedrockAgentClient


class TestBedrockAgentClient:

    def setup_method(self, method):
        """Setup test fixtures before each test method."""
        pass

    @patch('boto3.client')
    def test_initialization_with_env_vars(self, mock_boto_client):
        """Test client initialization with environment variables."""
        with patch.dict('os.environ', {
            'BEDROCK_AGENT_ID': 'test-agent-id',
            'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id',
            'AWS_REGION': 'us-west-2'
        }):
            client = BedrockAgentClient()

            assert client.agent_id == 'test-agent-id'
            assert client.agent_alias_id == 'test-alias-id'
            assert client.region == 'us-west-2'

            # Verify boto3 client was created
            mock_boto_client.assert_called_once()

    def test_initialization_missing_required_env_vars(self):
        """Test that initialization fails without required environment variables."""
        # Test missing agent ID
        with patch.dict('os.environ', {'BEDROCK_AGENT_ALIAS_ID': 'test-alias'}, clear=True):
            with pytest.raises(ValueError, match="BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set"):
                BedrockAgentClient()

        # Test missing alias ID
        with patch.dict('os.environ', {'BEDROCK_AGENT_ID': 'test-agent'}, clear=True):
            with pytest.raises(ValueError, match="BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set"):
                BedrockAgentClient()

    @patch('boto3.client')
    def test_query_agent_success(self, mock_boto_client):
        """Test successful agent query."""
        # Mock bedrock agent client
        mock_bedrock_agent = Mock()

        # Mock agent response
        mock_response = {
            'completion': [
                {
                    'chunk': {
                        'bytes': b'Hello from agent',
                        'attribution': {
                            'citations': [
                                {
                                    'retrievedReferences': [
                                        {
                                            'location': {
                                                'type': 'CONFLUENCE',
                                                'confluenceLocation': {'url': 'https://example.com/page1'}
                                            },
                                            'content': {'text': 'Sample content'},
                                            'metadata': {
                                                'x-amz-bedrock-kb-title': 'Test Page',
                                                'x-amz-bedrock-kb-author': 'Test Author'
                                            },
                                            'score': 0.9
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            ]
        }
        mock_bedrock_agent.invoke_agent.return_value = mock_response
        mock_boto_client.return_value = mock_bedrock_agent

        with patch.dict('os.environ', {
            'BEDROCK_AGENT_ID': 'test-agent-id',
            'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id'
        }):
            client = BedrockAgentClient()

            result = client.query_agent("Test question", "test-session")

            assert result['answer'] == 'Hello from agent'
            assert result['session_id'] == 'test-session'
            assert result['agent_id'] == 'test-agent-id'
            assert len(result['sources']) > 0

            # Check source formatting
            source = result['sources'][0]
            assert source['url'] == 'https://example.com/page1'
            assert source['title'] == 'Test Page'
            assert source['author'] == 'Test Author'

    @patch('boto3.client')
    @patch('uuid.uuid4')
    def test_query_agent_generates_session_id(self, mock_uuid, mock_boto_client):
        """Test that agent generates session ID when not provided."""
        mock_uuid.return_value = 'generated-session-id'
        mock_bedrock_agent = Mock()

        # Simple mock response
        mock_response = {
            'completion': [
                {'chunk': {'bytes': b'Response text'}}
            ]
        }
        mock_bedrock_agent.invoke_agent.return_value = mock_response
        mock_boto_client.return_value = mock_bedrock_agent

        with patch.dict('os.environ', {
            'BEDROCK_AGENT_ID': 'test-agent-id',
            'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id'
        }):
            client = BedrockAgentClient()
            result = client.query_agent("Test question")

            assert result['session_id'] == 'generated-session-id'

    @patch('boto3.client')
    def test_stream_query(self, mock_boto_client):
        """Test streaming query functionality."""
        mock_bedrock_agent = Mock()

        # Mock complete agent response for streaming simulation
        mock_response = {
            'completion': [
                {'chunk': {'bytes': b'Hello world from streaming'}}
            ]
        }
        mock_bedrock_agent.invoke_agent.return_value = mock_response
        mock_boto_client.return_value = mock_bedrock_agent

        with patch.dict('os.environ', {
            'BEDROCK_AGENT_ID': 'test-agent-id',
            'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id'
        }):
            client = BedrockAgentClient()

            # Mock the query_agent method to return structured response
            with patch.object(client, 'query_agent') as mock_query:
                mock_query.return_value = {
                    'answer': 'Hello world from streaming',
                    'sources': [{'url': 'https://example.com', 'title': 'Test Source'}],
                    'session_id': 'test-session'
                }

                chunks = list(client.stream_query("Test question", "test-session"))

                # Should have metadata first, then content chunks
                assert len(chunks) >= 2

                # Check metadata chunk
                metadata_chunk = chunks[0]
                assert metadata_chunk['type'] == 'metadata'
                assert 'sources' in metadata_chunk
                assert metadata_chunk['session_id'] == 'test-session'

                # Check content chunks (simulated streaming)
                content_chunks = [chunk for chunk in chunks if chunk['type'] == 'content']
                assert len(content_chunks) > 0

                # Verify all content chunks combine to original answer
                full_text = ''.join(chunk['text'] for chunk in content_chunks)
                assert 'Hello world from streaming' in full_text

    @patch('boto3.client')
    def test_error_handling(self, mock_boto_client):
        """Test error handling in agent query."""
        mock_bedrock_agent = Mock()
        mock_bedrock_agent.invoke_agent.side_effect = Exception("AWS Error")
        mock_boto_client.return_value = mock_bedrock_agent

        with patch.dict('os.environ', {
            'BEDROCK_AGENT_ID': 'test-agent-id',
            'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id'
        }):
            client = BedrockAgentClient()

            with pytest.raises(Exception, match="AWS Error"):
                client.query_agent("Test question")


if __name__ == '__main__':
    pytest.main([__file__])