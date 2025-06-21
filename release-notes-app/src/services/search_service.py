"""Service for performing RAG search operations."""

import json
import logging
from typing import List, Optional

from config.prompts import PromptTemplates
from models.data_models import SearchResult, LLMParameters
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class SearchService:
    """Service for RAG search operations."""
    
    def __init__(self, openai_service: OpenAIService):
        """Initialize with OpenAI service dependency."""
        self.openai_service = openai_service
    
    def perform_rag_search(
        self,
        queries: List[str],
        additional_info: Optional[dict] = None,
        parameters: Optional[LLMParameters] = None,
        semantic_config: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Perform RAG search for multiple queries.
        
        Args:
            queries: List of search queries
            additional_info: Additional context information
            parameters: LLM parameters for search
            semantic_config: Semantic configuration to use
            
        Returns:
            List of search results
        """
        if parameters is None:
            parameters = LLMParameters(use_search=True)
        else:
            parameters.use_search = True
        
        search_results = []
        logger.info(f"Starting RAG search for {len(queries)} queries")
        
        for query in queries:
            try:
                logger.debug(f"Searching for query: {query}")
                
                content = self.openai_service.generate_completion(
                    prompt=PromptTemplates.CONTEXT_RETRIEVER,
                    additional_info=query,
                    parameters=parameters,
                    semantic_config=semantic_config
                )
                
                # Skip if no relevant information found
                if self._is_no_information_response(content):
                    logger.info(f"No information found for query: {query}")
                    continue
                
                result = SearchResult(
                    query=query,
                    content=content,
                    additional_info=additional_info
                )
                
                search_results.append(result)
                logger.debug(f"Found content for query: {query[:50]}...")
                
            except Exception as e:
                logger.error(f"Error searching for query '{query}': {e}")
                continue
        
        logger.info(f"RAG search completed. Found {len(search_results)} results")
        return search_results
    
    def build_search_context(self, search_results: List[SearchResult]) -> str:
        """
        Build search context from search results.
        
        Args:
            search_results: List of search results
            
        Returns:
            JSON string containing query-answer pairs
        """
        if not search_results:
            return ""
        
        try:
            result_dict = {}
            for result in search_results:
                query_key = f"Query: {result.query}"
                answer_value = f"Answer: {result.content}"
                result_dict[query_key] = answer_value
            
            return json.dumps(result_dict)
            
        except Exception as e:
            logger.error(f"Error building search context: {e}")
            return ""
    
    @staticmethod
    def _is_no_information_response(content: str) -> bool:
        """Check if the response indicates no information was found."""
        no_info_indicators = [
            "No relevant information found in the documentation",
            "requested information is not"
        ]
        return any(indicator in content for indicator in no_info_indicators)
