"""Refactored Azure Functions app for release notes generation.

This module provides a clean, modular implementation of the release notes generator
using Azure Durable Functions with proper separation of concerns and error handling.
"""

import logging
import json
import azure.functions as func
import azure.durable_functions as df
from typing import Any

from models.data_models import WorkItemInput
from services.release_note_service import ReleaseNoteGenerator
from utils.validation import InputValidator
from utils.logging_config import setup_logging
from utils.azure_auth import setup_azure_auth_for_local_dev
from utils.enhanced_logging import create_enhanced_logger, log_exceptions

# Initialize logging
setup_logging(level="INFO")
logger = logging.getLogger("release_notes_app")
enhanced_logger = create_enhanced_logger("release_notes_app")

# Set up Azure authentication for local development
try:
    setup_azure_auth_for_local_dev()
except Exception as e:
    logger.warning(f"Azure authentication setup failed: {e}")
    logger.info("Application will continue but Azure services may not work locally")

# Initialize the Durable Functions app
app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="orchestrators/{functionName}")
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client) -> func.HttpResponse:
    """
    HTTP-triggered function that starts the Durable Functions orchestration.
    
    Args:
        req: HTTP request containing work item data
        client: Durable Functions client
        
    Returns:
        HTTP response with orchestration status
    """
    import time
    start_time = time.time()
    
    try:
        # Log request details for debugging
        logger.info(f"HTTP START: Received request - Method: {req.method}, URL: {req.url}")
        logger.debug(f"HTTP START: Headers: {dict(req.headers)}")
        
        # Get function name from route parameters
        function_name = req.route_params.get('functionName')
        logger.info(f"HTTP START: Function name requested: {function_name}")
        
        # Validate function name with detailed logging
        if not InputValidator.validate_function_name(function_name):
            logger.warning(f"HTTP START: Invalid function name provided: '{function_name}'. Supported functions: release_note_orchestrator")
            return func.HttpResponse(
                status_code=400,
                body=f"Invalid function name: {function_name}. Supported functions: release_note_orchestrator"
            )
        
        # Log payload size for monitoring
        try:
            body = req.get_body()
            logger.info(f"HTTP START: Request body size: {len(body)} bytes")
        except Exception as body_error:
            logger.warning(f"HTTP START: Could not get request body size: {body_error}")
        
        # Validate and parse request with enhanced logging
        logger.info("HTTP START: Starting request validation")
        is_valid, result = InputValidator.validate_and_parse_request(req)
        if not is_valid:
            logger.warning(f"HTTP START: Request validation failed for function {function_name}")
            logger.debug(f"HTTP START: Validation error details: {result.get_body() if hasattr(result, 'get_body') else 'No error details'}")
            return result  # This is already an HttpResponse with error details
        
        work_item_input: WorkItemInput = result
        logger.info(f"HTTP START: Request validated successfully - Single: {work_item_input.single}, Documentation: {work_item_input.documentation}")
        
        # Start orchestration with performance tracking
        orchestration_start = time.time()
        instance_id = await client.start_new(function_name, None, work_item_input)
        orchestration_time = time.time() - orchestration_start
        
        logger.info(f"HTTP START: Successfully started orchestration")
        logger.info(f"HTTP START: Instance ID: {instance_id}")
        logger.info(f"HTTP START: Function: {function_name}")
        logger.info(f"HTTP START: Orchestration start time: {orchestration_time:.3f}s")
        
        # Create status response
        response = client.create_check_status_response(req, instance_id)
        
        # Log total processing time
        total_time = time.time() - start_time
        logger.info(f"HTTP START: Total request processing time: {total_time:.3f}s")
        logger.info(f"HTTP START: Request completed successfully for instance {instance_id}")
        
        return response
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"HTTP START: Critical error after {total_time:.3f}s - {type(e).__name__}: {str(e)}")
        logger.error(f"HTTP START: Function name: {function_name if 'function_name' in locals() else 'Unknown'}")
        
        # Log additional context for debugging
        try:
            logger.debug(f"HTTP START: Request method: {req.method}")
            logger.debug(f"HTTP START: Request URL: {req.url}")
        except:
            logger.debug("HTTP START: Could not log request details")
        
        return func.HttpResponse(
            status_code=500,
            body=f"Internal server error: {str(e)}"
        )


