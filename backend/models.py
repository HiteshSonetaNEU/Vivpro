"""
Pydantic models for request/response validation.
Production-ready with comprehensive validation and documentation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ============================================================================
# Request Models
# ============================================================================

class SearchRequest(BaseModel):
    """Request model for intelligent search endpoint."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language search query",
        example="Find Phase 2 breast cancer trials that are recruiting"
    )
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination (starts at 1)"
    )
    
    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of results per page (max 100)"
    )
    
    use_ai: bool = Field(
        default=True,
        description="Whether to use OpenAI for entity extraction (fallback to basic search if False)"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate and sanitize query string."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        # Strip excess whitespace
        return ' '.join(v.split())
    
    class Config:
        populate_by_name = True


# ============================================================================
# Entity Extraction Models
# ============================================================================

class ExtractedEntities(BaseModel):
    """Entities extracted from natural language query by OpenAI."""
    
    phase: Optional[str] = Field(
        None,
        description="Clinical trial phase (PHASE1, PHASE2, PHASE3, PHASE4, NA)",
        example="PHASE2"
    )
    
    conditions: Optional[List[str]] = Field(
        None,
        description="Medical conditions or diseases",
        example=["breast cancer", "metastatic"]
    )
    
    interventions: Optional[List[str]] = Field(
        None,
        description="Treatments, drugs, or interventions",
        example=["chemotherapy", "pembrolizumab"]
    )
    
    status: Optional[str] = Field(
        None,
        description="Recruitment status (RECRUITING, COMPLETED, TERMINATED, etc.)",
        example="RECRUITING"
    )
    
    study_type: Optional[str] = Field(
        None,
        description="Type of study (INTERVENTIONAL, OBSERVATIONAL)",
        example="INTERVENTIONAL"
    )
    
    sponsors: Optional[List[str]] = Field(
        None,
        description="Sponsor or organization names (e.g., pharmaceutical companies, universities)",
        example=["Pfizer", "Mayo Clinic"]
    )
    
    locations: Optional[List[str]] = Field(
        None,
        description="Geographic locations (cities, states, countries)",
        example=["Boston", "New York", "California"]
    )
    
    keywords: Optional[List[str]] = Field(
        None,
        description="Additional keywords or concepts",
        example=["immunotherapy", "combination therapy"]
    )
    
    original_query: str = Field(
        ...,
        description="Original user query"
    )
    
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score of extraction (0-1)"
    )
    
    @validator('phase')
    def validate_phase(cls, v):
        """Validate phase value."""
        if v is None:
            return v
        valid_phases = ['PHASE1', 'PHASE2', 'PHASE3', 'PHASE4', 'PHASE1/PHASE2', 'PHASE2/PHASE3', 'NA']
        if v not in valid_phases:
            # Try to normalize
            v_upper = v.upper().replace(' ', '').replace('-', '')
            if v_upper in valid_phases:
                return v_upper
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status value."""
        if v is None:
            return v
        valid_statuses = [
            'RECRUITING', 'NOT_YET_RECRUITING', 'ACTIVE_NOT_RECRUITING',
            'COMPLETED', 'TERMINATED', 'SUSPENDED', 'WITHDRAWN', 'UNKNOWN'
        ]
        if v not in valid_statuses:
            v_upper = v.upper().replace(' ', '_')
            if v_upper in valid_statuses:
                return v_upper
        return v


# ============================================================================
# Response Models
# ============================================================================

class TrialSummary(BaseModel):
    """Summary of a clinical trial for search results."""
    
    nct_id: str = Field(..., description="ClinicalTrials.gov NCT ID")
    brief_title: str = Field(..., description="Brief title of the trial")
    official_title: Optional[str] = Field(None, description="Official title")
    phase: Optional[str] = Field(None, description="Study phase")
    overall_status: Optional[str] = Field(None, description="Overall status")
    study_type: Optional[str] = Field(None, description="Study type")
    
    brief_summaries_description: Optional[str] = Field(
        None,
        description="Brief summary"
    )
    
    conditions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Medical conditions"
    )
    
    interventions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Interventions"
    )
    
    enrollment: Optional[int] = Field(None, description="Target enrollment")
    start_date: Optional[str] = Field(None, description="Start date")
    completion_date: Optional[str] = Field(None, description="Completion date")
    
    score: Optional[float] = Field(
        None,
        description="Elasticsearch relevance score"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "nct_id": "NCT06890351",
                "brief_title": "Study of Drug X in Breast Cancer",
                "phase": "PHASE2",
                "overall_status": "RECRUITING",
                "score": 8.5
            }
        }


class TrialDetail(BaseModel):
    """Complete trial details."""
    
    # Allow any fields for full trial data
    class Config:
        extra = "allow"


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    
    query: str = Field(..., description="Original search query")
    
    extracted_entities: Optional[ExtractedEntities] = Field(
        None,
        description="Entities extracted from query (if AI was used)"
    )
    
    total_results: int = Field(
        ...,
        ge=0,
        description="Total number of matching trials"
    )
    
    page: int = Field(..., ge=1, description="Current page number")
    
    page_size: int = Field(..., ge=1, le=100, description="Number of results per page")
    
    total_pages: int = Field(..., ge=0, description="Total number of pages available")
    
    results: List[TrialSummary] = Field(
        ...,
        description="List of matching trials"
    )
    
    took_ms: int = Field(
        ...,
        ge=0,
        description="Time taken for search in milliseconds"
    )
    
    used_ai: bool = Field(
        ...,
        description="Whether AI entity extraction was used"
    )
    
    search_type: str = Field(
        ...,
        description="Type of search performed (intelligent, basic, similar)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Phase 2 breast cancer trials",
                "extracted_entities": {
                    "phase": "PHASE2",
                    "conditions": ["breast cancer"],
                    "original_query": "Phase 2 breast cancer trials"
                },
                "total_results": 45,
                "page": 1,
                "page_size": 10,
                "total_pages": 5,
                "results": [],
                "took_ms": 250,
                "used_ai": True,
                "search_type": "intelligent"
            }
        }


class TrialDetailResponse(BaseModel):
    """Response model for trial detail endpoint."""
    
    nct_id: str = Field(..., description="NCT ID")
    found: bool = Field(..., description="Whether trial was found")
    trial: Optional[TrialDetail] = Field(None, description="Complete trial data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nct_id": "NCT06890351",
                "found": True,
                "trial": {}
            }
        }


class FiltersResponse(BaseModel):
    """Response model for available filters endpoint."""
    
    phases: List[Dict[str, Any]] = Field(
        ...,
        description="Available phases with counts"
    )
    
    statuses: List[Dict[str, Any]] = Field(
        ...,
        description="Available statuses with counts"
    )
    
    study_types: List[Dict[str, Any]] = Field(
        ...,
        description="Available study types with counts"
    )
    
    top_conditions: List[Dict[str, Any]] = Field(
        ...,
        description="Top conditions with counts"
    )
    
    total_trials: int = Field(
        ...,
        description="Total number of trials in index"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "phases": [
                    {"key": "PHASE2", "doc_count": 308}
                ],
                "statuses": [
                    {"key": "COMPLETED", "doc_count": 857}
                ],
                "study_types": [
                    {"key": "INTERVENTIONAL", "doc_count": 792}
                ],
                "top_conditions": [
                    {"name": "Cancer", "doc_count": 214}
                ],
                "total_trials": 1000
            }
        }


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid query",
                "detail": "Query must be at least 1 character",
                "timestamp": "2026-02-07T12:00:00Z"
            }
        }
