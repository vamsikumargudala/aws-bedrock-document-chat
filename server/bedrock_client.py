import boto3
import os
from typing import Dict, List, Optional
import json
from dotenv import load_dotenv

load_dotenv()

class BedrockRAGClient:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.knowledge_base_id = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID")
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

        if not self.knowledge_base_id:
            raise ValueError("BEDROCK_KNOWLEDGE_BASE_ID must be set in environment variables")

        # Initialize Bedrock clients
        self.bedrock_agent = boto3.client(
            "bedrock-agent-runtime",
            region_name=self.region
        )

        self.bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=self.region
        )

    def query_knowledge_base(
        self,
        query: str,
        max_results: int = 5,
        max_tokens: int = 1000
    ) -> Dict:
        """
        Query the Bedrock Knowledge Base and generate a response

        Args:
            query: The user's question
            max_results: Maximum number of documents to retrieve
            max_tokens: Maximum tokens for the generated response

        Returns:
            Dictionary containing answer and source documents
        """
        try:
            # Retrieve relevant documents from knowledge base
            retrieval_response = self.bedrock_agent.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )

            # Extract retrieved documents
            retrieved_docs = []
            context_chunks = []

            for result in retrieval_response.get('retrievalResults', []):
                content = result.get('content', {}).get('text', '')
                location = result.get('location', {})
                score = result.get('score', 0)
                metadata = result.get('metadata', {})

                # Handle different location types and ensure required fields
                snippet = content[:200] + '...' if len(content) > 200 else content

                if location.get('type') == 'CONFLUENCE':
                    confluence_loc = location.get('confluenceLocation', {})
                    retrieved_docs.append({
                        'source': confluence_loc.get('url', 'Unknown'),
                        'score': score,
                        'snippet': snippet,
                        'url': confluence_loc.get('url', ''),
                        'title': metadata.get('x-amz-bedrock-kb-title', ''),
                        'author': metadata.get('x-amz-bedrock-kb-author', ''),
                        'content_preview': content[:200] + "..." if len(content) > 200 else content
                    })
                elif location.get('type') == 'S3':
                    s3_loc = location.get('s3Location', {})
                    uri = s3_loc.get('uri', 'Unknown')
                    retrieved_docs.append({
                        'source': uri,
                        'score': score,
                        'snippet': snippet,
                        'url': uri if uri.startswith('http') else None
                    })
                else:
                    # Fallback to original logic
                    source = location.get('s3Location', {}).get('uri', 'Unknown')
                    retrieved_docs.append({
                        'source': source,
                        'score': score,
                        'snippet': snippet
                    })

                context_chunks.append(content)

            # Prepare context for generation
            context = "\n\n".join(context_chunks)

            # Generate response using Claude
            prompt = self._build_prompt(query, context)

            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "top_p": 0.9
                })
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            answer = response_body.get('content', [{}])[0].get('text', 'No response generated')

            return {
                'answer': answer,
                'sources': retrieved_docs,
                'tokens_used': response_body.get('usage', {})
            }

        except Exception as e:
            print(f"Error querying knowledge base: {str(e)}")
            raise

    def _build_prompt(self, query: str, context: str) -> str:
        """Build the prompt for the LLM"""
        return f"""You are a helpful assistant answering questions based on the provided context.

Context from documents:
{context}

User Question: {query}

Instructions:
- Answer based solely on the provided context
- If the context doesn't contain enough information, say so
- Be concise but thorough
- Reference specific information from the context when possible

Answer:"""

    def stream_query(self, query: str, max_results: int = 5):
        """
        Stream the response for real-time updates

        Args:
            query: The user's question
            max_results: Maximum number of documents to retrieve

        Yields:
            Chunks of the generated response
        """
        # First, retrieve documents
        retrieval_response = self.bedrock_agent.retrieve(
            knowledgeBaseId=self.knowledge_base_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': max_results
                }
            }
        )

        # Build context
        context_chunks = []
        sources = []

        for result in retrieval_response.get('retrievalResults', []):
            content = result.get('content', {}).get('text', '')
            location = result.get('location', {})
            metadata = result.get('metadata', {})

            context_chunks.append(content)

            # Handle different location types for streaming and ensure required fields
            snippet = content[:200] + '...' if len(content) > 200 else content

            if location.get('type') == 'CONFLUENCE':
                confluence_loc = location.get('confluenceLocation', {})
                sources.append({
                    'source': confluence_loc.get('url', 'Unknown'),
                    'score': 0.0,
                    'snippet': snippet,
                    'url': confluence_loc.get('url', ''),
                    'title': metadata.get('x-amz-bedrock-kb-title', ''),
                    'author': metadata.get('x-amz-bedrock-kb-author', ''),
                    'content_preview': content[:200] + "..." if len(content) > 200 else content
                })
            elif location.get('type') == 'S3':
                s3_loc = location.get('s3Location', {})
                uri = s3_loc.get('uri', 'Unknown')
                sources.append({
                    'source': uri,
                    'score': 0.0,
                    'snippet': snippet,
                    'url': uri if uri.startswith('http') else None
                })
            else:
                # Fallback
                source = location.get('s3Location', {}).get('uri', 'Unknown')
                sources.append({
                    'source': source,
                    'score': 0.0,
                    'snippet': snippet
                })

        context = "\n\n".join(context_chunks)
        prompt = self._build_prompt(query, context)

        # Stream response
        response = self.bedrock_runtime.invoke_model_with_response_stream(
            modelId=self.model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3
            })
        )

        # Yield metadata first
        yield {
            'type': 'metadata',
            'sources': sources
        }

        # Stream the response chunks
        for event in response.get('body'):
            chunk = json.loads(event['chunk']['bytes'])
            if chunk.get('type') == 'content_block_delta':
                text = chunk.get('delta', {}).get('text', '')
                if text:
                    yield {
                        'type': 'content',
                        'text': text
                    }