@app.orchestration_trigger(context_name="context")
def release_note_orchestrator(context) -> Any:
    """
    Orchestrator function that coordinates the release note generation process.
    
    Args:
        context: Durable Functions orchestration context
        
    Returns:
        Generated release notes
    """
    import time
    
    # Get orchestration details for logging
    instance_id = context.instance_id
    is_replaying = context.is_replaying
    current_utc_datetime = context.current_utc_datetime
    
    if not is_replaying:
        logger.info(f"ORCHESTRATOR: Starting orchestration for instance {instance_id}")
        logger.info(f"ORCHESTRATOR: Start time: {current_utc_datetime}")
    
    try:
        # Get input from context with enhanced logging
        input_data = context.get_input()
        if not is_replaying:
            logger.info(f"ORCHESTRATOR: Input data type: {type(input_data).__name__}")
            logger.debug(f"ORCHESTRATOR: Input data keys: {list(input_data.keys()) if isinstance(input_data, dict) else 'Not a dictionary'}")
        
        # Convert dictionary to WorkItemInput object
        if isinstance(input_data, dict):
            if not is_replaying:
                logger.info("ORCHESTRATOR: Converting dictionary input to WorkItemInput object")
            work_item_input = WorkItemInput.from_dict(input_data)
        else:
            if not is_replaying:
                logger.info("ORCHESTRATOR: Input is already a WorkItemInput object")
            work_item_input = input_data
        
        # Log work item details
        if not is_replaying:
            logger.info(f"ORCHESTRATOR: Processing work item - Single: {work_item_input.single}")
            logger.info(f"ORCHESTRATOR: Documentation config: {work_item_input.documentation}")
            if hasattr(work_item_input.payload, '__len__'):
                logger.info(f"ORCHESTRATOR: Payload size: {len(work_item_input.payload)} items")
        
        # Call the activity function with performance tracking
        if not is_replaying:
            logger.info("ORCHESTRATOR: Calling generate_release_notes activity")
        
        activity_start_time = context.current_utc_datetime
        result = yield context.call_activity('generate_release_notes', work_item_input)
        
        if not is_replaying:
            # Calculate activity duration (approximate, since we can't get exact end time in orchestrator)
            logger.info("ORCHESTRATOR: Activity function completed successfully")
            logger.info(f"ORCHESTRATOR: Activity started at: {activity_start_time}")
            
            # Log result details
            if isinstance(result, str):
                logger.info(f"ORCHESTRATOR: Result type: string, length: {len(result)} characters")
                if "error" in result.lower() or "failed" in result.lower():
                    logger.warning(f"ORCHESTRATOR: Activity returned error-like result: {result[:200]}...")
                else:
                    logger.info("ORCHESTRATOR: Activity returned successful result")
            else:
                logger.info(f"ORCHESTRATOR: Result type: {type(result).__name__}")
            
            logger.info(f"ORCHESTRATOR: Orchestration completed successfully for instance {instance_id}")
        
        return result
        
    except Exception as e:
        if not is_replaying:
            logger.error(f"ORCHESTRATOR: Critical error in instance {instance_id}")
            logger.error(f"ORCHESTRATOR: Error type: {type(e).__name__}")
            logger.error(f"ORCHESTRATOR: Error message: {str(e)}")
            logger.error(f"ORCHESTRATOR: Is replaying: {is_replaying}")
            
            # Try to log input data for debugging
            try:
                input_data = context.get_input()
                logger.error(f"ORCHESTRATOR: Input data at error: {type(input_data).__name__}")
                if isinstance(input_data, dict):
                    logger.error(f"ORCHESTRATOR: Input keys: {list(input_data.keys())}")
            except Exception as input_error:
                logger.error(f"ORCHESTRATOR: Could not log input data: {input_error}")
        
        return {"error": f"Orchestration failed: {str(e)}", "instance_id": instance_id}


