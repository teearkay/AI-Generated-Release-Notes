"""Service for parsing JSON responses from LLM."""

import json
import re
import logging
from typing import List, Optional, Dict, Any

from models.data_models import WorkItemDetails

logger = logging.getLogger(__name__)


class ParsingService:
    """Service for parsing LLM responses into structured data."""
    
    @staticmethod
    def parse_work_item_details(response: str) -> Optional[WorkItemDetails]:
        """
        Parse work item details from LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Parsed WorkItemDetails or None if parsing fails
        """
        try:
            json_match = re.search(r"{.*?}", response, re.DOTALL)
            
            if not json_match:
                logger.error("No JSON found in work item details response")
                return None
            
            data = json.loads(json_match.group())
            
            work_item = WorkItemDetails(
                short_description=data.get("ShortDescription", ""),
                customer_impact=data.get("CustomerImpact", ""),
                activity_type=data.get("ActivityType", ""),
                keywords=data.get("Keywords", [])
            )
            
            logger.info(f"Parsed work item details: {work_item.short_description[:50]}...")
            return work_item
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse work item details: {e}")
            logger.debug(f"Response content: {response}")
            return None
    
    @staticmethod
    def parse_queries(response: str) -> List[str]:
        """
        Parse queries from LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            List of parsed queries
        """
        try:
            json_match = re.search(r"{.*?}", response, re.DOTALL)
            
            if not json_match:
                logger.error("No JSON found in queries response")
                return []
            
            data = json.loads(json_match.group())
            queries = data.get("queries", [])
            
            logger.info(f"Parsed {len(queries)} queries")
            return queries
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse queries: {e}")
            logger.debug(f"Response content: {response}")
            return []
    
    @staticmethod
    def parse_keywords(response: str) -> List[str]:
        """
        Parse keywords from LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            List of parsed keywords
        """
        try:
            json_match = re.search(r"{.*?}", response, re.DOTALL)
            
            if not json_match:
                logger.error("No JSON found in keywords response")
                return []
            
            data = json.loads(json_match.group())
            keywords = data.get("kwrds", [])
            
            logger.info(f"Parsed {len(keywords)} keywords")
            return keywords
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse keywords: {e}")
            logger.debug(f"Response content: {response}")
            return []
    
    @staticmethod
    def keywords_to_string(keywords: List[str]) -> str:
        """Convert keywords list to comma-separated string."""
        return ",".join(keywords)
    
    @staticmethod
    def validate_json_input(input_json: str) -> tuple[bool, Optional[str]]:
        """
        Validate JSON input string.
        
        Args:
            input_json: JSON string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            json.loads(input_json)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)
