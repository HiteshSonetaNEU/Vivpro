"""
OpenAI service for entity extraction from natural language queries.
Production-ready with comprehensive error handling and fallbacks.
Includes intelligent caching to reduce API costs and improve response times.
"""

import logging
import json
import hashlib
import time
from typing import Optional, Dict, Any
from openai import OpenAI, OpenAIError, APIError, RateLimitError, APIConnectionError
from config import Config
from models import ExtractedEntities

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for extracting structured entities from natural language queries."""
    
    def __init__(self):
        """Initialize OpenAI client with caching."""
        if not Config.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured - entity extraction will be disabled")
            self.client = None
        else:
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
            logger.info("OpenAI service initialized successfully")
        
        # In-memory cache: {query_hash: (entities, timestamp)}
        self._cache: Dict[str, tuple[ExtractedEntities, float]] = {}
        self._cache_ttl = 600  # 10 minutes TTL
        self._cache_max_size = 1000  # Max 1000 cached queries
        
        logger.info(f"Entity cache initialized (TTL: {self._cache_ttl}s, Max size: {self._cache_max_size})")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.client is not None
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query (case-insensitive)."""
        normalized_query = query.lower().strip()
        return hashlib.md5(normalized_query.encode()).hexdigest()
    
    def _get_from_cache(self, query: str) -> Optional[ExtractedEntities]:
        """Get entities from cache if available and not expired."""
        cache_key = self._get_cache_key(query)
        
        if cache_key in self._cache:
            entities, timestamp = self._cache[cache_key]
            age = time.time() - timestamp
            
            if age < self._cache_ttl:
                logger.info(f"Cache HIT for query: '{query}' (age: {age:.1f}s)")
                return entities
            else:
                # Expired - remove from cache
                logger.debug(f"Cache EXPIRED for query: '{query}' (age: {age:.1f}s)")
                del self._cache[cache_key]
        
        logger.info(f"Cache MISS for query: '{query}'")
        return None
    
    def _add_to_cache(self, query: str, entities: ExtractedEntities) -> None:
        """Add entities to cache with current timestamp."""
        # Check cache size limit
        if len(self._cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO eviction)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache full - evicted oldest entry")
        
        cache_key = self._get_cache_key(query)
        self._cache[cache_key] = (entities, time.time())
        logger.debug(f"Cached entities for query: '{query}' (cache size: {len(self._cache)})")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            "cache_size": len(self._cache),
            "cache_max_size": self._cache_max_size,
            "cache_ttl_seconds": self._cache_ttl,
            "utilization_percent": (len(self._cache) / self._cache_max_size) * 100
        }
    
    async def extract_entities(
        self,
        query: str,
        timeout: int = 10
    ) -> Optional[ExtractedEntities]:
        """
        Extract structured entities from natural language query.
        Uses intelligent caching to reduce API calls and improve performance.
        
        Args:
            query: Natural language search query
            timeout: Timeout in seconds
            
        Returns:
            ExtractedEntities object or None if extraction fails
            
        Example:
            Input: "Find Phase 2 breast cancer trials that are recruiting"
            Output: {
                "phase": "PHASE2",
                "conditions": ["breast cancer"],
                "status": "RECRUITING",
                "study_type": null,
                "interventions": null,
                "keywords": []
            }
        """
        if not self.client:
            logger.warning("OpenAI client not initialized - skipping entity extraction")
            return None
        
        # 🚀 Check cache first
        cached_entities = self._get_from_cache(query)
        if cached_entities:
            return cached_entities
        
        try:
            logger.info(f"Extracting entities from query: {query}")
            
            # Construct system prompt for entity extraction
            system_prompt = self._build_system_prompt()
            
            # Call OpenAI API with JSON mode
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500,
                timeout=timeout
            )
            
            # Parse response
            content = response.choices[0].message.content
            entities_dict = json.loads(content)
            
            # Add original query
            entities_dict['original_query'] = query
            
            # Validate and create ExtractedEntities object
            entities = ExtractedEntities(**entities_dict)
            
            logger.info(f"Successfully extracted entities: {entities.model_dump_json()}")
            
            # 🚀 Store in cache for future requests
            self._add_to_cache(query, entities)
            
            return entities
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return None
            
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            return None
            
        except APIConnectionError as e:
            logger.error(f"OpenAI API connection error: {e}")
            return None
            
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None
            
        except OpenAIError as e:
            logger.error(f"OpenAI error: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error during entity extraction: {e}", exc_info=True)
            return None
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for entity extraction."""
        return """You are an expert at extracting structured information from clinical trial search queries.