@app.activity_trigger(input_name="work_item_input")
def generate_release_notes(work_item_input: WorkItemInput) -> str:
    """
    Activity function that generates release notes from work item input.
    
    Args:
        work_item_input: Work item input data
        
    Returns:
        Generated release notes as string
    """
    import time
    start_time = time.time()
    
    try:
        logger.info("ACTIVITY: Starting release note generation activity")
        logger.info(f"ACTIVITY: Input type: {type(work_item_input).__name__}")
        logger.info(f"ACTIVITY: Single mode: {work_item_input.single}")
        logger.info(f"ACTIVITY: Documentation config: {work_item_input.documentation}")
        
        # Validate input data
        if not hasattr(work_item_input, 'payload') or work_item_input.payload is None:
            logger.error("ACTIVITY: Invalid input - payload is missing or None")
            return "Error: Invalid input data - payload is missing"
        
        # Log payload information
        if isinstance(work_item_input.payload, (list, dict)):
            payload_size = len(work_item_input.payload)
            logger.info(f"ACTIVITY: Payload size: {payload_size} items")
        else:
            logger.info(f"ACTIVITY: Payload type: {type(work_item_input.payload).__name__}")
        
        # Initialize the release note generator with timing
        init_start = time.time()
        generator = ReleaseNoteGenerator()
        init_time = time.time() - init_start
        logger.info(f"ACTIVITY: Generator initialized in {init_time:.3f}s")
        
        if work_item_input.single:
            logger.info("ACTIVITY: Processing single work item mode")
            
            # Generate release notes for a single work item with detailed parameters
            generation_start = time.time()
            result = generator.generate_release_notes(
                work_item_input=work_item_input,
                max_tokens=800,
                temperature=0.2,
                search_max_tokens=800,
                search_temperature=0,
                use_internal_doc=False,
                remove_internal_keywords=False
            )
            generation_time = time.time() - generation_start
            logger.info(f"ACTIVITY: Single release note generation completed in {generation_time:.3f}s")
            
            if result and result.release_notes:
                release_note = result.release_notes.get("ReleaseNote", "No release note generated")
                
                # Log success metrics
                note_length = len(release_note)
                logger.info(f"ACTIVITY: Successfully generated single release note")
                logger.info(f"ACTIVITY: Release note length: {note_length} characters")
                logger.info(f"ACTIVITY: Available note types: {list(result.release_notes.keys())}")
                
                # Log quality indicators
                if "error" in release_note.lower():
                    logger.warning("ACTIVITY: Release note contains error indicators")
                if note_length < 50:
                    logger.warning(f"ACTIVITY: Release note is unusually short: {note_length} characters")
                elif note_length > 2000:
                    logger.warning(f"ACTIVITY: Release note is unusually long: {note_length} characters")
                
                total_time = time.time() - start_time
                logger.info(f"ACTIVITY: Single mode completed successfully in {total_time:.3f}s")
                return release_note
            else:
                logger.error("ACTIVITY: Generator returned None or empty result")
                logger.error(f"ACTIVITY: Result object: {result}")
                return "Failed to generate release note - no result returned"
        else:
            logger.info("ACTIVITY: Processing bulk work items mode")
            
            # Generate bulk release notes for multiple work items
            bulk_start = time.time()
            release_notes = generator.generate_bulk_release_notes(work_item_input.payload)
            bulk_time = time.time() - bulk_start
            
            # Log bulk processing results
            notes_length = len(release_notes) if release_notes else 0
            logger.info(f"ACTIVITY: Bulk release notes generation completed in {bulk_time:.3f}s")
            logger.info(f"ACTIVITY: Bulk release notes length: {notes_length} characters")
            
            if notes_length > 0:
                logger.info("ACTIVITY: Successfully generated bulk release notes")
            else:
                logger.warning("ACTIVITY: Bulk generation returned empty result")
            
            total_time = time.time() - start_time
            logger.info(f"ACTIVITY: Bulk mode completed in {total_time:.3f}s")
            return release_notes
            
    except Exception as e:
        total_time = time.time() - start_time
        error_type = type(e).__name__
        logger.error(f"ACTIVITY: Critical error after {total_time:.3f}s")
        logger.error(f"ACTIVITY: Error type: {error_type}")
        logger.error(f"ACTIVITY: Error message: {str(e)}")
        
        # Log additional context for debugging
        try:
            logger.error(f"ACTIVITY: Work item input type: {type(work_item_input).__name__}")
            logger.error(f"ACTIVITY: Single mode: {getattr(work_item_input, 'single', 'Unknown')}")
            logger.error(f"ACTIVITY: Has payload: {hasattr(work_item_input, 'payload')}")
            if hasattr(work_item_input, 'payload') and work_item_input.payload:
                logger.error(f"ACTIVITY: Payload type: {type(work_item_input.payload).__name__}")
        except Exception as context_error:
            logger.error(f"ACTIVITY: Could not log error context: {context_error}")
        
        return f"Error generating release notes: {error_type} - {str(e)}"


