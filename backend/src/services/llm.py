from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime

from llama_index.llms.groq import Groq
from llama_index.core import Settings

from ..core.config import settings
from ..models.chatbot import ChatbotSettings, ChatMessage

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, temperature: Optional[float] = None, max_tokens: Optional[int] = None, model: Optional[str] = None):
        """Initialize the LLM service with Groq"""
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS
        self.model = model if model is not None else settings.LLM_MODEL
        
        # Initialize Groq LLM
        try:
            self.llm = Groq(
                api_key=settings.GROQ_API_KEY,
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            logger.info(f"Initialized Groq LLM with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq LLM: {str(e)}")
            raise
    
    async def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt
        
        Args:
            prompt: The prompt to generate text from
            
        Returns:
            Generated text
        """
        try:
            response = self.llm.complete(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Failed to generate text: {str(e)}")
    
    async def generate_chat_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a response from a list of chat messages
        
        Args:
            messages: List of chat messages in the format [{"role": "user", "content": "..."}]
            
        Returns:
            Generated response
        """
        try:
            response = self.llm.chat(messages)
            return response.message.content
        except Exception as e:
            raise Exception(f"Failed to generate chat response: {str(e)}")
    
    async def generate_with_context(self, query: str, context: str, instructions: Optional[str] = None) -> str:
        """Generate a response from a query and context
        
        Args:
            query: The user query
            context: The context to use for generation
            instructions: Optional system instructions
            
        Returns:
            Generated response
        """
        try:
            messages = []
            
            # Add system instructions if provided
            if instructions:
                messages.append({"role": "system", "content": instructions})
            
            # Add context and query
            messages.append({"role": "user", "content": f"Context information:\n{context}\n\nQuestion: {query}"})
            
            response = self.llm.chat(messages)
            return response.message.content
        except Exception as e:
            raise Exception(f"Failed to generate response with context: {str(e)}")

    async def generate_response(
        self,
        message: str,
        chat_history: List[ChatMessage],
        settings: ChatbotSettings,
        context: Optional[str] = None
    ) -> str:
        """Generate a response using the LLM model"""
        try:
            logger.info(f"Generating response with settings: {json.dumps(settings.__dict__)}")
            logger.info(f"Message: {message}")
            logger.info(f"Chat history length: {len(chat_history)}")
            if context:
                logger.info(f"Context provided: {len(context)} characters")
            else:
                logger.info("No context provided")
            
            # Build the conversation history
            formatted_messages = []
            
            # Add system instructions if available
            system_message = ""
            if settings.role:
                system_message += f"You are a {settings.role}. "
            
            if settings.instructions:
                system_message += settings.instructions
            
            if system_message:
                formatted_messages.append({
                    "role": "system",
                    "content": system_message
                })
            
            # Add context if available
            if context:
                context_message = "Here is relevant information from the knowledge base that you should use to answer the user's question:\n\n"
                context_message += context
                context_message += "\n\nPlease rely on this information to provide accurate answers. If the information does not contain the answer, acknowledge that and provide a general response based on what you know."
                
                formatted_messages.append({
                    "role": "system",
                    "content": context_message
                })
            
            # Add chat history
            for msg in chat_history:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add user message
            formatted_messages.append({
                "role": "user",
                "content": message
            })
            
            logger.info(f"Sending request to Groq with {len(formatted_messages)} messages")
            
            try:
                # Update LLM settings for this request
                self.llm.temperature = settings.temperature
                self.llm.max_tokens = settings.maxTokens
                
                # If in development or mock mode, return a mock response
                if settings.model == "mock":
                    logger.info("Using mock response mode")
                    return self._generate_mock_response(message, settings.role)
                
                # For real API calls, properly format messages for Groq
                from llama_index.core.llms import ChatMessage, MessageRole
                
                chat_messages = []
                for msg in formatted_messages:
                    role = msg["role"]
                    content = msg["content"]
                    
                    # Convert role string to MessageRole enum
                    if role == "system":
                        role_enum = MessageRole.SYSTEM
                    elif role == "user":
                        role_enum = MessageRole.USER
                    elif role == "assistant":
                        role_enum = MessageRole.ASSISTANT
                    else:
                        # Default to user for unknown roles
                        role_enum = MessageRole.USER
                    
                    chat_message = ChatMessage(
                        role=role_enum,
                        content=content
                    )
                    chat_messages.append(chat_message)
                
                # Call the LLM with proper error handling
                try:
                    logger.info("Calling LLM API with structured messages")
                    response = self.llm.chat(chat_messages)
                    
                    # Extract response content safely
                    if hasattr(response, 'message') and hasattr(response.message, 'content'):
                        result = response.message.content
                    else:
                        logger.warning("Unexpected response format, falling back to string conversion")
                        result = str(response)
                        
                    logger.info(f"LLM response successfully generated ({len(result)} chars)")
                    return result
                    
                except Exception as api_error:
                    logger.error(f"LLM API error: {str(api_error)}")
                    raise
                
            except Exception as e:
                logger.error(f"Error during LLM call: {str(e)}")
                import traceback
                logger.error(f"LLM error traceback: {traceback.format_exc()}")
                
                # Provide a reasonable fallback response
                if settings.role:
                    return f"As a {settings.role}, I'd like to help with your question about '{message}'. However, I'm experiencing technical difficulties at the moment. Please try again or rephrase your question."
                else:
                    return "I apologize, but I'm experiencing technical difficulties and cannot generate a proper response at the moment. Please try again shortly."

        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request. Please try again later."
            
    def _generate_mock_response(self, message: str, role: Optional[str] = None) -> str:
        """Generate a realistic mock response for development and testing
        
        Args:
            message: The user's message
            role: Optional role to personalize the response
            
        Returns:
            A mock response
        """
        # Create role-specific mock responses
        if "hr policies" in message.lower() or "company policy" in message.lower():
            return "Based on our company HR policies, employees are entitled to 20 days of paid time off annually, flexible working hours, and remote work options twice a week. Health insurance coverage begins after 30 days of employment. Please consult the employee handbook for more detailed information."
            
        if "pricing" in message.lower() or "cost" in message.lower() or "subscription" in message.lower():
            return "Our pricing structure includes three tiers: Basic ($9.99/month), Professional ($19.99/month), and Enterprise ($49.99/month). Each tier offers different features such as API access, priority support, and custom integrations. I'd be happy to provide more details about any specific tier you're interested in."
            
        if "help" in message.lower() or "support" in message.lower() or "contact" in message.lower():
            return "For technical support, you can contact our help desk at support@example.com or call our 24/7 support line at 1-800-555-0123. For billing inquiries, please email billing@example.com. Our typical response time is within 2 business hours."
            
        # Role-specific default responses
        if role and role.lower() == "customer support agent":
            return f"Thank you for your question about '{message}'. As a customer support representative, I'm here to help resolve your inquiry. Based on the information available, I can assist with product features, account management, and technical troubleshooting. Could you please provide more specific details so I can better address your needs?"
            
        elif role and role.lower() == "sales agent":
            return f"Thanks for your interest in '{message}'. As a sales representative, I can provide detailed information about our products, pricing options, and current promotions. Our solutions are designed to meet various business needs and scale with your growth. Would you like to schedule a personalized demo to see how our offerings can benefit your specific use case?"
            
        elif role and role.lower() == "language tutor":
            return f"That's a great question about '{message}'. When learning a new language, it's important to understand both the grammar rules and practical usage. I recommend practicing this concept in everyday conversations to reinforce your learning. Would you like some example sentences to help with your practice?"
            
        elif role and role.lower() == "coding expert":
            return f"Regarding your question about '{message}', this is a common programming challenge. The most efficient approach typically involves optimizing your algorithm for both time and space complexity. Consider using a hash map to store intermediate results, which can reduce redundant calculations. Would you like me to explain this solution with a code example?"
            
        # Generic response if no specific matches
        return f"I understand you're asking about '{message}'. Based on the information available, I can provide you with a comprehensive answer tailored to your specific question. Is there anything particular about this topic you'd like me to elaborate on?"

    async def get_document_context(
        self,
        query: str,
        document_ids: List[str],
        max_tokens: int = 1024
    ) -> Optional[str]:
        """Get relevant context from documents using vector search"""
        try:
            # TODO: Implement vector search to retrieve relevant document chunks
            # For now, return a mock context for testing
            return f"Here is some relevant information about {query}..."
        except Exception as e:
            logger.error(f"Error getting document context: {str(e)}")
            return None