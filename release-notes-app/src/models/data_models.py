"""Data models for the release notes generator."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class ActivityType(Enum):
    """Enumeration of work item activity types."""
    ENHANCEMENT = "enhancement"
    NEW_FEATURE = "new_feature"
    BUG_FIX = "bug_fix"
    REGRESSION = "regression"


@dataclass
class WorkItemInput:
    """Input model for work item processing."""
    single: bool
    payload: Dict[str, Any]
    documentation: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert to JSON string for serialization."""
        import json
        return json.dumps({
            "single": self.single,
            "payload": self.payload,
            "documentation": self.documentation
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "single": self.single,
            "payload": self.payload,
            "documentation": self.documentation
        }
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WorkItemInput':
        """Create WorkItemInput from JSON string."""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkItemInput':
        """Create WorkItemInput from dictionary."""
        return cls(
            single=data.get("single", False),
            payload=data.get("payload", {}),
            documentation=data.get("documentation")
        )


@dataclass
class WorkItemDetails:
    """Structured representation of work item analysis."""
    short_description: str
    customer_impact: str
    activity_type: str
    keywords: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ShortDescription": self.short_description,
            "CustomerImpact": self.customer_impact,
            "ActivityType": self.activity_type,
            "Keywords": self.keywords
        }


@dataclass
class SearchResult:
    """Result from RAG search operation."""
    query: str
    content: str
    additional_info: Optional[Dict[str, Any]] = None


@dataclass
class ReleaseNoteResult:
    """Complete result of release note generation."""
    work_item_details: WorkItemDetails
    queries: List[str]
    search_context: str
    user_impact: str
    release_notes: Dict[str, str]


@dataclass
class LLMParameters:
    """Parameters for LLM inference."""
    max_tokens: int = 800
    temperature: float = 0.2
    use_search: bool = False
    use_internal_doc: bool = False
    strictness: int = 3
