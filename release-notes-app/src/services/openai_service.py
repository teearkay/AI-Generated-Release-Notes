"""OpenAI service for LLM interactions."""

import logging
from typing import Optional, Dict, Any
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from config.settings import config
from models.data_models import LLMParameters

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with Azure OpenAI."""
    
    def __init__(self):
        """Initialize the OpenAI service with authentication."""
        try:
            self.token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
            
            self.client = AzureOpenAI(
                azure_endpoint=config.openai_endpoint,
                azure_ad_token_provider=self.token_provider,
                api_version=config.api_version,
            )
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {e}")
            raise
    def generate_completion(
        self,
        prompt: str,
        additional_info: Optional[str] = None,
        parameters: Optional[LLMParameters] = None,
        semantic_config: Optional[str] = None
    ) -> str:
        """
        Generate completion using Azure OpenAI.
        
        Args:
            prompt: The main prompt for the LLM
            additional_info: Additional context information
            parameters: LLM parameters for the request
            semantic_config: Semantic configuration for search
            
        Returns:
            Generated completion text
            
        Raises:
            Exception: If the API call fails
        """
        import time
        start_time = time.time()
        
        if parameters is None:
            parameters = LLMParameters()
        
        try:
            # Log detailed request information
            prompt_length = len(prompt)
            additional_length = len(additional_info) if additional_info else 0
            logger.info(f"OPENAI: Starting completion request")
            logger.info(f"OPENAI: Model: {config.deployment_name}")
            logger.info(f"OPENAI: Endpoint: {config.openai_endpoint}")
            logger.info(f"OPENAI: Prompt length: {prompt_length} chars")
            logger.info(f"OPENAI: Additional info length: {additional_length} chars")
            logger.info(f"OPENAI: Parameters - max_tokens: {parameters.max_tokens}, temperature: {parameters.temperature}")
            logger.info(f"OPENAI: Parameters - use_search: {parameters.use_search}, strictness: {parameters.strictness}")
            logger.info(f"OPENAI: Semantic config: {semantic_config}")
            logger.debug(f"OPENAI: Prompt content preview: {prompt[:300]}...")
            if additional_info:
                logger.debug(f"OPENAI: Additional info preview: {additional_info[:200]}...")
            
            # Build messages with logging
            messages = [{"role": "user", "content": prompt}]
            
            if additional_info and not parameters.use_search:
                original_content = messages[0]["content"]
                messages[0]["content"] = f"{prompt}\nAdditional Details: {additional_info}"
                logger.info(f"OPENAI: Added additional info to prompt (+{len(messages[0]['content']) - len(original_content)} chars)")
            
            # Prepare completion arguments
            completion_args = {
                "model": config.deployment_name,
                "messages": messages,
                "max_tokens": parameters.max_tokens,
                "temperature": parameters.temperature,
                "top_p": 1 if not parameters.use_search else 0.5,
                "frequency_penalty": 0 if not parameters.use_search else 0.5,
                "presence_penalty": 0,
                "stop": None,
                "stream": False
            }
            logger.info(f"OPENAI: Final message count: {len(messages)}")
            logger.info(f"OPENAI: Total input length: {sum(len(msg['content']) for msg in messages)} chars")
            logger.info(f"OPENAI: Request parameters - top_p: {completion_args['top_p']}, freq_penalty: {completion_args['frequency_penalty']}")
            logger.debug(f"OPENAI: Final message content preview: {messages[0]['content'][:400]}...")
            
            # Add search configuration if needed
            if parameters.use_search:
                logger.info(f"OPENAI: Configuring RAG search. Semantic config: {semantic_config or config.default_semantic_config}")
                search_config_start = time.time()
                completion_args["extra_body"] = self._build_search_config(
                    prompt, additional_info, semantic_config, parameters
                )
                search_config_time = time.time() - search_config_start
                logger.info(f"OPENAI: Search config built in {search_config_time:.3f}s")
                logger.info(f"OPENAI: Semantic config: {semantic_config}")
            
            # Make the API call
            logger.info("OPENAI: Sending request to Azure OpenAI")
            api_start = time.time()
            completion = self.client.chat.completions.create(**completion_args)
            api_time = time.time() - api_start
            logger.info(f"OPENAI: API call completed in {api_time:.3f}s")
            
            # Process response
            if completion.choices and len(completion.choices) > 0:
                response_content = completion.choices[0].message.content
                response_length = len(response_content) if response_content else 0
                  # Enhanced response logging
                logger.info(f"OPENAI: Response received successfully")
                logger.info(f"OPENAI: Response length: {response_length} characters")
                logger.info(f"OPENAI: Number of choices: {len(completion.choices)}")
                logger.info(f"OPENAI: Response preview (first 200 chars): {response_content[:200]}...")
                if response_length > 200:
                    logger.debug(f"OPENAI: Response preview (last 100 chars): ...{response_content[-100:]}")
                
                # Log completion reason
                if hasattr(completion.choices[0], 'finish_reason'):
                    finish_reason = completion.choices[0].finish_reason
                    logger.info(f"OPENAI: Completion finish reason: {finish_reason}")
                    if finish_reason == 'length':
                        logger.warning("OPENAI: Response was truncated due to max token limit")
                    elif finish_reason == 'content_filter':
                        logger.warning("OPENAI: Response was filtered due to content policy")
                  # Enhanced usage and performance logging
                if hasattr(completion, 'usage') and completion.usage:
                    usage = completion.usage
                    logger.info(f"OPENAI: Token usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
                    
                    # Calculate cost estimate (approximate)
                    cost_per_1k_prompt = 0.003  # Approximate cost for GPT-4
                    cost_per_1k_completion = 0.006
                    estimated_cost = (usage.prompt_tokens * cost_per_1k_prompt / 1000) + (usage.completion_tokens * cost_per_1k_completion / 1000)
                    logger.info(f"OPENAI: Estimated cost: ${estimated_cost:.4f}")
                    
                    # Token efficiency metrics
                    if usage.prompt_tokens > 0:
                        efficiency = usage.completion_tokens / usage.prompt_tokens
                        logger.info(f"OPENAI: Token efficiency ratio (output/input): {efficiency:.2f}")
                    
                    # Check if we're approaching token limits
                    if usage.total_tokens > parameters.max_tokens * 0.9:
                        logger.warning(f"OPENAI: High token usage ({usage.total_tokens}/{parameters.max_tokens})")
                else:
                    logger.warning("OPENAI: No usage information available in response")

                # Enhanced quality and performance analysis
                if response_length == 0:
                    logger.warning("OPENAI: Received empty response")
                elif response_length < 10:
                    logger.warning(f"OPENAI: Received very short response: {response_length} chars")
                elif response_length < 50:
                    logger.info(f"OPENAI: Received short response: {response_length} chars")
                elif response_length > 2000:
                    logger.info(f"OPENAI: Received long response: {response_length} chars")
                
                # Content quality checks
                if "error" in response_content.lower():
                    logger.warning("OPENAI: Response contains error indicators")
                if "sorry" in response_content.lower() and "cannot" in response_content.lower():
                    logger.warning("OPENAI: Response indicates inability to fulfill request")
                
                total_time = time.time() - start_time
                chars_per_second = response_length / total_time if total_time > 0 else 0
                logger.info(f"OPENAI: Total completion time: {total_time:.3f}s")
                logger.info(f"OPENAI: Generation speed: {chars_per_second:.1f} chars/sec")
                
                # Log structured response data for monitoring
                logger.info(f"OPENAI: SUCCESS - Model: {config.deployment_name}, Time: {total_time:.3f}s, Tokens: {usage.total_tokens if hasattr(completion, 'usage') and completion.usage else 'N/A'}, Chars: {response_length}")
                
                return response_content
            else:
                error_msg = "No completion choices returned from OpenAI"
                logger.error(f"OPENAI: {error_msg}")
                logger.error(f"OPENAI: Completion object: {completion}")
                raise Exception(error_msg)
        except Exception as e:
            total_time = time.time() - start_time
            error_type = type(e).__name__
            logger.error(f"OPENAI: FAILED - Error after {total_time:.3f}s - {error_type}: {str(e)}")
            logger.error(f"OPENAI: Model: {config.deployment_name}")
            logger.error(f"OPENAI: Endpoint: {config.openai_endpoint}")
            logger.error(f"OPENAI: Max tokens: {parameters.max_tokens}")
            logger.error(f"OPENAI: Temperature: {parameters.temperature}")
            logger.error(f"OPENAI: Use search: {parameters.use_search}")
            logger.error(f"OPENAI: Semantic config: {semantic_config}")
            
            # Log additional context for debugging
            try:
                logger.error(f"OPENAI: Input prompt length: {len(prompt)}")
                logger.error(f"OPENAI: Has additional info: {additional_info is not None}")
                logger.error(f"OPENAI: Additional info length: {len(additional_info) if additional_info else 0}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"OPENAI: HTTP status: {e.response.status_code}")
                    logger.error(f"OPENAI: HTTP response: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
                if hasattr(e, 'code'):
                    logger.error(f"OPENAI: Error code: {e.code}")
            except Exception as context_error:
                logger.error(f"OPENAI: Could not log error context: {context_error}")
            
            raise
    
    def _build_search_config(
        self,
        prompt: str,
        additional_info: Optional[str],
        semantic_config: Optional[str],
        parameters: LLMParameters
    ) -> Dict[str, Any]:
        """Build search configuration for RAG."""
        search_index = config.get_search_index(
            semantic_config or config.default_semantic_config
        )
        
        logger.debug(f"OPENAI: Build Search Configs: SearchIndex: {search_index}, SemanticConfig: {semantic_config or config.default_semantic_config}")
        
        return {
            "data_sources": [{
                "type": "azure_search",
                "parameters": {
                    "endpoint": config.search_endpoint,
                    "index_name": search_index,
                    "semantic_configuration": semantic_config or config.default_semantic_config,
                    "query_type": "semantic",
                    "fields_mapping": {},
                    "in_scope": True,
                    "role_information": prompt,
                    "filter": None,
                    "strictness": parameters.strictness,
                    "top_n_documents": 3,
                    "authentication": {
                        "type": "system_assigned_managed_identity"
                    }
                }
            }]
        }
