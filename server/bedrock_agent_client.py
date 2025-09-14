import boto3
import os
import json
import uuid
import time
from typing import Dict, List, Optional, Generator
from dotenv import load_dotenv

load_dotenv()

class BedrockAgentClient:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.agent_id = os.getenv("BEDROCK_AGENT_ID")
        self.agent_alias_id = os.getenv("BEDROCK_AGENT_ALIAS_ID")

        if not self.agent_id or not self.agent_alias_id:
            raise ValueError("BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set in environment variables")

        # Initialize Bedrock Agent Runtime client
        self.bedrock_agent = boto3.client(
            "bedrock-agent-runtime",
            region_name=self.region
        )

    def query_agent(
        self,
        question: str,
        session_id: Optional[str] = None,
        max_tokens: int = 1000
    ) -> Dict:
        """
        Query the Bedrock Agent and get a response with citations

        Args:
            question: The user's question
            session_id: Optional session ID for conversation continuity
            max_tokens: Maximum tokens for response (not used by agent, kept for compatibility)

        Returns:
            Dictionary containing answer and source documents
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        try:
            # Invoke the agent
            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=question
            )

            # Process the response stream
            full_response = ""
            citations = []
            sources = []

            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        text = chunk['bytes'].decode('utf-8')
                        full_response += text

                    # Extract citations from chunk attribution (like your POC)
                    if 'attribution' in chunk and 'citations' in chunk['attribution']:
                        for citation in chunk['attribution']['citations']:
                            for ref in citation.get('retrievedReferences', []):
                                if ref.get('location', {}).get('type') == 'CONFLUENCE':
                                    citations.append({
                                        "url": ref['location']['confluenceLocation']['url'],
                                        "title": ref.get('metadata', {}).get('x-amz-bedrock-kb-title', ''),
                                        "author": ref.get('metadata', {}).get('x-amz-bedrock-kb-author', ''),
                                        "content_preview": ref['content']['text'][:200] + "..."
                                    })

                # Also check event-level attribution (backup)
                if 'attribution' in event:
                    attribution = event['attribution']
                    if 'citations' in attribution:
                        for citation in attribution['citations']:
                            # Extract source information with proper URL handling
                            for reference in citation.get('retrievedReferences', []):
                                location = reference.get('location', {})

                                # Initialize source info
                                source_info = {
                                    'snippet': reference.get('content', {}).get('text', '')[:200],
                                    'score': reference.get('score', 0)
                                }

                                # Handle different location types
                                if location.get('type') == 'CONFLUENCE':
                                    confluence_loc = location.get('confluenceLocation', {})
                                    source_info.update({
                                        'url': confluence_loc.get('url', ''),
                                        'title': reference.get('metadata', {}).get('x-amz-bedrock-kb-title', ''),
                                        'author': reference.get('metadata', {}).get('x-amz-bedrock-kb-author', ''),
                                        'source': confluence_loc.get('url', 'Unknown'),
                                        'content_preview': reference.get('content', {}).get('text', '')[:200] + "..."
                                    })
                                elif location.get('type') == 'S3':
                                    s3_loc = location.get('s3Location', {})
                                    source_info.update({
                                        'source': s3_loc.get('uri', 'Unknown'),
                                        'url': s3_loc.get('uri', '') if s3_loc.get('uri', '').startswith('http') else ''
                                    })
                                else:
                                    # Generic handling
                                    source_info['source'] = str(location.get('uri', 'Unknown'))
                                    if location.get('uri', '').startswith('http'):
                                        source_info['url'] = location.get('uri', '')

                                sources.append(source_info)

            # Merge citations and sources, prioritizing citations with URLs
            all_sources = citations + sources

            # Remove duplicates and ensure required fields
            unique_sources = []
            seen_sources = set()
            for source in all_sources:
                source_key = source.get('url') or source.get('source', 'unknown')
                if source_key not in seen_sources:
                    seen_sources.add(source_key)

                    # Ensure all required fields are present
                    normalized_source = {
                        'source': source.get('source', source.get('url', 'Unknown')),
                        'score': source.get('score', 0.0),
                        'snippet': source.get('snippet', source.get('content_preview', ''))[:200],
                        'url': source.get('url'),
                        'title': source.get('title'),
                        'author': source.get('author'),
                        'content_preview': source.get('content_preview')
                    }
                    unique_sources.append(normalized_source)

            return {
                'answer': full_response if full_response else "No response generated",
                'sources': unique_sources[:5],  # Limit to 5 sources
                'session_id': session_id,
                'agent_id': self.agent_id
            }

        except Exception as e:
            print(f"Error querying agent: {str(e)}")
            raise

    def stream_query(
        self,
        question: str,
        session_id: Optional[str] = None
    ) -> Generator[Dict, None, None]:
        """
        Stream the response from Bedrock Agent (simulated streaming for better UX)

        Args:
            question: The user's question
            session_id: Optional session ID for conversation continuity

        Yields:
            Chunks of the response with metadata or content
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        try:
            # First, get the complete response
            result = self.query_agent(question, session_id)

            # Send sources first
            if result.get('sources'):
                yield {
                    'type': 'metadata',
                    'sources': result['sources'],
                    'session_id': session_id
                }

            # Simulate streaming by chunking the response
            full_text = result.get('answer', '')

            # Split into words and stream them in small chunks
            words = full_text.split()
            chunk_size = 5  # Send 5 words at a time for faster streaming

            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_text = ' '.join(chunk_words)
                if i + chunk_size < len(words):
                    chunk_text += ' '  # Add space if not last chunk

                yield {
                    'type': 'content',
                    'text': chunk_text
                }

                # No delay for instant streaming

        except Exception as e:
            print(f"Error streaming from agent: {str(e)}")
            yield {
                'type': 'error',
                'message': str(e)
            }