"""
Search router with intelligent query processing endpoints.
Production-ready with comprehensive error handling and validation.
"""

import logging
import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from elasticsearch import NotFoundError, RequestError, ConnectionError as ESConnectionError

from models import (
    SearchRequest, SearchResponse, TrialSummary, 
    TrialDetailResponse, TrialDetail, FiltersResponse,
    ExtractedEntities, ErrorResponse
)
from openai_service import openai_service
from query_builder import query_builder

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["search"])

# Elasticsearch client will be injected via app state
def get_es_client():
    """Get Elasticsearch client from app state."""
    from main import es_client
    return es_client


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Intelligent search for clinical trials",
    description="""
    Search clinical trials using natural language queries.
    
    The endpoint uses AI (OpenAI GPT-4o-mini) to extract structured entities from your query,
    then constructs an optimized Elasticsearch query for relevant results.
    
    Features:
    - Natural language processing for entity extraction
    - Intelligent query construction with relevance scoring
    - Fallback to basic full-text search if AI extraction fails
    - Pagination support
    - Detailed search metadata in response
    
    Examples:
    - "Find Phase 2 breast cancer trials"
    - "Recruiting studies for diabetes with metformin"
    - "Completed COVID-19 vaccine trials"
    - "Phase 3 interventional trials for asthma"
    """
)
async def search_trials(request: SearchRequest) -> SearchResponse:
    """
    Intelligent search endpoint with AI-powered entity extraction.
    
    Query Processing Flow:
    1. Validate input
    2. Extract entities using OpenAI (if enabled)
    3. Build optimized Elasticsearch query
    4. Execute search
    5. Format and return results
    """
    start_time = time.time()
    es = get_es_client()
    
    try:
        # Calculate offset from page number
        from_offset = (request.page - 1) * request.page_size
        
        logger.info(f"Search request: query='{request.query}', page={request.page}, "
                   f"page_size={request.page_size}, offset={from_offset}, use_ai={request.use_ai}")
        
        # Check Elasticsearch connection
        if not es:
            raise HTTPException(
                status_code=503,
                detail="Search service unavailable - Elasticsearch not connected"
            )
        
        extracted_entities = None
        search_type = "basic"
        
        # Step 1: Entity extraction (if AI enabled)
        if request.use_ai and openai_service.is_available():
            try:
                logger.info("Attempting AI entity extraction")
                extracted_entities = await openai_service.extract_entities(
                    query=request.query,
                    timeout=10
                )
                
                if extracted_entities:
                    search_type = "intelligent"
                    logger.info(f"AI extraction successful: {extracted_entities.model_dump_json()}")
                else:
                    logger.warning("AI extraction returned None - falling back to basic search")
                    
            except Exception as e:
                logger.error(f"AI extraction failed: {e} - falling back to basic search")
        else:
            logger.info("AI extraction disabled or unavailable - using basic search")
        
        # Step 2: Build Elasticsearch query
        # 🚀 HYBRID SEARCH: Use different strategies based on confidence
        if extracted_entities:
            confidence = extracted_entities.confidence or 0.0
            
            if confidence >= 0.8:
                # High confidence: Use structured intelligent query
                search_type = "intelligent"
                es_query = query_builder.build_intelligent_query(
                    entities=extracted_entities,
                    size=request.page_size,
                    from_=from_offset
                )
                logger.info(f"Using structured query (confidence: {confidence:.2f})")
            else:
                # Low confidence: Use hybrid multi-field query
                search_type = "hybrid"
                es_query = query_builder.build_hybrid_query(
                    query_text=request.query,
                    entities=extracted_entities,
                    size=request.page_size,
                    from_=from_offset
                )
                logger.info(f"Using hybrid query with nested fields (low confidence: {confidence:.2f})")
        else:
            # No entities extracted: Use basic search
            es_query = query_builder.build_basic_query(
                query_text=request.query,
                size=request.page_size,
                from_=from_offset
            )
            logger.info("Using basic full-text query (no AI extraction)")
        
        logger.debug(f"Elasticsearch query: {es_query}")
        
        # Step 3: Execute search
        try:
            es_response = await es.search(
                index="clinical_trials",
                body=es_query
            )
        except RequestError as e:
            logger.error(f"Invalid Elasticsearch query: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid search query: {str(e)}"
            )
        except ESConnectionError as e:
            logger.error(f"Elasticsearch connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Search service temporarily unavailable"
            )
        
        # Step 4: Parse results
        total_results = es_response['hits']['total']['value']
        hits = es_response['hits']['hits']
        
        logger.info(f"Search completed: found {total_results} results, returning {len(hits)}")
        
        # Step 5: Format trial summaries
        results = []
        for hit in hits:
            source = hit['_source']
            
            trial_summary = TrialSummary(
                nct_id=hit['_id'],
                brief_title=source.get('brief_title', 'No title'),
                official_title=source.get('official_title'),
                phase=source.get('phase'),
                overall_status=source.get('overall_status'),
                study_type=source.get('study_type'),
                brief_summaries_description=source.get('brief_summaries_description'),
                conditions=source.get('conditions'),
                interventions=source.get('interventions'),
                enrollment=source.get('enrollment'),
                start_date=source.get('start_date'),
                completion_date=source.get('completion_date'),
                score=hit.get('_score')
            )
            results.append(trial_summary)
        
        # Calculate time taken
        took_ms = int((time.time() - start_time) * 1000)
        
        # Calculate total pages
        total_pages = (total_results + request.page_size - 1) // request.page_size
        
        # Build response
        response = SearchResponse(
            query=request.query,
            extracted_entities=extracted_entities,
            total_results=total_results,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            results=results,
            took_ms=took_ms,
            used_ai=extracted_entities is not None,
            search_type=search_type
        )
        
        logger.info(f"Search response prepared in {took_ms}ms - page {request.page}/{total_pages}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal search error: {str(e)}"
        )


