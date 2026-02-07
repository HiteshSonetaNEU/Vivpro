"""
Query builder for constructing Elasticsearch queries from extracted entities.
Production-ready with comprehensive query construction and fallback strategies.
"""

import logging
from typing import Dict, Any, List, Optional
from models import ExtractedEntities

logger = logging.getLogger(__name__)


class QueryBuilder:
    """Build Elasticsearch queries from extracted entities or raw search terms."""
    
    def __init__(self):
        """Initialize query builder."""
        logger.info("QueryBuilder initialized")
    
    def build_intelligent_query(
        self,
        entities: ExtractedEntities,
        size: int = 10,
        from_: int = 0
    ) -> Dict[str, Any]:
        """
        Build intelligent Elasticsearch query from extracted entities.
        
        Uses must/should/filter clauses for optimal relevance and performance.
        
        Args:
            entities: Extracted entities from OpenAI
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Complete Elasticsearch query DSL
        """
        logger.info(f"Building intelligent query from entities: {entities.model_dump_json()}")
        
        # Build query clauses
        must_clauses = []
        should_clauses = []
        filter_clauses = []
        
        # EXACT MATCH FILTERS (must match)
        # Phase filter
        if entities.phase:
            filter_clauses.append({
                "term": {"phase": entities.phase}
            })
            logger.debug(f"Added phase filter: {entities.phase}")
        
        # Status filter
        if entities.status:
            filter_clauses.append({
                "term": {"overall_status": entities.status}
            })
            logger.debug(f"Added status filter: {entities.status}")
        
        # Study type filter
        if entities.study_type:
            filter_clauses.append({
                "term": {"study_type": entities.study_type}
            })
            logger.debug(f"Added study_type filter: {entities.study_type}")
        
        # RELEVANCE SCORING (should match - boosts score)
        # Conditions
        if entities.conditions:
            for condition in entities.conditions:
                # High boost for condition name match
                should_clauses.append({
                    "nested": {
                        "path": "conditions",
                        "query": {
                            "match": {
                                "conditions.name": {
                                    "query": condition,
                                    "boost": 3.0
                                }
                            }
                        }
                    }
                })
                # Also search in other text fields
                should_clauses.append({
                    "multi_match": {
                        "query": condition,
                        "fields": [
                            "brief_title^2",
                            "official_title^1.5",
                            "brief_summaries_description"
                        ],
                        "boost": 1.5
                    }
                })
            logger.debug(f"Added {len(entities.conditions)} condition queries")
        
        # Interventions
        if entities.interventions:
            for intervention in entities.interventions:
                # High boost for intervention name match
                should_clauses.append({
                    "nested": {
                        "path": "interventions",
                        "query": {
                            "match": {
                                "interventions.name": {
                                    "query": intervention,
                                    "boost": 3.0
                                }
                            }
                        }
                    }
                })
                # Also search in description
                should_clauses.append({
                    "nested": {
                        "path": "interventions",
                        "query": {
                            "match": {
                                "interventions.description": {
                                    "query": intervention,
                                    "boost": 1.5
                                }
                            }
                        }
                    }
                })
            logger.debug(f"Added {len(entities.interventions)} intervention queries")
        
        # Sponsors
        if entities.sponsors:
            for sponsor in entities.sponsors:
                # Nested query for sponsor name
                should_clauses.append({
                    "nested": {
                        "path": "sponsors",
                        "query": {
                            "match": {
                                "sponsors.name": {
                                    "query": sponsor,
                                    "boost": 2.5
                                }
                            }
                        }
                    }
                })
                # Also check source field (lead sponsor)
                should_clauses.append({
                    "match": {
                        "source": {
                            "query": sponsor,
                            "boost": 2.0
                        }
                    }
                })
            logger.debug(f"Added {len(entities.sponsors)} sponsor queries")
        
        # Locations
        if entities.locations:
            for location in entities.locations:
                # Nested query for facility location
                should_clauses.append({
                    "nested": {
                        "path": "facilities",
                        "query": {
                            "bool": {
                                "should": [
                                    {"match": {"facilities.city": {"query": location, "boost": 3.0}}},
                                    {"match": {"facilities.state": {"query": location, "boost": 2.5}}},
                                    {"match": {"facilities.country": {"query": location, "boost": 2.0}}}
                                ]
                            }
                        }
                    }
                })
            logger.debug(f"Added {len(entities.locations)} location queries")
        
        # Keywords - search across all text fields
        if entities.keywords:
            for keyword in entities.keywords:
                should_clauses.append({
                    "multi_match": {
                        "query": keyword,
                        "fields": [
                            "brief_title^2",
                            "official_title^1.5",
                            "brief_summaries_description",
                            "detailed_description"
                        ],
                        "boost": 1.0
                    }
                })
            logger.debug(f"Added {len(entities.keywords)} keyword queries")
        
        # If no specific should clauses, use original query for full-text search
        if not should_clauses and entities.original_query:
            should_clauses.append({
                "multi_match": {
                    "query": entities.original_query,
                    "fields": [
                        "brief_title^3",
                        "official_title^2",
                        "brief_summaries_description^1.5",
                        "detailed_description"
                    ],
                    "type": "best_fields",
                    "boost": 2.0
                }
            })
            logger.debug("Added fallback full-text search")
        
        # Construct bool query
        bool_query = {}
        if must_clauses:
            bool_query["must"] = must_clauses
        if should_clauses:
            bool_query["should"] = should_clauses
            # Only require should match if there are no filters
            # With filters, should clauses are for scoring only
            if not filter_clauses:
                bool_query["minimum_should_match"] = 1
        if filter_clauses:
            bool_query["filter"] = filter_clauses
        
        # Construct final query
        query = {
            "size": size,
            "from": from_,
            "query": {
                "bool": bool_query
            } if bool_query else {
                "match_all": {}
            },
            "_source": {
                "excludes": ["detailed_description"]  # Exclude large fields from results
            },
            "track_scores": True
        }
        
        logger.info(f"Built intelligent query with {len(filter_clauses)} filters, "
                   f"{len(should_clauses)} should clauses")
        return query
    
    def build_basic_query(
        self,
        query_text: str,
        size: int = 10,
        from_: int = 0
    ) -> Dict[str, Any]:
        """
        Build basic full-text search query (fallback when AI extraction fails).
        
        Args:
            query_text: Raw search text
            size: Number of results
            from_: Offset for pagination
            
        Returns:
            Elasticsearch query DSL
        """
        logger.info(f"Building basic query for text: {query_text}")
        
        query = {
            "size": size,
            "from": from_,
            "query": {
                "multi_match": {
                    "query": query_text,
                    "fields": [
                        "brief_title^3",
                        "official_title^2",
                        "brief_summaries_description^1.5",
                        "detailed_description",
                        "conditions.name^2",
                        "interventions.name^2",
                        "keywords"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "_source": {
                "excludes": ["detailed_description"]
            },
            "track_scores": True
        }
        
        logger.info("Built basic full-text query with fuzzy matching")
        return query
    
    def build_hybrid_query(
        self,
        query_text: str,
        entities: Optional[ExtractedEntities] = None,
        size: int = 10,
        from_: int = 0
    ) -> Dict[str, Any]:
        """
        Build hybrid query for low-confidence extractions.
        Searches across ALL fields including nested sponsors and facilities.
        
        This is used when AI confidence is low (<0.8) to cast a wider net
        and find results even when entity extraction is uncertain.
        
        Args:
            query_text: Raw search text
            entities: Optional extracted entities (may have keywords, sponsors, locations)
            size: Number of results
            from_: Offset for pagination
            
        Returns:
            Elasticsearch query with comprehensive field coverage
        """
        logger.info(f"Building hybrid query for text: {query_text} (low confidence)")
        
        should_clauses = []
        
        # Main text search across standard fields
        should_clauses.append({
            "multi_match": {
                "query": query_text,
                "fields": [
                    "brief_title^3",
                    "official_title^2",
                    "brief_summaries_description^1.5",
                    "detailed_description",
                    "keywords"
                ],
                "type": "best_fields",
                "fuzziness": "AUTO",
                "boost": 2.0
            }
        })
        
        # Search in nested conditions
        should_clauses.append({
            "nested": {
                "path": "conditions",
                "query": {
                    "match": {
                        "conditions.name": {
                            "query": query_text,
                            "fuzziness": "AUTO",
                            "boost": 2.5
                        }
                    }
                }
            }
        })
        
        # Search in nested interventions
        should_clauses.append({
            "nested": {
                "path": "interventions",
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["interventions.name^2", "interventions.description"],
                        "fuzziness": "AUTO",
                        "boost": 2.0
                    }
                }
            }
        })
        
        # Search in nested sponsors
        should_clauses.append({
            "nested": {
                "path": "sponsors",
                "query": {
                    "match": {
                        "sponsors.name": {
                            "query": query_text,
                            "fuzziness": "AUTO",
                            "boost": 2.5
                        }
                    }
                }
            }
        })
        
        # Search in nested facilities (locations)
        should_clauses.append({
            "nested": {
                "path": "facilities",
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": [
                            "facilities.city^3",
                            "facilities.state^2.5",
                            "facilities.country^2",
                            "facilities.name"
                        ],
                        "fuzziness": "AUTO",
                        "boost": 2.0
                    }
                }
            }
        })
        
        # Also search in source field (lead sponsor)
        should_clauses.append({
            "match": {
                "source": {
                    "query": query_text,
                    "fuzziness": "AUTO",
                    "boost": 1.5
                }
            }
        })
        
        # If entities were extracted, add specific boosts for those
        if entities:
            if entities.sponsors:
                for sponsor in entities.sponsors:
                    should_clauses.append({
                        "nested": {
                            "path": "sponsors",
                            "query": {
                                "match": {
                                    "sponsors.name": {
                                        "query": sponsor,
                                        "boost": 3.0
                                    }
                                }
                            }
                        }
                    })
            
            if entities.locations:
                for location in entities.locations:
                    should_clauses.append({
                        "nested": {
                            "path": "facilities",
                            "query": {
                                "bool": {
                                    "should": [
                                        {"match": {"facilities.city": {"query": location, "boost": 3.5}}},
                                        {"match": {"facilities.state": {"query": location, "boost": 3.0}}},
                                        {"match": {"facilities.country": {"query": location, "boost": 2.5}}}
                                    ]
                                }
                            }
                        }
                    })
        
        query = {
            "size": size,
            "from": from_,
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            },
            "_source": {
                "excludes": ["detailed_description"]
            },
            "track_scores": True
        }
        
        logger.info(f"Built hybrid query with {len(should_clauses)} search clauses")
        return query
    
    def build_similar_trials_query(
        self,
        nct_id: str,
        size: int = 5,
        from_: int = 0
    ) -> Dict[str, Any]:
        """
        Build query to find similar trials (for "More Like This" feature).
        
        Args:
            nct_id: NCT ID of reference trial
            size: Number of similar trials to return
            from_: Offset for pagination
            
        Returns:
            Elasticsearch More Like This query
        """
        logger.info(f"Building similar trials query for: {nct_id}, size={size}, from={from_}")
        
        query = {
            "size": size,
            "from": from_,
            "query": {
                "more_like_this": {
                    "fields": [
                        "brief_title",
                        "brief_summaries_description",
                        "conditions.name",
                        "interventions.name"
                    ],
                    "like": [
                        {
                            "_index": "clinical_trials",
                            "_id": nct_id
                        }
                    ],
                    "min_term_freq": 1,
                    "min_doc_freq": 2,
                    "max_query_terms": 25
                }
            },
            "_source": {
                "excludes": ["detailed_description"]
            }
        }
        
        return query
    
    def build_aggregation_query(self) -> Dict[str, Any]:
        """
        Build query for retrieving filter options (phases, statuses, etc.).
        
        Returns:
            Elasticsearch aggregation query
        """
        logger.info("Building aggregation query for filters")
        
        query = {
            "size": 0,  # Don't return documents, only aggregations
            "aggs": {
                "phases": {
                    "terms": {
                        "field": "phase",
                        "size": 20,
                        "missing": "UNKNOWN"
                    }
                },
                "statuses": {
                    "terms": {
                        "field": "overall_status",
                        "size": 20,
                        "missing": "UNKNOWN"
                    }
                },
                "study_types": {
                    "terms": {
                        "field": "study_type",
                        "size": 10,
                        "missing": "UNKNOWN"
                    }
                },
                "top_conditions": {
                    "nested": {
                        "path": "conditions"
                    },
                    "aggs": {
                        "condition_names": {
                            "terms": {
                                "field": "conditions.name.keyword",
                                "size": 20
                            }
                        }
                    }
                }
            }
        }
        
        return query
    
    def build_count_query(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build query for counting documents with optional filters.
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            Elasticsearch count query
        """
        if not filters:
            return {"query": {"match_all": {}}}
        
        filter_clauses = []
        
        if "phase" in filters:
            filter_clauses.append({"term": {"phase": filters["phase"]}})
        
        if "status" in filters:
            filter_clauses.append({"term": {"overall_status": filters["status"]}})
        
        if "study_type" in filters:
            filter_clauses.append({"term": {"study_type": filters["study_type"]}})
        
        return {
            "query": {
                "bool": {
                    "filter": filter_clauses
                }
            }
        } if filter_clauses else {"query": {"match_all": {}}}


# Global query builder instance
query_builder = QueryBuilder()
