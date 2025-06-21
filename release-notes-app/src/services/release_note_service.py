"""Core business logic for release note generation."""

import json
import logging
from typing import Optional, Dict, Any

from config.prompts import PromptTemplates
from config.settings import config
from models.data_models import (
    WorkItemInput, WorkItemDetails, ReleaseNoteResult, LLMParameters
)
from services.openai_service import OpenAIService
from services.parsing_service import ParsingService
from services.search_service import SearchService
from utils.enhanced_logging import create_enhanced_logger, log_exceptions

logger = logging.getLogger(__name__)
enhanced_logger = create_enhanced_logger(__name__)


class ReleaseNoteGenerator:
    """Core service for generating release notes from work items."""
    
    def __init__(self):
        """Initialize the release note generator with required services."""
        self.openai_service = OpenAIService()
        self.search_service = SearchService(self.openai_service)
        self.parsing_service = ParsingService()
        
    def generate_release_notes(
        self,
        work_item_input: WorkItemInput,
        max_tokens: int = 800,
        temperature: float = 0.2,
        search_max_tokens: int = 800,
        search_temperature: float = 0,
        use_internal_doc: bool = False,
        remove_internal_keywords: bool = False
    ) -> Optional[ReleaseNoteResult]:
        """
        Generate release notes from work item input.
        
        Args:
            work_item_input: Input containing work item data
            max_tokens: Maximum tokens for LLM requests
            temperature: Temperature for LLM requests
            search_max_tokens: Maximum tokens for search requests
            search_temperature: Temperature for search requests
            use_internal_doc: Whether to use internal documentation
            remove_internal_keywords: Whether to remove internal keywords
            
        Returns:
            ReleaseNoteResult containing all generated content
        """
        import time
        start_time = time.time()
        
        try:
            logger.info("SERVICE: Starting release note generation pipeline")
            logger.info(f"SERVICE: Parameters - max_tokens: {max_tokens}, temperature: {temperature}")
            logger.info(f"SERVICE: Search params - max_tokens: {search_max_tokens}, temperature: {search_temperature}")
            logger.info(f"SERVICE: Flags - use_internal_doc: {use_internal_doc}, remove_keywords: {remove_internal_keywords}")
            
            # Validate input
            if not work_item_input or not work_item_input.payload:
                logger.error("SERVICE: Invalid input - work_item_input or payload is None")
                return None
            
            # Get semantic configuration
            semantic_start = time.time()
            semantic_config = config.get_semantic_config(work_item_input.documentation)
            semantic_time = time.time() - semantic_start
            logger.info(f"SERVICE: Semantic config retrieved in {semantic_time:.3f}s: {semantic_config}")
            
            # Step 1: Analyze work item details
            logger.info("SERVICE: Step 1 - Analyzing work item details")
            analysis_start = time.time()
            work_item_details = self._analyze_work_item(
                work_item_input.payload, max_tokens, temperature
            )
            analysis_time = time.time() - analysis_start
            logger.info(f"SERVICE: Work item analysis completed in {analysis_time:.3f}s")
            if not work_item_details:
                logger.error("SERVICE: Failed to analyze work item details - analysis returned None")
                return None
            
            logger.info(f"SERVICE: Analysis result - Description: {work_item_details.short_description[:100] if work_item_details.short_description else 'None'}...")
            logger.info(f"SERVICE: Analysis result - Description length: {len(work_item_details.short_description) if work_item_details.short_description else 0}")
            
            # Step 2: Generate search queries
            logger.info("SERVICE: Step 2 - Generating search queries")
            query_start = time.time()
            queries = self._generate_queries(work_item_details, max_tokens, temperature)
            query_time = time.time() - query_start
            logger.info(f"SERVICE: Query generation completed in {query_time:.3f}s")
            logger.info(f"SERVICE: Generated {len(queries)} search queries")
            
            # Step 3: Perform RAG search
            logger.info("SERVICE: Step 3 - Performing RAG search")
            search_start = time.time()
            search_results = self.search_service.perform_rag_search(
                queries=queries,
                parameters=LLMParameters(
                    max_tokens=search_max_tokens,
                    temperature=search_temperature,
                    use_internal_doc=use_internal_doc
                ),
                semantic_config=semantic_config
            )
            search_time = time.time() - search_start
            logger.info(f"SERVICE: RAG search completed in {search_time:.3f}s")
            logger.info(f"SERVICE: Search returned {len(search_results) if search_results else 0} results")
            
            # Step 4: Build search context
            logger.info("SERVICE: Step 4 - Building search context")
            context_start = time.time()
            search_context = self.search_service.build_search_context(search_results)
            context_time = time.time() - context_start
            context_length = len(search_context) if search_context else 0
            logger.info(f"SERVICE: Search context built in {context_time:.3f}s, length: {context_length} chars")
            
            # Step 5: Generate user impact summary
            logger.info("SERVICE: Step 5 - Generating user impact summary")
            impact_start = time.time()
            user_impact = self._generate_user_impact(
                search_context, work_item_details.short_description, max_tokens, temperature
            )
            impact_time = time.time() - impact_start
            impact_length = len(user_impact) if user_impact else 0
            logger.info(f"SERVICE: User impact generation completed in {impact_time:.3f}s, length: {impact_length} chars")
            
            # Step 6: Generate release notes
            logger.info("SERVICE: Step 6 - Generating final release notes")
            final_start = time.time()
            release_notes = self._generate_final_release_notes(
                work_item_details=work_item_details,
                search_context=search_context,
                user_impact=user_impact,
                max_tokens=max_tokens,
                temperature=temperature,
                use_internal_doc=use_internal_doc,
                remove_internal_keywords=remove_internal_keywords,
                semantic_config=semantic_config
            )
            final_time = time.time() - final_start
            logger.info(f"SERVICE: Final release notes generated in {final_time:.3f}s")
            logger.info(f"SERVICE: Generated {len(release_notes)} release note variants")
            
            # Create and validate result
            result = ReleaseNoteResult(
                work_item_details=work_item_details,
                queries=queries,
                search_context=search_context,
                user_impact=user_impact,
                release_notes=release_notes
            )
            
            # Log pipeline completion metrics
            total_time = time.time() - start_time
            logger.info(f"SERVICE: Release note generation pipeline completed successfully in {total_time:.3f}s")
            logger.info(f"SERVICE: Pipeline breakdown - Analysis: {analysis_time:.3f}s, Queries: {query_time:.3f}s, Search: {search_time:.3f}s, Context: {context_time:.3f}s, Impact: {impact_time:.3f}s, Final: {final_time:.3f}s")
            
            # Quality metrics
            primary_note = release_notes.get("ReleaseNote", "")
            if primary_note:
                note_length = len(primary_note)
                logger.info(f"SERVICE: Primary release note length: {note_length} characters")
                if note_length < 100:
                    logger.warning(f"SERVICE: Release note is shorter than expected: {note_length} chars")
                elif note_length > 1500:
                    logger.warning(f"SERVICE: Release note is longer than expected: {note_length} chars")
            
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            error_type = type(e).__name__
            logger.error(f"SERVICE: Critical error in generation pipeline after {total_time:.3f}s")
            logger.error(f"SERVICE: Error type: {error_type}")
            logger.error(f"SERVICE: Error message: {str(e)}")
            
            # Log context for debugging
            try:
                logger.error(f"SERVICE: Input documentation: {work_item_input.documentation if work_item_input else 'None'}")
                logger.error(f"SERVICE: Payload type: {type(work_item_input.payload).__name__ if work_item_input and work_item_input.payload else 'None'}")
            except Exception as context_error:
                logger.error(f"SERVICE: Could not log error context: {context_error}")
            
            return None
    
    def generate_bulk_release_notes(self, input_json: Any) -> str:
        """
        Generate bulk release notes from multiple work items.
        
        Args:
            input_json: JSON data containing multiple work items
            
        Returns:
            Formatted release notes
        """
        try:
            logger.info("Generating bulk release notes")
            
            final_output = self.openai_service.generate_completion(
                prompt=PromptTemplates.RELEASE_NOTES_FORMATTER.format(json.dumps(input_json)),
                parameters=LLMParameters(max_tokens=2000, temperature=0.1)
            )
              # Clean up markdown formatting
            release_notes = final_output.replace("```markdown", "").replace("```", "").strip().strip("\n")
            
            logger.info("Bulk release notes generation completed")
            return release_notes
            
        except Exception as e:
            logger.error(f"Error generating bulk release notes: {e}")
            return "Error generating release notes"
    
    def _analyze_work_item(
        self, payload: Dict[str, Any], max_tokens: int, temperature: float
    ) -> Optional[WorkItemDetails]:
        """Analyze work item and extract structured details."""
        try:
            enhanced_logger.log_function_entry("_analyze_work_item", 
                payload_type=type(payload).__name__, 
                max_tokens=max_tokens, 
                temperature=temperature)
            enhanced_logger.log_data_quality("payload", payload, dict)
            
            enhanced_logger.log_api_call("OpenAI", "analyze_work_item", 
                max_tokens=max_tokens, 
                temperature=temperature)
            
            response = self.openai_service.generate_completion(
                prompt=PromptTemplates.INPUT_GENERATOR.format(payload),
                parameters=LLMParameters(max_tokens=max_tokens, temperature=temperature)
            )
            enhanced_logger.log_data_quality("openai_response", response, str)
            
            result = self.parsing_service.parse_work_item_details(response)
            enhanced_logger.log_data_quality("parsed_work_item", result, WorkItemDetails)
            
            if result:
                enhanced_logger.log_business_metric("work_item_analysis_success", 1)
                enhanced_logger.log_function_exit("_analyze_work_item", "Successfully parsed work item details")
            else:
                enhanced_logger.log_business_metric("work_item_analysis_failure", 1)
                logger.warning("Failed to parse work item details from OpenAI response")
            
            return result
            
        except Exception as e:
            enhanced_logger.log_business_metric("work_item_analysis_error", 1)
            logger.error(f"Error analyzing work item: {e}")
            return None
    
    def _generate_queries(
        self, work_item_details: WorkItemDetails, max_tokens: int, temperature: float
    ) -> list[str]:
        """Generate search queries from work item details."""
        try:
            enhanced_logger.log_function_entry("_generate_queries", 
                max_tokens=max_tokens, 
                temperature=temperature)
            
            work_item_input = json.dumps(work_item_details.to_dict())
            enhanced_logger.log_data_quality("work_item_json", work_item_input, str)
            
            enhanced_logger.log_api_call("OpenAI", "generate_queries", 
                max_tokens=max_tokens, 
                temperature=temperature)
            
            response = self.openai_service.generate_completion(
                prompt=PromptTemplates.QUERY_GENERATOR.format(work_item_input),
                parameters=LLMParameters(max_tokens=max_tokens, temperature=temperature)
            )
            
            enhanced_logger.log_data_quality("query_response", response, str)
            
            queries = self.parsing_service.parse_queries(response)
            enhanced_logger.log_data_quality("parsed_queries", queries, list)
            
            logger.info(f"Generated {len(queries)} queries")
            enhanced_logger.log_business_metric("queries_generated", len(queries))
            enhanced_logger.log_function_exit("_generate_queries", f"Generated {len(queries)} queries")
            
            return queries
            
        except Exception as e:
            enhanced_logger.log_business_metric("query_generation_error", 1)
            logger.error(f"Error generating queries: {e}")
            return []
    
    def _generate_user_impact(
        self, search_context: str, short_description: str, max_tokens: int, temperature: float
    ) -> str:
        """Generate user impact summary."""
        try:
            response = self.openai_service.generate_completion(
                prompt=PromptTemplates.CONTEXT_SUMMARIZER.format(search_context, short_description),
                parameters=LLMParameters(max_tokens=max_tokens, temperature=temperature)
            )
            
            logger.info("Generated user impact summary")
            return response
            
        except Exception as e:
            logger.error(f"Error generating user impact: {e}")
            return "Unable to determine user impact"
    
    def _generate_final_release_notes(
        self,
        work_item_details: WorkItemDetails,
        search_context: str,
        user_impact: str,
        max_tokens: int,
        temperature: float,
        use_internal_doc: bool,
        remove_internal_keywords: bool,
        semantic_config: str
    ) -> Dict[str, str]:
        """Generate the final release notes."""
        release_notes = {}
        
        try:
            # Generate primary release note
            if use_internal_doc:
                rag_note = self.openai_service.generate_completion(
                    prompt=PromptTemplates.RELEASE_NOTE_GENERATOR_V2,
                    additional_info=user_impact,
                    parameters=LLMParameters(
                        max_tokens=max_tokens,
                        temperature=temperature,
                        use_search=True
                    ),
                    semantic_config=semantic_config
                )
                release_notes["RAG_ReleaseNote"] = rag_note
            
            # Generate standard release note
            standard_note = self.openai_service.generate_completion(
                prompt=PromptTemplates.RELEASE_NOTE_GENERATOR.format(
                    work_item_details.to_dict(), search_context
                ),
                parameters=LLMParameters(max_tokens=max_tokens, temperature=temperature)
            )
            
            # Handle keyword removal if requested
            if remove_internal_keywords:
                release_notes["ReleaseNote_withoutKeywords"] = self._remove_internal_keywords(
                    standard_note, max_tokens, semantic_config
                )
            else:
                release_notes["ReleaseNote_withoutKeywords"] = standard_note
            
            release_notes["ReleaseNote"] = standard_note
            
            logger.info("Generated final release notes")
            return release_notes
            
        except Exception as e:
            logger.error(f"Error generating final release notes: {e}")
            return {"ReleaseNote": "Error generating release note"}
    
    def _remove_internal_keywords(
        self, release_note: str, max_tokens: int, semantic_config: str
    ) -> str:
        """Remove internal keywords from release note."""
        try:
            # Extract keywords
            keyword_response = self.openai_service.generate_completion(
                prompt=PromptTemplates.KEYWORD_EXTRACTOR.format(release_note),
                parameters=LLMParameters(max_tokens=400, temperature=0)
            )
            
            keywords = self.parsing_service.parse_keywords(keyword_response)
            if not keywords:
                return release_note
            
            # Find replacements for keywords
            replacements = {}
            for keyword in keywords:
                # Try product documentation first
                prod_doc_response = self.openai_service.generate_completion(
                    prompt=PromptTemplates.PRODUCT_DOC_SEARCH,
                    additional_info=keyword,
                    parameters=LLMParameters(max_tokens=400, temperature=0, use_search=True),
                    semantic_config=semantic_config
                )
                
                if "requested information is not" not in prod_doc_response:
                    logger.debug(f"Found documentation for keyword: {keyword}")
                    continue
                
                # Try internal documentation
                internal_doc_response = self.openai_service.generate_completion(
                    prompt=PromptTemplates.KEYWORD_DICTIONARY,
                    additional_info=keyword,
                    parameters=LLMParameters(
                        max_tokens=400,
                        temperature=0,
                        use_search=True,
                        use_internal_doc=True
                    ),
                    semantic_config=semantic_config
                )
                
                replacements[keyword] = internal_doc_response
            
            # Apply replacements if any found
            if replacements:
                final_note = self.openai_service.generate_completion(
                    prompt=PromptTemplates.KEYWORD_REPLACER.format(
                        json.dumps(replacements), release_note
                    ),
                    parameters=LLMParameters(max_tokens=800, temperature=0)
                )
                return final_note
            
            return release_note
            
        except Exception as e:
            logger.error(f"Error removing internal keywords: {e}")
            return release_note
