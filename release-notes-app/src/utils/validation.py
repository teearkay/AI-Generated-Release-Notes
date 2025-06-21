"""Input validation utilities."""

import json
import logging
from typing import Tuple, Optional, Dict, Any
import azure.functions as func

from models.data_models import WorkItemInput
from services.parsing_service import ParsingService

logger = logging.getLogger(__name__)


class InputValidator:
    """Utility class for validating and processing input data."""
    
    @staticmethod
    def validate_and_parse_request(req: func.HttpRequest) -> Tuple[bool, any]:
        """
        Validate and parse HTTP request for work item processing.
          Args:
            req: Azure Functions HTTP request
            
        Returns:
            Tuple of (success, result) where result is either WorkItemInput or HttpResponse
        """
        try:
            logger.info("VALIDATION: Parsing and validating HTTP request")
            
            # Get JSON parameters with enhanced logging
            logger.info("VALIDATION: Parsing request JSON")
            params = req.get_json()
            if not params:
                logger.warning("VALIDATION: Request body does not contain valid JSON")
                return False, func.HttpResponse(
                    status_code=400,
                    body="Request body must contain valid JSON"
                )
            
            logger.info(f"VALIDATION: Received parameters: {list(params.keys())}")
            
            # Extract and validate required parameters
            logger.info("VALIDATION: Checking required parameters")
            if "single" not in params:
                logger.warning("VALIDATION: Missing required parameter: 'single'")
                return False, func.HttpResponse(
                    status_code=400,
                    body="Missing required parameter: 'single'"
                )
            
            if "payload" not in params:
                logger.warning("VALIDATION: Missing required parameter: 'payload'")
                return False, func.HttpResponse(
                    status_code=400,
                    body="Missing required parameter: 'payload'"
                )
            
            # Extract values with type validation
            is_single = params["single"]
            payload_json = params["payload"]
            
            logger.info(f"VALIDATION: Single mode: {is_single}")
            logger.info(f"VALIDATION: Payload type: {type(payload_json).__name__}")
            
            # Validate single parameter type
            if not isinstance(is_single, bool):
                logger.warning(f"VALIDATION: 'single' parameter must be boolean, got {type(is_single).__name__}")
                return False, func.HttpResponse(
                    status_code=400,
                    body=f"Parameter 'single' must be boolean, got {type(is_single).__name__}"
                )
            
            # Validate payload
            if payload_json is None:
                logger.warning("VALIDATION: Payload cannot be null")
                return False, func.HttpResponse(
                    status_code=400,
                    body="Parameter 'payload' cannot be null"
                )
            documentation_config = params.get("documentation", None)
            
            # Validate payload JSON
            if isinstance(payload_json, str):
                is_valid, error = ParsingService.validate_json_input(payload_json)
                if not is_valid:
                    return False, func.HttpResponse(
                        status_code=400,
                        body=f"Invalid 'payload' parameter. Expecting valid JSON. Exception: {error}"
                    )
                payload_data = json.loads(payload_json)
            else:
                payload_data = payload_json
              # Create WorkItemInput object
            work_item_input = WorkItemInput(
                single=is_single,
                payload=payload_data,
                documentation=documentation_config
            )
            
            return True, work_item_input
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return False, func.HttpResponse(
                status_code=400,
                body=f"Invalid JSON in request body: {e}"
            )
        except Exception as e:
            logger.error(f"Error validating request: {e}")
            return False, func.HttpResponse(
                status_code=500,
                body="Internal error processing request"
            )
    
    @staticmethod
    def validate_function_name(function_name: Optional[str]) -> bool:
        """
        Validate function name parameter.
        
        Args:
            function_name: Function name from route parameters
            
        Returns:
            True if valid, False otherwise
        """
        if not function_name:
            return False
        
        # Add any specific validation logic for function names here
        allowed_functions = ["orchestrator", "release_note_orchestrator"]
        return function_name in allowed_functions
