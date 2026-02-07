"""
Elasticsearch index mapping for clinical trials.
Defines field types, analyzers, and nested structures.
"""

# Elasticsearch index mapping for clinical_trials
CLINICAL_TRIALS_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "english_analyzer": {
                    "type": "english"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # Core identifiers
            "nct_id": {
                "type": "keyword"
            },
            
            # Title fields - searchable with keyword subfield for sorting
            "brief_title": {
                "type": "text",
                "analyzer": "english",
                "fields": {
                    "raw": {"type": "keyword"}
                }
            },
            "official_title": {
                "type": "text",
                "analyzer": "english"
            },
            
            # Description fields - full text search
            "brief_summaries_description": {
                "type": "text",
                "analyzer": "english"
            },
            "detailed_description": {
                "type": "text",
                "analyzer": "english"
            },
            
            # Categorical fields - exact match filtering
            "phase": {
                "type": "keyword"
            },
            "overall_status": {
                "type": "keyword"
            },
            "study_type": {
                "type": "keyword"
            },
            "source": {
                "type": "keyword"
            },
            "gender": {
                "type": "keyword"
            },
            "allocation": {
                "type": "keyword"
            },
            "intervention_model": {
                "type": "keyword"
            },
            "primary_purpose": {
                "type": "keyword"
            },
            "masking": {
                "type": "keyword"
            },
            "observational_model": {
                "type": "keyword"
            },
            
            # Numeric fields
            "enrollment": {
                "type": "integer"
            },
            "number_of_arms": {
                "type": "integer"
            },
            "number_of_groups": {
                "type": "integer"
            },
            
            # Boolean fields
            "healthy_volunteers": {
                "type": "boolean"
            },
            "has_results": {
                "type": "boolean"
            },
            "has_dmc": {
                "type": "boolean"
            },
            
            # Date fields
            "start_date": {
                "type": "date",
                "ignore_malformed": True
            },
            "completion_date": {
                "type": "date",
                "ignore_malformed": True
            },
            "primary_completion_date": {
                "type": "date",
                "ignore_malformed": True
            },
            "study_first_submitted_date": {
                "type": "date",
                "ignore_malformed": True
            },
            "last_update_submitted_date": {
                "type": "date",
                "ignore_malformed": True
            },
            
            # Nested arrays - conditions
            "conditions": {
                "type": "nested",
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    }
                }
            },
            
            # Nested arrays - interventions
            "interventions": {
                "type": "nested",
                "properties": {
                    "intervention_type": {
                        "type": "keyword"
                    },
                    "name": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "english"
                    }
                }
            },
            
            # Nested arrays - sponsors
            "sponsors": {
                "type": "nested",
                "properties": {
                    "name": {
                        "type": "keyword"
                    },
                    "lead_or_collaborator": {
                        "type": "keyword"
                    }
                }
            },
            
            # Nested arrays - facilities
            "facilities": {
                "type": "nested",
                "properties": {
                    "name": {
                        "type": "text",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    },
                    "city": {
                        "type": "keyword"
                    },
                    "state": {
                        "type": "keyword"
                    },
                    "country": {
                        "type": "keyword"
                    }
                }
            },
            
            # Keywords array - simple strings
            "keywords": {
                "type": "text",
                "analyzer": "english",
                "fields": {
                    "raw": {"type": "keyword"}
                }
            },
            
            # Browse conditions and interventions
            "browse_conditions": {
                "type": "nested",
                "properties": {
                    "mesh_term": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    }
                }
            },
            
            "browse_interventions": {
                "type": "nested",
                "properties": {
                    "mesh_term": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    }
                }
            },
            
            # Design outcomes
            "design_outcomes": {
                "type": "nested",
                "properties": {
                    "measure": {
                        "type": "text",
                        "analyzer": "english"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "english"
                    },
                    "time_frame": {
                        "type": "text"
                    }
                }
            },
            
            # Adverse events
            "adverse_events": {
                "type": "nested",
                "properties": {
                    "result_group_code": {
                        "type": "keyword"
                    },
                    "subjects_affected": {
                        "type": "integer"
                    },
                    "subjects_at_risk": {
                        "type": "integer"
                    },
                    "organ_system": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    },
                    "adverse_event_term": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    },
                    "event_type": {
                        "type": "keyword"
                    },
                    "result_group_title": {
                        "type": "text"
                    },
                    "result_group_description": {
                        "type": "text"
                    },
                    "risk_ratio": {
                        "type": "float"
                    }
                }
            }
        }
    }
}
