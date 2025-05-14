import os
import logging
import traceback
from typing import List, Dict, Any, Optional, Union, Tuple
import json

from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.vector_stores.types import VectorStore
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.llms import ChatMessage, MessageRole
from pymilvus import MilvusException
from dotenv import load_dotenv
from qdrant_client import QdrantClient

from ..core.config import settings as app_settings
from ..db.firebase import FirestoreDB
from ..db.vector_store import get_vector_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGStatus:
    """Constants for RAG status"""
    SUCCESS = "rag_success"
    FALLBACK = "llm_fallback"
    ERROR = "error"
    NO_RESULTS = "no_context_found"
    NO_DOCUMENTS = "no_documents"

class QueryEngine:
    def __init__(self):
        self.firestore = FirestoreDB()
        self.vector_db = get_vector_db()
        self.last_sources = []
        
        # Initialize LLM
        self.llm = Groq(
            model=app_settings.LLM_MODEL,
            max_tokens=app_settings.LLM_MAX_TOKENS,
            temperature=app_settings.LLM_TEMPERATURE
        )
        
        # Initialize embedding model - renamed from embed_model to embeddings
        self.embeddings = HuggingFaceEmbedding(
            model_name=app_settings.EMBEDDING_MODEL
        )
        
        # Initialize settings
        Settings.llm = self.llm
        Settings.embed_model = self.embeddings
    
    async def create_service_context(self, temperature: Optional[float] = None):
        """Create settings with custom temperature
        
        Args:
            temperature: Optional temperature override
            
        Returns:
            None - updates global Settings
        """
        # Use custom temperature if provided
        if temperature is not None:
            llm = Groq(
                model=app_settings.LLM_MODEL,
                max_tokens=app_settings.LLM_MAX_TOKENS,
                temperature=temperature
            )
            Settings.llm = llm
        else:
            Settings.llm = self.llm
        
        Settings.embed_model = self.embeddings
    
    async def query(self, 
                    query: str, 
                    document_ids: Optional[List[str]] = None,
                    chatbot_id: Optional[str] = None,
                    temperature: Optional[float] = None,
                    instructions: Optional[str] = None,
                    max_tokens: Optional[int] = None,
                    model: Optional[str] = None) -> Union[str, Tuple[str, List[Dict[str, Any]], int, str]]:
        """Query the chatbot with user input"""
        try:
            logger.info(f"Starting query: '{query}'")
            logger.info(f"Parameters: temperature={temperature}, max_tokens={max_tokens}, model={model}")
            logger.info(f"Document IDs: {document_ids}")
            logger.info(f"Chatbot ID: {chatbot_id}")
            
            chatbot = None
            rag_status = RAGStatus.NO_DOCUMENTS
            
            # Get chatbot configuration if ID is provided
            if chatbot_id and not document_ids:
                logger.info(f"Fetching chatbot configuration for ID: {chatbot_id}")
                chatbot = await self.firestore.get_chatbot(chatbot_id)
                if not chatbot:
                    logger.error(f"Chatbot {chatbot_id} not found")
                    raise ValueError(f"Chatbot {chatbot_id} not found")
                
                # Get document IDs associated with this chatbot
                document_ids = chatbot.get('documents', [])
                logger.info(f"Found {len(document_ids)} documents associated with chatbot")
            
            # If no documents found, just use the LLM directly
            if not document_ids:
                logger.info("No documents provided, using LLM-only mode")
                response = await self._query_llm_only(query, temperature, instructions, chatbot)
                return response.get("response", "No response generated"), [], 0, RAGStatus.NO_DOCUMENTS
            
            try:
                # Update settings with custom temperature if provided
                await self.create_service_context(temperature)
                
                # Create vector store index
                logger.info("Creating vector store for documents")
                vector_store = await self._create_vector_store_for_documents(document_ids)
                index = VectorStoreIndex.from_vector_store(vector_store)
                logger.info("Vector store index created successfully")
                
                # Get query complexity to adjust retrieval parameters
                complexity = self._assess_query_complexity(query)
                logger.info(f"Query complexity assessment: {complexity}")
                
                # Adjust retrieval parameters based on query complexity
                similarity_top_k = 3  # Default
                similarity_cutoff = 0.6  # Default
                
                if complexity == "high":
                    similarity_top_k = 8
                    similarity_cutoff = 0.5
                elif complexity == "medium":
                    similarity_top_k = 5
                    similarity_cutoff = 0.55
                
                logger.info(f"Using retrieval parameters: top_k={similarity_top_k}, cutoff={similarity_cutoff}")
                
                # Create retriever with similarity threshold
                logger.info("Setting up retriever and query engine")
                retriever = VectorIndexRetriever(
                    index=index,
                    similarity_top_k=similarity_top_k,
                )
                
                # Create query engine
                query_engine = RetrieverQueryEngine.from_args(
                    retriever=retriever,
                    node_postprocessors=[
                        SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)
                    ]
                )
                
                # Add system instructions if provided
                system_prompt = self._build_system_prompt(instructions, chatbot)
                if system_prompt:
                    logger.info(f"Adding system prompt: {system_prompt}")
                    query_engine.update_prompts({"system_prompt": system_prompt})
                
                # Execute query
                logger.info("Executing query with vector search")
                response = query_engine.query(query)
                logger.info(f"Raw query response: {response}")
                
                # Extract source documents
                source_nodes = response.source_nodes if hasattr(response, 'source_nodes') else []
                sources = []
                
                if not source_nodes:
                    logger.warning("No source nodes found in response")
                    rag_status = RAGStatus.NO_RESULTS
                else:
                    rag_status = RAGStatus.SUCCESS
                    
                for node in source_nodes:
                    if hasattr(node, 'node') and hasattr(node.node, 'metadata'):
                        source = {
                            "document_id": node.node.metadata.get("document_id"),
                            "chunk_id": node.node.metadata.get("chunk_id"),
                            "score": node.score if hasattr(node, 'score') else None
                        }
                        sources.append(source)
                        logger.info(f"Found source: {source}")
                
                # Store sources for later use if needed
                self.last_sources = sources
                
                # Get response text
                response_text = str(response)
                if not response_text.strip():
                    logger.warning("Empty response from query engine")
                    response_text = "I apologize, but I'm having trouble generating a response based on the available information."
                
                # If we have no sources but still got a response, it's likely the LLM answered without context
                if not sources and rag_status != RAGStatus.NO_RESULTS:
                    rag_status = RAGStatus.FALLBACK
                    logger.warning("LLM answered without using context")
                
                # Estimate token usage (rough approximation)
                tokens_used = len(query.split()) + len(response_text.split())
                logger.info(f"Query complete. Response length: {len(response_text)}, Sources: {len(sources)}, Tokens: {tokens_used}")
                
                # Add fallback prefix if we couldn't find relevant content
                if rag_status == RAGStatus.NO_RESULTS:
                    fallback_prefix = "I couldn't find specific information about that in the knowledge base. "
                    if not response_text.startswith(fallback_prefix):
                        response_text = fallback_prefix + response_text
                
                return response_text, sources, tokens_used, rag_status
                
            except Exception as vector_error:
                logger.error(f"Vector search error: {str(vector_error)}")
                logger.error(f"Vector search traceback: {traceback.format_exc()}")
                rag_status = RAGStatus.ERROR
                
                # Fall back to LLM-only if vector search fails
                logger.info("Falling back to LLM-only mode due to vector search error")
                response = await self._query_llm_only(query, temperature, instructions, chatbot)
                return response.get("response", "I encountered an error while accessing knowledge base."), [], 0, rag_status
                
        except Exception as e:
            logger.error(f"Error in query method: {str(e)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            
            # Fall back to LLM-only if vector search fails
            try:
                logger.info("Falling back to LLM-only mode")
                response = await self._query_llm_only(query, temperature, instructions, chatbot)
                return response.get("response", "I encountered an error while accessing knowledge base."), [], 0, RAGStatus.FALLBACK
            except Exception as fallback_error:
                logger.error(f"Error in LLM fallback: {str(fallback_error)}")
                logger.error(f"Fallback error traceback: {traceback.format_exc()}")
                return "I apologize, but I encountered an unexpected error. Please try again later.", [], 0, RAGStatus.ERROR
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess query complexity to adjust retrieval parameters
        
        Args:
            query: The query text
            
        Returns:
            Complexity level: "low", "medium", or "high"
        """
        words = query.split()
        
        # Check for question words that indicate complex queries
        complex_indicators = ["why", "how", "explain", "describe", "compare", "contrast", "analyze", "relationship", "difference"]
        
        # Check if any complex indicator is in the query
        has_complex_indicator = any(word.lower() in complex_indicators for word in words)
        
        # Determine complexity based on length and indicators
        if len(words) > 15 or has_complex_indicator:
            return "high"
        elif len(words) > 8:
            return "medium"
        else:
            return "low"
    
    def _build_system_prompt(self, instructions: Optional[str] = None, chatbot: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Build system prompt from instructions and chatbot settings
        
        Args:
            instructions: Custom instructions
            chatbot: Chatbot configuration
            
        Returns:
            System prompt
        """
        prompt_parts = []
        
        # Add chatbot role if available
        if chatbot and "settings" in chatbot and "role" in chatbot["settings"] and chatbot["settings"]["role"]:
            prompt_parts.append(f"You are a {chatbot['settings']['role']}.")
        
        # Add chatbot instructions if available
        if chatbot and "settings" in chatbot and "instructions" in chatbot["settings"] and chatbot["settings"]["instructions"]:
            prompt_parts.append(f"{chatbot['settings']['instructions']}")
        
        # Add custom instructions if provided
        if instructions:
            prompt_parts.append(f"{instructions}")
        
        # Add RAG instructions
        prompt_parts.append("Use ONLY the provided context to answer the question. If the context doesn't contain the answer, admit that you don't know rather than making up information.")
        
        # Join all parts with spaces
        if prompt_parts:
            return " ".join(prompt_parts)
        
        return None
    
    async def _query_llm_only(self, 
                              query_text: str, 
                              temperature: Optional[float] = None,
                              instructions: Optional[str] = None,
                              chatbot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query LLM directly without vector search
        
        Args:
            query_text: Query text
            temperature: Optional temperature override
            instructions: Optional instructions
            chatbot: Optional chatbot configuration
            
        Returns:
            Dictionary with response
        """
        try:
            logger.info("Preparing LLM-only query as fallback")
            # Create the prompt
            system_prompt = self._build_llm_only_prompt(instructions, chatbot)
            
            # Important: Use ChatMessage objects for proper message formatting
            messages = []
            if system_prompt:
                logger.info(f"Using system prompt: {system_prompt[:100]}...")
                messages.append(ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))
            
            messages.append(ChatMessage(role=MessageRole.USER, content=query_text))
            logger.info(f"Created {len(messages)} messages for LLM")
            
            # Set up LLM with temperature
            temp_value = temperature if temperature is not None else app_settings.LLM_TEMPERATURE
            logger.info(f"Using LLM temperature: {temp_value}")
            
            # Initialize the LLM with our configuration
            llm = Groq(
                model=app_settings.LLM_MODEL,
                max_tokens=app_settings.LLM_MAX_TOKENS,
                temperature=temp_value
            )
            
            # Call LLM
            logger.info(f"Calling LLM with model: {app_settings.LLM_MODEL}")
            response = llm.chat(messages)
            logger.info(f"Received response from LLM: {type(response)}")
            
            # Extract response based on the type returned by the LLM
            response_content = ""
            
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                logger.info("Found content in response.message.content")
                response_content = response.message.content
            elif isinstance(response, dict) and 'content' in response:
                logger.info("Found content in response dictionary")
                response_content = response['content']
            elif isinstance(response, str):
                logger.info("Response is a string type")
                response_content = response
            else:
                logger.error(f"Unexpected response format: {type(response)}")
                logger.error(f"Response representation: {repr(response)}")
                response_content = "I'm having trouble generating a response right now."
            
            # Log response preview
            logger.info(f"LLM response generated ({len(response_content)} chars): {response_content[:100]}...")
            
            return {"response": response_content}
            
        except Exception as e:
            logger.error(f"Error in LLM-only query: {str(e)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            return {"response": "I'm having trouble generating a response right now. Please try again later."}
    
    def _build_llm_only_prompt(self, instructions: Optional[str] = None, chatbot: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for LLM-only mode
        
        Args:
            instructions: Custom instructions
            chatbot: Chatbot configuration
            
        Returns:
            System prompt
        """
        prompt_parts = []
        
        # Add chatbot role if available
        if chatbot and "settings" in chatbot and "role" in chatbot["settings"] and chatbot["settings"]["role"]:
            prompt_parts.append(f"You are a {chatbot['settings']['role']}.")
        
        # Add chatbot instructions if available
        if chatbot and "settings" in chatbot and "instructions" in chatbot["settings"] and chatbot["settings"]["instructions"]:
            prompt_parts.append(f"{chatbot['settings']['instructions']}")
        
        # Add custom instructions if provided
        if instructions:
            prompt_parts.append(f"{instructions}")
        
        # Add standard instructions
        prompt_parts.append("Answer the user's question to the best of your ability based on your general knowledge.")
        
        # Join all parts with spaces
        if prompt_parts:
            return " ".join(prompt_parts)
        
        return "You are a helpful assistant. Answer the user's question to the best of your ability."
    
    async def _create_vector_store_for_documents(self, document_ids: List[str]) -> VectorStore:
        """Create a vector store for the specified documents
        
        Args:
            document_ids: List of document IDs
            
        Returns:
            VectorStore object
        """
        try:
            if app_settings.VECTOR_DB_TYPE == "qdrant":
                logger.info("Creating QdrantVectorStore for documents")
                client = QdrantClient(url=app_settings.QDRANT_URL, api_key=app_settings.QDRANT_API_KEY)
                
                # Construct filter expression based on document IDs
                filter_expr = None
                if document_ids:
                    if len(document_ids) == 1:
                        filter_expr = {"document_id": document_ids[0]}
                    else:
                        filter_expr = {"document_id": {"$in": document_ids}}
                logger.info(f"Using filter expression: {filter_expr}")
                
                return QdrantVectorStore(
                    client=client,
                    collection_name=app_settings.QDRANT_COLLECTION_NAME,
                    embeddings=self.embeddings,  # Changed from embedding_function to embeddings
                    filter=filter_expr
                )
            else:
                # Create the filter expression for Milvus
                if len(document_ids) == 1:
                    filter_expr = f'document_id == "{document_ids[0]}"'
                else:
                    doc_ids_str = '", "'.join(document_ids)
                    filter_expr = f'document_id in ["{doc_ids_str}"]'
                logger.info(f"Using filter expression: {filter_expr}")

                return MilvusVectorStore(
                    uri=app_settings.MILVUS_URI,
                    token=app_settings.MILVUS_TOKEN,
                    collection_name=app_settings.MILVUS_COLLECTION_NAME,
                    embeddings=self.embeddings,  # Changed from embedding_function to embeddings
                    filter_expr=filter_expr
                )
            
            logger.info("Vector store created successfully")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            logger.error(f"Document IDs: {document_ids}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            raise

    async def get_context(self, query: str, document_ids: List[str]) -> Optional[str]:
        """Get relevant context from documents based on a query
        
        Args:
            query: The query to get context for
            document_ids: List of document IDs to search in
            
        Returns:
            String containing relevant context, or None if no context found
        """
        try:
            if not document_ids:
                logger.warning("No document IDs provided for context retrieval")
                self.last_sources = []
                return None
                
            logger.info(f"Getting context for query: '{query}' from {len(document_ids)} documents")
            logger.info(f"Document IDs: {document_ids}")
            
            # Create service context
            service_context = await self.create_service_context()
            logger.info(f"Created service context with LLM: {self.llm.__class__.__name__}")
            
            try:
                # Create vector store index
                logger.info(f"Creating vector store for documents: {document_ids}")
                vector_store = await self._create_vector_store_for_documents(document_ids)
                logger.info(f"Successfully created vector store for documents")
                
                index = VectorStoreIndex.from_vector_store(
                    vector_store,
                    service_context=service_context
                )
                logger.info(f"Successfully created vector index")
                
                # Create retriever with similarity threshold
                logger.info("Creating vector index retriever")
                retriever = VectorIndexRetriever(
                    index=index,
                    similarity_top_k=3,
                )
                
                # Add similarity score threshold
                postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)
                
                # Create query engine
                query_engine = RetrieverQueryEngine(
                    retriever=retriever,
                    node_postprocessors=[postprocessor]
                )
                
                # Get nodes from the query
                logger.info(f"Retrieving relevant nodes for query: '{query}'")
                retrieved_nodes = retriever.retrieve(query)
                
                # If no nodes found
                if not retrieved_nodes:
                    logger.info("No relevant nodes found for the query")
                    self.last_sources = []
                    return None
                
                # Extract context from nodes
                logger.info(f"Found {len(retrieved_nodes)} relevant nodes")
                context_texts = []
                self.last_sources = []
                
                for i, node in enumerate(retrieved_nodes):
                    content = node.get_content()
                    score = node.score or 0.0
                    doc_id = node.metadata.get("document_id", "unknown")
                    chunk_id = node.metadata.get("chunk_id", f"chunk-{i}")
                    
                    logger.info(f"Node {i+1}: Doc ID: {doc_id}, Chunk ID: {chunk_id}, Score: {score:.4f}")
                    logger.info(f"Content preview: {content[:100]}...")
                    
                    context_texts.append(content)
                    # Store source metadata
                    source_info = {
                        "documentId": doc_id,
                        "chunkId": chunk_id,
                        "score": score
                    }
                    self.last_sources.append(source_info)
                
                # Combine context texts
                context = "\n\n".join(context_texts)
                logger.info(f"Total context length: {len(context)} characters")
                return context
                
            except Exception as vector_error:
                logger.error(f"Error in vector search: {str(vector_error)}")
                import traceback
                logger.error(f"Vector search traceback: {traceback.format_exc()}")
                self.last_sources = []
                return None
        
        except Exception as e:
            logger.error(f"Error getting document context: {str(e)}")
            import traceback
            logger.error(f"Error trace: {traceback.format_exc()}")
            self.last_sources = []
            return None