@router.get(
    "/trial/{nct_id}",
    response_model=TrialDetailResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get detailed information about a specific trial",
    description="""
    Retrieve complete details for a clinical trial by NCT ID.
    
    Returns all available information including:
    - Basic information (title, phase, status)
    - Eligibility criteria
    - Detailed descriptions
    - Conditions and interventions
    - Sponsors and collaborators
    - Locations and contacts
    - Outcomes and adverse events
    """
)
async def get_trial_detail(
    nct_id: str = Path(
        ...,
        description="ClinicalTrials.gov NCT ID",
        example="NCT06890351",
        regex="^NCT[0-9]{8}$"
    )
) -> TrialDetailResponse:
    """Get complete details for a specific clinical trial."""
    es = get_es_client()
    
    try:
        logger.info(f"Fetching trial detail: {nct_id}")
        
        if not es:
            raise HTTPException(
                status_code=503,
                detail="Search service unavailable - Elasticsearch not connected"
            )
        
        # Fetch trial document
        try:
            response = await es.get(
                index="clinical_trials",
                id=nct_id
            )
            
            trial_data = response['_source']
            logger.info(f"Trial {nct_id} found")
            
            return TrialDetailResponse(
                nct_id=nct_id,
                found=True,
                trial=TrialDetail(**trial_data)
            )
            
        except NotFoundError:
            logger.warning(f"Trial not found: {nct_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Trial {nct_id} not found"
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error fetching trial {nct_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trial: {str(e)}"
        )


@router.get(
    "/filters",
    response_model=FiltersResponse,
    responses={
        500: {"model": ErrorResponse}
    },
    summary="Get available filter options",
    description="""
    Retrieve available filter options with document counts.
    
    Returns aggregated data for:
    - Available phases (PHASE1, PHASE2, PHASE3, etc.)
    - Recruitment statuses (RECRUITING, COMPLETED, etc.)
    - Study types (INTERVENTIONAL, OBSERVATIONAL)
    - Top medical conditions
    
    Useful for building filter UI components.
    """
)
async def get_filters() -> FiltersResponse:
    """Get available filter options with counts."""
    es = get_es_client()
    
    try:
        logger.info("Fetching filter options")
        
        if not es:
            raise HTTPException(
                status_code=503,
                detail="Search service unavailable - Elasticsearch not connected"
            )
        
        # Build aggregation query
        agg_query = query_builder.build_aggregation_query()
        
        # Execute query
        response = await es.search(
            index="clinical_trials",
            body=agg_query
        )
        
        # Parse aggregations
        aggregations = response['aggregations']
        total_trials = response['hits']['total']['value']
        
        # Format phases
        phases = [
            {
                "key": bucket['key'],
                "doc_count": bucket['doc_count']
            }
            for bucket in aggregations['phases']['buckets']
        ]
        
        # Format statuses
        statuses = [
            {
                "key": bucket['key'],
                "doc_count": bucket['doc_count']
            }
            for bucket in aggregations['statuses']['buckets']
        ]
        
        # Format study types
        study_types = [
            {
                "key": bucket['key'],
                "doc_count": bucket['doc_count']
            }
            for bucket in aggregations['study_types']['buckets']
        ]
        
        # Format top conditions (nested aggregation)
        top_conditions = [
            {
                "name": bucket['key'],
                "doc_count": bucket['doc_count']
            }
            for bucket in aggregations['top_conditions']['condition_names']['buckets']
        ]
        
        logger.info(f"Filter options retrieved: {len(phases)} phases, {len(statuses)} statuses, "
                   f"{len(study_types)} study types, {len(top_conditions)} conditions")
        
        return FiltersResponse(
            phases=phases,
            statuses=statuses,
            study_types=study_types,
            top_conditions=top_conditions,
            total_trials=total_trials
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error fetching filters: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving filters: {str(e)}"
        )


@router.get(
    "/similar/{nct_id}",
    response_model=SearchResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Find similar trials",
    description="""
    Find clinical trials similar to the specified trial.
    
    Uses Elasticsearch's "More Like This" query to find trials with similar:
    - Conditions
    - Interventions
    - Descriptions
    - Keywords
    
    Useful for "You might also be interested in" features.
    """
)
async def find_similar_trials(
    nct_id: str = Path(
        ...,
        description="NCT ID of reference trial",
        example="NCT06890351",
        regex="^NCT[0-9]{8}$"
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number for pagination"
    ),
    page_size: int = Query(
        default=5,
        ge=1,
        le=20,
        description="Number of similar trials per page"
    )
) -> SearchResponse:
    """Find trials similar to the specified trial."""
    start_time = time.time()
    es = get_es_client()
    
    try:
        # Calculate offset from page number
        from_offset = (page - 1) * page_size
        
        logger.info(f"Finding similar trials for: {nct_id}, page={page}, page_size={page_size}")
        
        if not es:
            raise HTTPException(
                status_code=503,
                detail="Search service unavailable - Elasticsearch not connected"
            )
        
        # Check if reference trial exists
        try:
            await es.get(index="clinical_trials", id=nct_id)
        except NotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Reference trial {nct_id} not found"
            )
        
        # Build similar trials query
        similar_query = query_builder.build_similar_trials_query(
            nct_id=nct_id,
            size=page_size,
            from_=from_offset
        )
        
        # Execute search
        response = await es.search(
            index="clinical_trials",
            body=similar_query
        )
        
        # Parse results
        total_results = response['hits']['total']['value']
        hits = response['hits']['hits']
        
        # Format results
        results = []
        for hit in hits:
            source = hit['_source']
            trial_summary = TrialSummary(
                nct_id=hit['_id'],
                brief_title=source.get('brief_title', 'No title'),
                official_title=source.get('official_title'),
                phase=source.get('phase'),
                overall_status=source.get('overall_status'),
                study_type=source.get('study_type'),
                brief_summaries_description=source.get('brief_summaries_description'),
                conditions=source.get('conditions'),
                interventions=source.get('interventions'),
                enrollment=source.get('enrollment'),
                start_date=source.get('start_date'),
                completion_date=source.get('completion_date'),
                score=hit.get('_score')
            )
            results.append(trial_summary)
        
        took_ms = int((time.time() - start_time) * 1000)
        
        # Calculate total pages
        total_pages = (total_results + page_size - 1) // page_size
        
        logger.info(f"Found {len(results)} similar trials in {took_ms}ms - page {page}/{total_pages}")
        
        return SearchResponse(
            query=f"Similar to {nct_id}",
            extracted_entities=None,
            total_results=total_results,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            results=results,
            took_ms=took_ms,
            used_ai=False,
            search_type="similar"
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error finding similar trials: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error finding similar trials: {str(e)}"
        )