# Legacy function name alias for backward compatibility
@app.activity_trigger(input_name="input_data")
def releasenotegenerator(input_data: tuple) -> str:
    """
    Legacy activity function for backward compatibility.
    
    Args:
        input_data: Tuple containing (is_single, payload, documentation_config)
        
    Returns:
        Generated release notes as string
    """
    try:
        logger.info("Using legacy release note generator function")
          # Convert legacy input format to new format
        is_single, payload, documentation_config = input_data
        
        work_item_input = WorkItemInput(
            single=is_single,
            payload=payload,
            documentation=documentation_config
        )
        
        # Use the new activity function
        return generate_release_notes(work_item_input)
        
    except Exception as e:
        logger.error(f"Error in legacy release note generator: {e}")
        return f"Error in legacy function: {str(e)}"


# Health check endpoint
@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint to verify the function app is running.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response indicating health status
    """
    try:
        return func.HttpResponse(
            body='{"status": "healthy", "service": "release-notes-generator"}',
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return func.HttpResponse(
            body=f'{{"status": "unhealthy", "error": "{str(e)}"}}',
            status_code=500,
            mimetype="application/json"
        )


# HTML cleaning endpoint
@app.route(route="clean-html", methods=["POST"])
def clean_html(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered function that cleans HTML content using BeautifulSoup.
    
    Args:
        req: HTTP request containing HTML content to clean
        
    Returns:
        HTTP response with cleaned text
    """
    import time
    from bs4 import BeautifulSoup
    
    start_time = time.time()
    
    try:
        logger.info("HTML_CLEANER: Starting HTML cleaning operation")
        
        # Validate request method
        if req.method != "POST":
            logger.warning(f"HTML_CLEANER: Invalid method {req.method}, expected POST")
            return func.HttpResponse(
                status_code=405,
                body='{"error": "Method not allowed. Use POST."}',
                mimetype="application/json"
            )
        
        # Get request body
        try:
            body = req.get_body()
            if not body:
                logger.warning("HTML_CLEANER: Empty request body")
                return func.HttpResponse(
                    status_code=400,
                    body='{"error": "Request body is empty"}',
                    mimetype="application/json"
                )
            
            logger.info(f"HTML_CLEANER: Received content size: {len(body)} bytes")
        except Exception as e:
            logger.error(f"HTML_CLEANER: Failed to get request body: {e}")
            return func.HttpResponse(
                status_code=400,
                body=f'{{"error": "Invalid request body: {str(e)}"}}',
                mimetype="application/json"
            )        # Parse request content
        try:
            content_type = req.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                data = json.loads(body.decode('utf-8'))
                
                if isinstance(data, dict):
                    # Check if html field is provided
                    if 'html' not in data:
                        logger.warning("HTML_CLEANER: JSON format should include 'html' field")
                        return func.HttpResponse(
                            status_code=400,
                            body='{"error": "JSON should contain \'html\' field"}',
                            mimetype="application/json"
                        )
                    
                    # Required parameter
                    html_content = data['html']
                    
                    # Optional parameters with defaults
                    preserve_structure = data.get('preserve_structure', False)
                    remove_attributes = data.get('remove_attributes', True)
                    
                    logger.info(f"HTML_CLEANER: Using preserve_structure={preserve_structure}, remove_attributes={remove_attributes}")
                else:
                    logger.warning("HTML_CLEANER: JSON payload should be an object")
                    return func.HttpResponse(
                        status_code=400,
                        body='{"error": "JSON payload should be an object"}',
                        mimetype="application/json"
                    )
            else:
                # Treat as plain HTML text
                html_content = body.decode('utf-8')
                preserve_structure = False
                remove_attributes = True
                
            logger.info(f"HTML_CLEANER: HTML content length: {len(html_content)} characters")
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"HTML_CLEANER: Failed to parse request content: {e}")
            return func.HttpResponse(
                status_code=400,
                body=f'{{"error": "Invalid content format: {str(e)}"}}',
                mimetype="application/json"
            )
        
        # Clean HTML content using BeautifulSoup
        cleaning_start = time.time()
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
              # Remove comments
            from bs4 import Comment
            comments = soup.find_all(text=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            
            if preserve_structure:
                # Keep basic structure tags but clean content
                if remove_attributes:
                    # Remove all attributes from tags
                    for tag in soup.find_all():
                        tag.attrs = {}
                
                # Get text with some structure preserved
                cleaned_text = str(soup)
                logger.info("HTML_CLEANER: Preserved HTML structure")
            else:
                # Extract plain text only
                cleaned_text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in cleaned_text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                cleaned_text = ' '.join(chunk for chunk in chunks if chunk)
                
                logger.info("HTML_CLEANER: Extracted plain text only")
            
            cleaning_time = time.time() - cleaning_start
            logger.info(f"HTML_CLEANER: Cleaning completed in {cleaning_time:.3f}s")
            logger.info(f"HTML_CLEANER: Output length: {len(cleaned_text)} characters")
            
            # Prepare response
            response_data = {
                "cleaned_text": cleaned_text,
                "original_length": len(html_content),
                "cleaned_length": len(cleaned_text),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "preserve_structure": preserve_structure
            }
            
            total_time = time.time() - start_time
            logger.info(f"HTML_CLEANER: Operation completed successfully in {total_time:.3f}s")
            
            return func.HttpResponse(
                body=json.dumps(response_data, ensure_ascii=False, indent=2),
                status_code=200,
                mimetype="application/json; charset=utf-8"
            )
            
        except Exception as e:
            logger.error(f"HTML_CLEANER: BeautifulSoup processing failed: {e}")
            return func.HttpResponse(
                status_code=500,
                body=f'{{"error": "HTML cleaning failed: {str(e)}"}}',
                mimetype="application/json"
            )
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"HTML_CLEANER: Critical error after {total_time:.3f}s - {type(e).__name__}: {str(e)}")
        
        return func.HttpResponse(
            status_code=500,
            body=f'{{"error": "Internal server error: {str(e)}"}}',
            mimetype="application/json"
        )


