"""
Data preprocessing module for clinical trials data.
Handles validation, cleaning, and normalization before Elasticsearch ingestion.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class DataPreprocessor:
    """Preprocess clinical trial data before Elasticsearch ingestion."""
    
    def __init__(self):
        self.stats = {
            "total_records": 0,
            "valid_records": 0,
            "skipped_records": 0,
            "warnings": []
        }
    
    def preprocess_trial(self, trial: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Preprocess a single trial record.
        Returns cleaned record or None if invalid.
        """
        self.stats["total_records"] += 1
        
        try:
            # 1. Validate required fields
            if not self._validate_required_fields(trial):
                return None
            
            # 2. Clean text fields
            trial = self._clean_text_fields(trial)
            
            # 3. Normalize dates
            trial = self._normalize_dates(trial)
            
            # 4. Clean nested arrays
            trial = self._clean_nested_arrays(trial)
            
            # 5. Convert data types
            trial = self._convert_data_types(trial)
            
            # 6. Handle missing values
            trial = self._handle_missing_values(trial)
            
            self.stats["valid_records"] += 1
            return trial
            
        except Exception as e:
            logger.error(f"Failed to preprocess trial {trial.get('nct_id', 'UNKNOWN')}: {e}")
            self.stats["skipped_records"] += 1
            return None
    
    def _validate_required_fields(self, trial: Dict) -> bool:
        """Ensure critical fields exist."""
        required = ["nct_id"]
        
        for field in required:
            if not trial.get(field):
                logger.warning(f"Missing required field '{field}', skipping record")
                self.stats["skipped_records"] += 1
                return False
        
        return True
    
    def _clean_text_fields(self, trial: Dict) -> Dict:
        """Remove null bytes, excessive whitespace, control characters."""
        text_fields = [
            "brief_title", "official_title", "brief_summaries_description", 
            "detailed_description", "intervention_model_description",
            "primary_purpose", "source"
        ]
        
        for field in text_fields:
            if trial.get(field):
                text = trial[field]
                if isinstance(text, str):
                    # Remove null bytes
                    text = text.replace('\x00', '')
                    # Remove other control characters (except newlines/tabs)
                    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
                    # Normalize whitespace
                    text = ' '.join(text.split())
                    # Truncate if too long (ES limit is 32KB, use 30KB to be safe)
                    if len(text) > 30000:
                        text = text[:30000] + "... [truncated]"
                        self.stats["warnings"].append(f"{trial['nct_id']}: Truncated {field}")
                    
                    trial[field] = text if text else None
        
        return trial
    
    def _normalize_dates(self, trial: Dict) -> Dict:
        """Parse and validate date fields."""
        date_fields = [
            "study_first_submitted_date", "last_update_submitted_date",
            "last_update_posted_date", "results_first_posted_date",
            "start_date", "completion_date", "primary_completion_date"
        ]
        
        for field in date_fields:
            if trial.get(field):
                try:
                    # Try parsing the date
                    if isinstance(trial[field], str):
                        # Handle ISO format and various date formats
                        date_str = trial[field].replace('Z', '+00:00')
                        datetime.fromisoformat(date_str)
                        # Keep as-is if valid
                except (ValueError, AttributeError):
                    logger.debug(f"{trial['nct_id']}: Invalid date in {field}: {trial[field]}")
                    trial[field] = None
        
        return trial
    
    def _clean_nested_arrays(self, trial: Dict) -> Dict:
        """Clean nested object arrays (conditions, interventions, etc.)."""
        nested_fields = [
            "conditions", "interventions", "sponsors", "facilities", 
            "design_outcomes", "age", "id_information",
            "browse_conditions", "browse_interventions", "design_groups",
            "adverse_events", "submissions", "documents"
        ]
        
        for field in nested_fields:
            if field not in trial:
                trial[field] = []
            elif trial[field] is None:
                trial[field] = []
            elif not isinstance(trial[field], list):
                logger.warning(f"{trial['nct_id']}: {field} is not a list, converting")
                trial[field] = [trial[field]] if trial[field] else []
            else:
                # Remove null entries and validate objects
                cleaned = []
                for item in trial[field]:
                    if item is not None and isinstance(item, dict):
                        # Remove entries with all null values
                        if any(v is not None and v != "" for v in item.values()):
                            cleaned.append(item)
                    elif item is not None and not isinstance(item, dict):
                        # If it's a simple value (like string in keywords), keep it
                        cleaned.append(item)
                trial[field] = cleaned
        
        # Special handling for keywords - flatten to strings
        if trial.get("keywords"):
            keywords = trial["keywords"]
            if isinstance(keywords, list):
                flat_keywords = []
                for kw in keywords:
                    if isinstance(kw, dict):
                        # Extract 'name' field if it's a dict
                        if kw.get('name') and kw['name'] != 'NA':
                            flat_keywords.append(str(kw['name']))
                    elif isinstance(kw, str) and kw and kw != 'NA':
                        flat_keywords.append(kw)
                trial["keywords"] = flat_keywords
        
        return trial
    
    def _convert_data_types(self, trial: Dict) -> Dict:
        """Convert fields to expected types."""
        
        # Integer fields - enrollment
        if trial.get("enrollment"):
            try:
                # Handle "None" strings and special cases
                if trial["enrollment"] in ["None", "NA", "", None]:
                    trial["enrollment"] = None
                else:
                    # Remove commas and convert to int
                    trial["enrollment"] = int(str(trial["enrollment"]).replace(",", ""))
            except (ValueError, TypeError):
                trial["enrollment"] = None
        
        # Boolean fields
        bool_fields = [
            "healthy_volunteers", "has_results", "has_dmc",
            "subject_masked", "caregiver_masked", "investigator_masked",
            "outcomes_assessor_masked"
        ]
        
        for field in bool_fields:
            if trial.get(field) is not None:
                if isinstance(trial[field], (int, float)):
                    trial[field] = bool(trial[field])
                elif isinstance(trial[field], str):
                    trial[field] = trial[field].lower() in ["true", "yes", "1"]
        
        # Integer count fields
        int_fields = ["number_of_arms", "number_of_groups", "document_count", "document_total_page_count"]
        for field in int_fields:
            if trial.get(field):
                try:
                    if trial[field] in ["None", "NA", "", None]:
                        trial[field] = None
                    else:
                        trial[field] = int(trial[field])
                except (ValueError, TypeError):
                    trial[field] = None
        
        return trial
    
    def _handle_missing_values(self, trial: Dict) -> Dict:
        """Set defaults for missing categorical fields."""
        
        # Keyword fields that shouldn't be empty strings
        keyword_fields = {
            "study_type": "NA",
            "phase": "NA",
            "overall_status": "UNKNOWN",
            "gender": "ALL",
            "allocation": "NA",
            "intervention_model": "NA",
            "observational_model": "NA",
            "primary_purpose": "NA",
            "masking": "NA"
        }
        
        for field, default in keyword_fields.items():
            if not trial.get(field) or trial[field] == "":
                trial[field] = default
        
        return trial
    
    def get_stats(self) -> Dict:
        """Return preprocessing statistics."""
        return self.stats
    
    def preprocess_batch(self, trials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Preprocess a batch of trial records.
        Returns list of cleaned records.
        """
        cleaned_trials = []
        
        for trial in trials:
            cleaned = self.preprocess_trial(trial)
            if cleaned:
                cleaned_trials.append(cleaned)
        
        return cleaned_trials
