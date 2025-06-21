"""
Unit tests for the refactored release notes generator.
Run with: python -m pytest tests/ -v
"""

import pytest
import json
import sys
import os

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.data_models import WorkItemInput, WorkItemDetails, LLMParameters
from services.parsing_service import ParsingService
from config.settings import AppConfig
from utils.validation import InputValidator
from unittest.mock import Mock, patch


class TestDataModels:
    """Test data models and their methods."""
    def test_work_item_input_creation(self):
        """Test WorkItemInput model creation."""
        work_item = WorkItemInput(
            single=True,
            payload={"test": "data"},
            documentation="test-config"
        )        
        assert work_item.single is True
        assert work_item.payload == {"test": "data"}
        assert work_item.documentation == "test-config"
    
    def test_work_item_details_to_dict(self):
        """Test WorkItemDetails to_dict method."""
        details = WorkItemDetails(
            short_description="Test description",
            customer_impact="Test impact", 
            activity_type="enhancement",
            keywords=["test", "keyword"]
        )
        
        result = details.to_dict()
        
        expected = {
            "ShortDescription": "Test description",
            "CustomerImpact": "Test impact",
            "ActivityType": "enhancement", 
            "Keywords": ["test", "keyword"]
        }
        
        assert result == expected
    
    def test_llm_parameters_defaults(self):
        """Test LLMParameters default values."""
        params = LLMParameters()
        
        assert params.max_tokens == 800
        assert params.temperature == 0.2
        assert params.use_search is False
        assert params.use_internal_doc is False
        assert params.strictness == 3


class TestParsingService:
    """Test parsing service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parsing_service = ParsingService()
    
    def test_validate_json_input_valid(self):
        """Test JSON validation with valid input."""
        valid_json = '{"test": "value", "number": 123}'
        
        is_valid, error = self.parsing_service.validate_json_input(valid_json)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_json_input_invalid(self):
        """Test JSON validation with invalid input."""
        invalid_json = '{"test": "value", "number": }'
        
        is_valid, error = self.parsing_service.validate_json_input(invalid_json)
        assert is_valid is False
        assert error is not None
        assert "value" in str(error).lower()
    
    def test_parse_work_item_details_valid(self):
        """Test parsing valid work item details."""
        response = '''
        {
            "ShortDescription": "Fix login bug",
            "CustomerImpact": "Users can login successfully",
            "ActivityType": "bug_fix",
            "Keywords": ["login", "authentication"]
        }
        '''
        
        result = self.parsing_service.parse_work_item_details(response)
        
        assert result is not None
        assert result.short_description == "Fix login bug"
        assert result.customer_impact == "Users can login successfully"
        assert result.activity_type == "bug_fix"
        assert result.keywords == ["login", "authentication"]
    
    def test_parse_work_item_details_invalid(self):
        """Test parsing invalid work item details."""
        response = "This is not JSON"
        
        result = self.parsing_service.parse_work_item_details(response)
        
        assert result is None
    
    def test_parse_queries_valid(self):
        """Test parsing valid queries."""
        response = '''
        {
            "queries": ["What is SSO?", "How does authentication work?", "Define login flow"]
        }
        '''
        
        result = self.parsing_service.parse_queries(response)
        
        assert len(result) == 3
        assert "What is SSO?" in result
        assert "How does authentication work?" in result
        assert "Define login flow" in result
    
    def test_parse_queries_invalid(self):
        """Test parsing invalid queries."""
        response = "Not a valid JSON response"
        
        result = self.parsing_service.parse_queries(response)
        
        assert result == []
    
    def test_keywords_to_string(self):
        """Test keywords to string conversion."""
        keywords = ["authentication", "sso", "login"]
        
        result = self.parsing_service.keywords_to_string(keywords)
        
        assert result == "authentication,sso,login"


class TestAppConfig:
    """Test application configuration."""
    
    def test_config_initialization(self):
        """Test config initialization with defaults."""
        config = AppConfig()
        
        assert "openai.azure.com" in config.openai_endpoint
        assert config.deployment_name is not None
        assert config.default_semantic_config is not None
        assert config.api_version == "2024-05-01-preview"
    
    def test_get_search_index(self):
        """Test search index extraction."""
        config = AppConfig()
        semantic_config = "my-search-index-semantic-configuration"
        
        result = config.get_search_index(semantic_config)
        
        assert result == "my-search-index"
    
    def test_get_semantic_config_with_input(self):
        """Test semantic config with provided input."""
        config = AppConfig()
        provided_config = "custom-config"
        
        result = config.get_semantic_config(provided_config)
        
        assert result == "custom-config"
    
    def test_get_semantic_config_default(self):
        """Test semantic config with default."""
        config = AppConfig()
        
        result = config.get_semantic_config(None)
        
        assert result == config.default_semantic_config


class TestInputValidator:
    """Test input validation functionality."""
    
    def test_validate_function_name_valid(self):
        """Test valid function name validation."""
        valid_names = ["orchestrator", "release_note_orchestrator"]
        
        for name in valid_names:
            result = InputValidator.validate_function_name(name)
            assert result is True
    
    def test_validate_function_name_invalid(self):
        """Test invalid function name validation."""
        invalid_names = ["invalid_function", "", None, "malicious_function"]
        
        for name in invalid_names:
            result = InputValidator.validate_function_name(name)
            assert result is False


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @patch('services.openai_service.OpenAIService')
    def test_complete_workflow_mock(self, mock_openai):
        """Test complete workflow with mocked OpenAI service."""
        # Mock OpenAI responses
        mock_openai.return_value.generate_completion.side_effect = [
            # Work item analysis response
            '''{"ShortDescription": "Fix login timeout", "CustomerImpact": "Users can login", "ActivityType": "bug_fix", "Keywords": ["login", "timeout"]}''',
            # Query generation response  
            '''{"queries": ["What is login timeout?", "How does authentication work?"]}''',
            # User impact response
            "Users will experience faster login times",
            # Final release note response
            "Fixed login timeout issue for improved user experience"
        ]
        
        # This would test the complete workflow
        # Implementation would require full service mocking
        pass


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