Your task is to extract the following entities from user queries:
- phase: Clinical trial phase (PHASE1, PHASE2, PHASE3, PHASE4, PHASE1/PHASE2, PHASE2/PHASE3, NA, or null)
- conditions: List of medical conditions or diseases (e.g., ["breast cancer", "diabetes"])
- interventions: List of treatments, drugs, or interventions (e.g., ["chemotherapy", "pembrolizumab"])
- status: Recruitment status (RECRUITING, NOT_YET_RECRUITING, ACTIVE_NOT_RECRUITING, COMPLETED, TERMINATED, SUSPENDED, WITHDRAWN, UNKNOWN, or null)
- study_type: Type of study (INTERVENTIONAL, OBSERVATIONAL, or null)
- sponsors: List of sponsor organizations, pharmaceutical companies, or institutions (e.g., ["Pfizer", "Mayo Clinic", "NIH"])
- locations: List of geographic locations like cities, states, or countries (e.g., ["Boston", "California", "United States"])
- keywords: Additional relevant keywords or concepts
- confidence: Your confidence in the extraction (0.0 to 1.0)

IMPORTANT RULES:
1. Only extract entities that are explicitly mentioned or clearly implied in the query
2. Return null for entities that are not mentioned
3. Use standard values (e.g., "PHASE2" not "Phase 2", "RECRUITING" not "recruiting")
4. For conditions, use medical terminology (e.g., "breast cancer" not "cancer of the breast")
5. For sponsors, extract pharmaceutical companies, universities, hospitals, or research organizations
6. For locations, extract cities, states, or countries mentioned
7. Return empty list [] for keywords if no additional concepts are mentioned
8. Be conservative - if unsure, return null rather than guessing

Examples:

Query: "Find Phase 2 breast cancer trials"
Response: {
  "phase": "PHASE2",
  "conditions": ["breast cancer"],
  "interventions": null,
  "status": null,
  "study_type": null,
  "sponsors": null,
  "locations": null,
  "keywords": [],
  "confidence": 0.95
}

Query: "Pfizer trials in Boston"
Response: {
  "phase": null,
  "conditions": null,
  "interventions": null,
  "status": null,
  "study_type": null,
  "sponsors": ["Pfizer"],
  "locations": ["Boston"],
  "keywords": [],
  "confidence": 0.9
}

Query: "Mayo Clinic diabetes studies"
Response: {
  "phase": null,
  "conditions": ["diabetes"],
  "interventions": null,
  "status": null,
  "study_type": null,
  "sponsors": ["Mayo Clinic"],
  "locations": null,
  "keywords": [],
  "confidence": 0.85
}

Query: "Recruiting studies for diabetes with metformin"
Response: {
  "phase": null,
  "conditions": ["diabetes"],
  "interventions": ["metformin"],
  "status": "RECRUITING",
  "study_type": null,
  "sponsors": null,
  "locations": null,
  "keywords": [],
  "confidence": 0.9
}

Query: "Phase 3 cancer trials in California sponsored by Novartis"
Response: {
  "phase": "PHASE3",
  "conditions": ["cancer"],
  "interventions": null,
  "status": null,
  "study_type": null,
  "sponsors": ["Novartis"],
  "locations": ["California"],
  "keywords": [],
  "confidence": 0.95
}

Query: "asthma"
Response: {
  "phase": null,
  "conditions": ["asthma"],
  "interventions": null,
  "status": null,
  "study_type": null,
  "sponsors": null,
  "locations": null,
  "keywords": [],
  "confidence": 0.85
}

Query: "completed cancer immunotherapy trials"
Response: {
  "phase": null,
  "conditions": ["cancer"],
  "interventions": ["immunotherapy"],
  "status": "COMPLETED",
  "study_type": null,
  "keywords": [],
  "confidence": 0.9
}

Return ONLY valid JSON matching this schema. Do not include any additional text or explanation."""
    
    def extract_entities_sync(
        self,
        query: str,
        timeout: int = 10
    ) -> Optional[ExtractedEntities]:
        """
        Synchronous version of extract_entities.
        Used for testing or non-async contexts.
        """
        if not self.client:
            logger.warning("OpenAI client not initialized - skipping entity extraction")
            return None
        
        try:
            logger.info(f"Extracting entities from query (sync): {query}")
            
            system_prompt = self._build_system_prompt()
            
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=500,
                timeout=timeout
            )
            
            content = response.choices[0].message.content
            entities_dict = json.loads(content)
            entities_dict['original_query'] = query
            
            entities = ExtractedEntities(**entities_dict)
            
            logger.info(f"Successfully extracted entities (sync): {entities.model_dump_json()}")
            return entities
            
        except Exception as e:
            logger.error(f"Error during synchronous entity extraction: {e}", exc_info=True)
            return None


# Global service instance
openai_service = OpenAIService()