# HTML cleaning endpoint with file upload support
@app.route(route="clean-html-file", methods=["POST"])
def clean_html_file(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered function that cleans HTML content from uploaded files.
    
    Args:
        req: HTTP request containing HTML file to clean
        
    Returns:
        HTTP response with cleaned text
    """
    import time
    from bs4 import BeautifulSoup
    
    start_time = time.time()
    
    try:
        logger.info("HTML_FILE_CLEANER: Starting HTML file cleaning operation")
        
        # Validate request method
        if req.method != "POST":
            logger.warning(f"HTML_FILE_CLEANER: Invalid method {req.method}, expected POST")
            return func.HttpResponse(
                status_code=405,
                body='{"error": "Method not allowed. Use POST."}',
                mimetype="application/json"
            )
        
        # Get file content from request
        try:
            # Check for multipart form data
            content_type = req.headers.get('content-type', '').lower()
            
            if 'multipart/form-data' in content_type:
                # Handle file upload (simplified - Azure Functions has limitations with multipart)
                body = req.get_body()
                if not body:
                    return func.HttpResponse(
                        status_code=400,
                        body='{"error": "No file content received"}',
                        mimetype="application/json"
                    )
                
                # For simplicity, treat the body as HTML content
                # In a production scenario, you'd need proper multipart parsing
                html_content = body.decode('utf-8')
                
            else:
                # Treat as raw HTML file content
                body = req.get_body()
                if not body:
                    return func.HttpResponse(
                        status_code=400,
                        body='{"error": "No file content received"}',
                        mimetype="application/json"
                    )
                
                html_content = body.decode('utf-8')
            
            logger.info(f"HTML_FILE_CLEANER: File content size: {len(html_content)} characters")
            
        except UnicodeDecodeError as e:
            logger.error(f"HTML_FILE_CLEANER: Failed to decode file content: {e}")
            return func.HttpResponse(
                status_code=400,
                body='{"error": "File content is not valid UTF-8 text"}',
                mimetype="application/json"
            )
        
        # Clean HTML content using BeautifulSoup
        cleaning_start = time.time()
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
              # Remove comments
            from bs4 import Comment
            comments = soup.find_all(text=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            
            # Remove common unwanted attributes but preserve basic structure
            unwanted_attrs = ['style', 'class', 'id', 'onclick', 'onload', 'onerror']
            for tag in soup.find_all():
                for attr in unwanted_attrs:
                    if attr in tag.attrs:
                        del tag.attrs[attr]
            
            # Get cleaned HTML
            cleaned_html = str(soup)
            
            # Also provide plain text version
            plain_text = soup.get_text()
            lines = (line.strip() for line in plain_text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned_plain_text = ' '.join(chunk for chunk in chunks if chunk)
            
            cleaning_time = time.time() - cleaning_start
            logger.info(f"HTML_FILE_CLEANER: Cleaning completed in {cleaning_time:.3f}s")
            logger.info(f"HTML_FILE_CLEANER: Cleaned HTML length: {len(cleaned_html)} characters")
            logger.info(f"HTML_FILE_CLEANER: Plain text length: {len(cleaned_plain_text)} characters")
            
            # Prepare response
            response_data = {
                "cleaned_html": cleaned_html,
                "plain_text": cleaned_plain_text,
                "original_length": len(html_content),
                "cleaned_html_length": len(cleaned_html),
                "plain_text_length": len(cleaned_plain_text),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
            
            total_time = time.time() - start_time
            logger.info(f"HTML_FILE_CLEANER: Operation completed successfully in {total_time:.3f}s")
            
            return func.HttpResponse(
                body=json.dumps(response_data, ensure_ascii=False, indent=2),
                status_code=200,
                mimetype="application/json; charset=utf-8"
            )
            
        except Exception as e:
            logger.error(f"HTML_FILE_CLEANER: BeautifulSoup processing failed: {e}")
            return func.HttpResponse(
                status_code=500,
                body=f'{{"error": "HTML cleaning failed: {str(e)}"}}',
                mimetype="application/json"
            )
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"HTML_FILE_CLEANER: Critical error after {total_time:.3f}s - {type(e).__name__}: {str(e)}")
        
        return func.HttpResponse(
            status_code=500,
            body=f'{{"error": "Internal server error: {str(e)}"}}',
            mimetype="application/json"
        )