# 🧪 Intelligent Clinical Trials Search — Project Plan

## 1. Project Overview

**Goal:** Build a full-stack, production-ready application that enables intelligent search over **1,000+ clinical trial records** sourced from `clinical_trials.json`.

**Context:** 12-hour hackathon (~7–8 hours of build time). Evaluated by technical mentors and a non-technical CEO. Every technical decision must be justifiable.

**⚠️ Critical Mentor Feedback:** Implement data preprocessing & validation BEFORE ingesting into Elasticsearch (see Section 5).

---

## 2. Dataset Summary

| Property | Value |
|---|---|
| Total Records | 1,000 |
| Fields per Record | 64 |
| Study Types | `INTERVENTIONAL`, `OBSERVATIONAL` |
| Phases | `PHASE1`, `PHASE1/PHASE2`, `PHASE2`, `PHASE2/PHASE3`, `PHASE3`, `PHASE4`, `NA` |
| Statuses | `RECRUITING`, `NOT_YET_RECRUITING`, `ACTIVE_NOT_RECRUITING`, `COMPLETED`, `TERMINATED`, `SUSPENDED`, `WITHDRAWN`, `UNKNOWN` |
| Unique Sponsors | ~120 |
| Key Nested Fields | `conditions`, `interventions`, `sponsors`, `facilities`, `design_outcomes`, `adverse_events`, `keywords`, `age` |

### What does this mean?

**1,000 clinical trials** spanning different phases (early research to late-stage), covering multiple conditions and intervention types. Each trial has:
- **Structured metadata** (phase, status, enrollment count, dates, locations)
- **Text descriptions** (brief title, official title, detailed description, summaries)
- **Nested entities** (multiple conditions per trial, multiple interventions, multiple sponsors/facilities)
- **Outcome measures** (primary and secondary endpoints)

This rich structure allows us to:
- Search by free text ("breast cancer trials")
- Filter by structured criteria (Phase 2, Recruiting, specific sponsors)
- Find related trials based on conditions, interventions, or genes mentioned in descriptions
- Display geographic distribution via facilities data

---

## 3. Proposed Architecture

```
┌────────────────────────────────────────────────────────────┐
│                       FRONTEND                             │
│            React + TypeScript + Tailwind CSS               │
│  ┌────────────────────┐ ┌──────────────────────────────┐  │
│  │   Natural Language │ │   Results (Exact + Similar)  │  │
│  │     Search Bar     │ │   + Detail View              │  │
│  └────────────────────┘ └──────────────────────────────┘  │
└──────────────────────────┬─────────────────────────────────┘
                           │  REST API
┌──────────────────────────▼─────────────────────────────────┐
│                       BACKEND (FastAPI)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │             INTELLIGENT SEARCH API                  │   │
│  │  1. Receives natural language query                 │   │
│  │  2. Sends to OpenAI for entity extraction           │   │
│  │  3. Builds ES query from extracted entities         │   │
│  │  4. Executes search with exact + similarity fallback│   │
│  └────────────────┬───────────────────┬────────────────┘   │
│                   │                   │                     │
│         ┌─────────▼──────┐   ┌────────▼──────────┐         │
│         │  OpenAI API    │   │ Elasticsearch     │         │
│         │  (GPT-4/3.5)   │   │ Client            │         │
│         │  - Entity      │   │ - Query builder   │         │
│         │    extraction  │   │ - Aggregations    │         │
│         │  - Embeddings  │   │ - Similar search  │         │
│         └────────────────┘   └───────────────────┘         │
└────────────────────────────────────┬────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────┐
│               ELASTICSEARCH (Docker)                        │
│  - Full-text search with fuzzy matching                     │
│  - Nested queries for conditions/interventions/facilities   │
│  - Aggregations for facets                                  │
│  - Vector similarity search (optional embeddings)           │
└─────────────────────────────────────────────────────────────┘
```

### API Endpoint Design

**Q: Why do we need separate Search API, Filter API, and Detail API when users just type natural language?**

**A: Great question! Here's the breakdown:**

#### 1. **Intelligent Search API** (`POST /search`)
**Purpose:** The main endpoint that handles natural language queries.

**Example Request:**
```json
{
  "query": "List all Phase 2 trials for Breast Cancer associated with BRCA1 gene"
}
```

**What it does:**
1. **Sends query to OpenAI GPT** to extract structured entities:
   ```python
   {
     "phase": "PHASE2",
     "condition": "Breast Cancer",
     "gene": "BRCA1",
     "keywords": ["BRCA1", "breast cancer"]
   }
   ```

2. **Builds an Elasticsearch query** combining:
   - Exact filters (phase = PHASE2)
   - Text search (condition name = "Breast Cancer")
   - Keyword search (descriptions containing "BRCA1")

3. **Returns two result sets:**
   - **Exact matches** (trials that match all criteria)
   - **Similar matches** (if exact < 5, find related trials based on semantic similarity)

**Why this matters:** You don't manually apply filters — the LLM extracts them from your natural language query and applies them automatically.

#### 2. **Aggregations/Filter Metadata API** (`GET /filters`)
**Purpose:** Returns available filter options with counts (used to show what's available in the dataset).

**Example Response:**
```json
{
  "phases": {
    "PHASE1": 120,
    "PHASE2": 340,
    "PHASE3": 280,
    "PHASE4": 150
  },
  "statuses": {
    "RECRUITING": 450,
    "NOT_YET_RECRUITING": 200,
    "COMPLETED": 300
  },
  "top_conditions": [
    {"name": "Breast Cancer", "count": 85},
    {"name": "Diabetes", "count": 62}
  ]
}
```

**Why we need it:**
- **For the UI:** Shows users what data is available (even though they don't manually filter)
- **For validation:** Helps the LLM know what valid values are (if GPT extracts "Phase Two", we map it to "PHASE2")
- **For discovery:** Users can see "what's in the dataset?" before searching

#### 3. **Trial Detail API** (`GET /trials/{nct_id}`)
**Purpose:** Returns full details of a single trial when user clicks on a result.

**Example:** `GET /trials/NCT06890351`

**Why separate endpoint:**
- Search results show only **summary data** (title, phase, status, brief description)
- Detail view shows **everything** (full description, outcomes, facilities, sponsors, adverse events)
- Keeps search response fast and lightweight (not sending 64 fields × 1,000 trials)

---

### Summary: How the Flow Works

**User types:** *"List all Phase 2 trials for Breast Cancer associated with BRCA1 gene"*

1. Frontend sends query to `POST /search`
2. Backend calls OpenAI to parse → extracts `{phase: PHASE2, condition: Breast Cancer, gene: BRCA1}`
3. Backend builds Elasticsearch query:
   ```json
   {
     "bool": {
       "must": [
         {"term": {"phase": "PHASE2"}},
         {"nested": {"path": "conditions", "query": {"match": {"conditions.name": "Breast Cancer"}}}},
         {"multi_match": {"query": "BRCA1", "fields": ["brief_title", "brief_summaries_description", "keywords.name"]}}
       ]
     }
   }
   ```
4. ES returns exact matches (say, 3 results)
5. If < 5 results, backend runs a **similarity search** (relaxes filters or uses embeddings)
6. Returns `{exact: [...], similar: [...]}`
7. User clicks on a trial → Frontend calls `GET /trials/{nct_id}` for full details

**So we need all 3 APIs:**
- **Search API** = the brain (NL query → structured query → results)
- **Filters API** = metadata helper (what's available in the dataset?)
- **Detail API** = full record viewer (don't bloat search results)

### Why this stack?

| Decision | Justification |
|---|---|
| **Elasticsearch** | Purpose-built for full-text search. Supports fuzzy matching, synonym expansion, boosting, nested queries, and aggregations — all critical for clinical trial search. Far superior to SQL `LIKE` or basic Postgres FTS for this use case. |
| **FastAPI (Python)** | Async-first, automatic OpenAPI docs, Pydantic validation, fast to develop. Python ecosystem gives us easy access to NLP libraries if needed. |
| **React + TypeScript** | Component-based UI, type safety, massive ecosystem. Tailwind for rapid, consistent styling. |
| **Docker** | Elasticsearch runs cleanly in Docker. Compose file makes it one-command reproducible. |

---

## 4. Feature Roadmap (Priority Order)

### ✅ Phase 1 — Core (Hours 1–3) *Must Have*
1. **Docker Compose** with Elasticsearch 8.x
2. **Data ingestion script** — load all 1,000 records into ES with proper mapping
3. **Backend API** — FastAPI with:
   - `GET /search?q=...` — full-text search across `brief_title`, `official_title`, `brief_summaries_description`, `conditions.name`, `interventions.name`
   - `GET /trials/{nct_id}` — single trial detail
4. **Frontend** — search bar + results list + detail view

### ✅ Phase 2 — Smart Search (Hours 3–5) *Should Have*
5. **Faceted filtering** — phase, status, study type, sponsor, condition, intervention type
6. **Aggregations API** — return filter counts from ES
7. **Fuzzy matching** — handle typos (e.g., "diabetis" → "diabetes")
8. **Field boosting** — title matches rank higher than description matches
9. **Highlighting** — show matched terms in context in search results
10. **Pagination** — cursor-based or offset pagination

### ✅ Phase 3 — NLP & Intelligence (Hours 5–7) *Nice to Have*
11. **Synonym expansion** — map domain terms (e.g., "heart attack" ↔ "myocardial infarction")
12. **Auto-suggest / autocomplete** — suggest completions as user types
13. **Semantic search** (if time allows) — use a lightweight sentence-transformer to encode trial descriptions, then use ES `dense_vector` field + kNN for meaning-based retrieval
14. **"Similar Trials"** — given a trial, find related ones via more-like-this query

### ✅ Phase 4 — Polish (Hour 7–8) *Final Touch*
15. **Loading states, error handling, empty states** in UI
16. **Responsive design**
17. **Summary statistics dashboard** (counts by phase, status, condition — powered by ES aggregations)
18. **README + architecture diagram** for presentation

---

## 5. Data Preprocessing & Validation (Critical!)

**Mentor Feedback:** Handle data issues BEFORE ingesting into Elasticsearch.

### Why Preprocessing Matters

Real-world data is messy. Before indexing, we must:
- ✅ Validate required fields
- ✅ Handle missing/null values
- ✅ Sanitize malformed data
- ✅ Normalize inconsistent formats
- ✅ Log issues for debugging

**If we skip this:** Ingestion fails mid-way, or worse — bad data gets indexed and breaks search.

---

### Data Quality Issues We Expect

| Issue Type | Example | Impact |
|---|---|---|
| **Missing required fields** | No `nct_id` | Can't uniquely identify trial → skip record |
| **Null/empty nested arrays** | `conditions: null` | ES expects array → use `[]` |
| **Malformed dates** | `"2025-13-45"` | Invalid date → set to `null` |
| **Encoding issues** | `"Brest C\x00ancer"` | Null bytes crash ES → sanitize |
| **Wrong data types** | `enrollment: "540"` (string) | ES expects integer → convert |
| **Empty strings in keyword fields** | `phase: ""` | Use `"NA"` or `null` |
| **Nested objects with missing keys** | `{"name": null}` in conditions | Remove or fill with default |
| **Very long text fields** | Description > 32KB | Truncate (ES has size limits) |

---

### Preprocessing Pipeline

```python
# backend/data_preprocessing.py

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

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
            "detailed_description", "intervention_model_description"
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
                        # Handle ISO format
                        datetime.fromisoformat(trial[field].replace('Z', '+00:00'))
                    # Keep as-is if valid
                except (ValueError, AttributeError):
                    logger.warning(f"{trial['nct_id']}: Invalid date in {field}: {trial[field]}")
                    trial[field] = None
        
        return trial
    
    def _clean_nested_arrays(self, trial: Dict) -> Dict:
        """Clean nested object arrays (conditions, interventions, etc.)."""
        nested_fields = [
            "conditions", "interventions", "sponsors", "facilities", 
            "design_outcomes", "age", "keywords", "id_information",
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
                trial[field] = cleaned
        
        return trial
    
    def _convert_data_types(self, trial: Dict) -> Dict:
        """Convert fields to expected types."""
        
        # Integer fields
        if trial.get("enrollment"):
            try:
                # Handle "None" strings
                if trial["enrollment"] in ["None", "NA", ""]:
                    trial["enrollment"] = None
                else:
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
                    if trial[field] == "None":
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


# Usage in ingest.py
def ingest_data():
    preprocessor = DataPreprocessor()
    
    with open("clinical_trials.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} records from JSON")
    
    # Preprocess all records
    cleaned_trials = []
    for trial in data:
        cleaned = preprocessor.preprocess_trial(trial)
        if cleaned:
            cleaned_trials.append(cleaned)
    
    # Log statistics
    stats = preprocessor.get_stats()
    logger.info(f"""
    Preprocessing Complete:
    - Total records: {stats['total_records']}
    - Valid records: {stats['valid_records']}
    - Skipped records: {stats['skipped_records']}
    - Warnings: {len(stats['warnings'])}
    """)
    
    # Bulk index to ES
    bulk_index_to_elasticsearch(cleaned_trials)
```

---

### Preprocessing Checklist

Before ingestion, we must handle:

- ✅ **Required field validation** (nct_id must exist)
- ✅ **Text sanitization** (remove null bytes, control characters)
- ✅ **Text truncation** (ES has 32KB limit per field)
- ✅ **Date validation** (parse ISO dates, set invalid to null)
- ✅ **Nested array validation** (ensure all nested fields are arrays, not null)
- ✅ **Remove empty objects** (e.g., `{name: null}` in conditions)
- ✅ **Type conversion** (enrollment string → integer)
- ✅ **Boolean normalization** (1.0 → true, "Yes" → true)
- ✅ **Empty string handling** (phase: "" → "NA")
- ✅ **Logging & statistics** (track how many records were cleaned/skipped)

---

### Testing Preprocessing

```python
# Quick test before full ingestion
sample = data[0]
print("Original:", sample.get('enrollment'), type(sample.get('enrollment')))

cleaned = preprocessor.preprocess_trial(sample)
print("Cleaned:", cleaned.get('enrollment'), type(cleaned.get('enrollment')))

# Check nested arrays
print("Conditions:", cleaned.get('conditions'))
print("Interventions:", cleaned.get('interventions'))
```

---

## 6. Elasticsearch Index Design

### Mapping Strategy

```json
{
  "mappings": {
    "properties": {
      "nct_id":                { "type": "keyword" },
      "brief_title":           { "type": "text", "analyzer": "english", "fields": { "raw": { "type": "keyword" } } },
      "official_title":        { "type": "text", "analyzer": "english" },
      "brief_summaries_description": { "type": "text", "analyzer": "english" },
      "detailed_description":  { "type": "text", "analyzer": "english" },
      "overall_status":        { "type": "keyword" },
      "phase":                 { "type": "keyword" },
      "study_type":            { "type": "keyword" },
      "source":                { "type": "keyword" },
      "enrollment":            { "type": "integer" },
      "gender":                { "type": "keyword" },
      "minimum_age":           { "type": "text" },
      "maximum_age":           { "type": "text" },
      "start_date":            { "type": "date" },
      "completion_date":       { "type": "date" },
      "conditions":            { "type": "nested", "properties": { "name": { "type": "text", "fields": { "raw": { "type": "keyword" } } } } },
      "interventions":         { "type": "nested", "properties": {
        "intervention_type":   { "type": "keyword" },
        "name":                { "type": "text", "fields": { "raw": { "type": "keyword" } } },
        "description":         { "type": "text" }
      }},
      "sponsors":              { "type": "nested", "properties": { "name": { "type": "keyword" } } },
      "facilities":            { "type": "nested", "properties": {
        "city":                { "type": "keyword" },
        "state":               { "type": "keyword" },
        "country":             { "type": "keyword" }
      }},
      "keywords":              { "type": "nested", "properties": { "name": { "type": "text", "fields": { "raw": { "type": "keyword" } } } } }
    }
  }
}
```

### Why these choices?
- **`text` with `english` analyzer** → stemming, stopword removal, case-insensitive search
- **`keyword` subfields (`.raw`)** → exact match for aggregations/facets
- **`nested` for arrays of objects** → prevents cross-object matching (e.g., matching city from one facility with state from another)
- **`keyword` for categorical fields** → efficient filtering and aggregation

### Detailed Explanation of Mapping Strategy

#### 1. **Why `text` vs `keyword`?**
- **`text` fields** are **analyzed** → tokenized, lowercased, stemmed
  - Example: "Running Studies" → tokens: `["run", "studi"]`
  - Supports **fuzzy search**, **partial matching**, **synonyms**
  - Used for: titles, descriptions, condition names, intervention names
  
- **`keyword` fields** are **not analyzed** → stored exactly as-is
  - Example: "PHASE2" → stored as `"PHASE2"` (not lowercased)
  - Supports **exact matching**, **sorting**, **aggregations** (counting)
  - Used for: phase, status, study_type, nct_id

#### 2. **Why `nested` type for arrays?**

**Problem:** Default arrays in ES are "flattened" — object boundaries are lost.

**Example without `nested`:**
```json
{
  "facilities": [
    {"city": "Boston", "state": "MA"},
    {"city": "Seattle", "state": "WA"}
  ]
}
```
↓ ES flattens to:
```json
{
  "facilities.city": ["Boston", "Seattle"],
  "facilities.state": ["MA", "WA"]
}
```
Now a query for `city=Seattle AND state=MA` would **incorrectly match** (cross-object match).

**Solution: `nested` type** maintains object boundaries:
```json
{
  "type": "nested",
  "properties": {
    "city": {"type": "keyword"},
    "state": {"type": "keyword"}
  }
}
```
Now `city=Seattle AND state=MA` correctly returns **no match**.

**We use `nested` for:**
- `conditions` — multiple conditions per trial
- `interventions` — multiple drugs/procedures per trial
- `facilities` — multiple locations per trial
- `sponsors` — multiple funding organizations

#### 3. **Why dual mapping: `text` + `.raw` subfield?**

For fields like `brief_title`, we want **both** search and aggregation:

```json
"brief_title": {
  "type": "text",
  "analyzer": "english",
  "fields": {
    "raw": {"type": "keyword"}
  }
}
```

- **`brief_title` (text)** → used for search queries: `"asthma"` matches "Asthma Study in Adults"
- **`brief_title.raw` (keyword)** → used for exact sorting or grouping: "Asthma Study in Adults" (exact string)

**Use case:** Search by condition name (`text`), but aggregate/count unique conditions (`.raw`).

#### 4. **Why `english` analyzer?**

The `english` analyzer performs:
1. **Lowercasing:** "Breast" → "breast"
2. **Stemming:** "running" → "run", "studies" → "studi"
3. **Stop word removal:** "the", "a", "an" are ignored

**Benefit:** User searches "cancer treatment" → matches "Cancer Treatment Study" AND "treating cancers"

#### 5. **Why `date` type for date fields?**

Stored as milliseconds since epoch → enables range queries:
```json
{
  "range": {
    "start_date": {
      "gte": "2025-01-01",
      "lte": "2025-12-31"
    }
  }
}
```
Also supports date math: `"gte": "now-1y"` (trials starting in the last year)

---

## 7. Why We SHOULD Use OpenAI LLM for NLP (Updated Decision)

### The Mentor's Insight: Exact Match → Similar Fallback

**Use Case:** 
1. User searches: *"List all Phase 2 trials for Breast Cancer associated with BRCA1 gene"*
2. If **exact matches exist** → display them prominently
3. If **no exact matches OR < 5 results** → show **similar trials** (relaxed criteria or semantic similarity)

### Why LLM is the RIGHT Choice Here

| Without LLM | With OpenAI LLM |
|---|---|
| **Regex/Rules-based parsing** is brittle: <br>- "Phase 2" vs "Phase II" vs "phase two" vs "second phase" <br>- "breast cancer" vs "mammary carcinoma" vs "ductal breast cancer" <br>- Gene names: BRCA1, BRCA-1, BRCA1/2 | **GPT-4 understands context:** <br>- Handles all variations naturally <br>- Extracts structured entities from free text <br>- Maps synonyms (breast cancer ↔ mammary carcinoma) |
| **Hard to expand:** Adding new entity types (e.g., "trials in California", "recruiting in 2025") requires code changes | **Flexible prompting:** Add new entity types to the prompt, no code changes |
| **No semantic understanding:** Can't find "similar" trials based on meaning | **Embeddings for similarity:** Generate embeddings for trial descriptions, find semantically similar trials |
| **Difficult user queries fail:** <br>- "Show me cancer trials near Boston" (location parsing?) <br>- "Diabetes studies for elderly patients" (age parsing?) | **Natural language → structured query:** <br>- "near Boston" → filter facilities with city/state <br>- "elderly" → filter age criteria |

### Architecture with OpenAI

```python
# Example flow in backend
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_query(user_query: str):
    """Use GPT to extract structured entities from natural language."""
    
    prompt = f"""
    Extract clinical trial search parameters from this query: "{user_query}"
    
    Return JSON with these fields (null if not mentioned):
    - phase: one of [PHASE1, PHASE2, PHASE3, PHASE4, PHASE1/PHASE2, PHASE2/PHASE3]
    - condition: medical condition name
    - intervention: drug/treatment name
    - gene: gene name (e.g., BRCA1, KRAS)
    - status: one of [RECRUITING, NOT_YET_RECRUITING, COMPLETED, etc.]
    - location: city or state
    - keywords: list of important terms to search in descriptions
    
    Example: "Phase 2 breast cancer trials with Herceptin" →
    {{"phase": "PHASE2", "condition": "breast cancer", "intervention": "Herceptin", "keywords": ["breast cancer", "Herceptin"]}}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Fast and cheap
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

# Example usage
entities = parse_query("List all Phase 2 trials for Breast Cancer associated with BRCA1 gene")
# Returns: {
#   "phase": "PHASE2",
#   "condition": "Breast Cancer",
#   "gene": "BRCA1",
#   "keywords": ["breast cancer", "BRCA1"]
# }

# Now build ES query from entities
es_query = build_elasticsearch_query(entities)
results = es_client.search(index="clinical_trials", body=es_query)

# If exact matches < 5, find similar trials
if results['hits']['total']['value'] < 5:
    similar = find_similar_trials(entities, relax_filters=True)
    return {"exact": results, "similar": similar}
```

### Cost & Performance Analysis

| Aspect | Value |
|---|---|
| **Model** | `gpt-4o-mini` (fast, cheap) or `gpt-3.5-turbo` |
| **Cost per query** | ~$0.0001–0.0003 (fraction of a cent) |
| **Latency** | ~200-500ms (acceptable for hackathon) |
| **Rate limits** | 10,000 requests/min on paid tier (more than enough) |
| **Reliability** | OpenAI uptime > 99.9%, we have API key → low risk |

**For 1,000 queries at the hackathon:** ~$0.10–0.30 total cost. Negligible.

### Similarity Fallback Strategy

When exact matches are insufficient, we have **two approaches**:

#### **Option A: Relaxed Elasticsearch Query (Fast)**
Progressively remove filters:
1. Try exact match (phase + condition + gene)
2. If < 5 results → remove gene filter, keep phase + condition
3. If still < 5 → remove phase, keep only condition
4. Sort by relevance score

**Pros:** Fast (no additional API calls), deterministic
**Cons:** Less "intelligent" — just removes filters

#### **Option B: Semantic Embeddings (Smarter)**
Use OpenAI embeddings to find trials with similar *meaning*:

```python
def find_similar_by_embeddings(query: str, top_k=10):
    # Get embedding for user query
    query_embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding
    
    # Search ES using vector similarity (kNN)
    es_query = {
        "knn": {
            "field": "description_embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": 100
        }
    }
    
    return es_client.search(index="clinical_trials", body=es_query)
```

**Setup required:** Pre-compute embeddings for all 1,000 trial descriptions at ingestion time.

**Pros:** Truly semantic — "blood pressure" finds "hypertension" trials
**Cons:** Requires pre-processing step (adds 10 min to setup)

### Recommendation: Use Both

1. **Primary:** OpenAI GPT for query parsing (entity extraction)
2. **Exact match:** Elasticsearch with extracted filters
3. **Fallback 1:** Relaxed ES query (remove filters progressively)
4. **Fallback 2 (if time):** Semantic embeddings for "similar trials" feature

### Why This is Better Than ES-Only NLP

| Feature | ES-Only (Analyzers + Synonyms) | ES + OpenAI LLM |
|---|---|---|
| **Entity extraction** | Requires regex patterns, brittle | Natural language understanding |
| **Synonym handling** | Manual curation (time-consuming) | Built-in medical knowledge |
| **Complex queries** | Limited (can't parse "near Boston" or "elderly patients") | Handles any natural language |
| **Similarity search** | More-like-this (keyword-based) | Semantic embeddings (meaning-based) |
| **Development time** | Longer (write parsing rules) | Faster (prompt engineering) |
| **Maintainability** | Hard (add new entity types = code changes) | Easy (update prompt) |
| **Demo impact** | "Works okay" | "Wow, it understands me!" |

### Risk Mitigation

**Q: What if OpenAI API goes down during the hackathon?**

**A: Fallback to basic ES search:**
```python
def search_trials(query: str):
    try:
        # Try LLM parsing
        entities = parse_query_with_openai(query)
        es_query = build_query_from_entities(entities)
    except Exception as e:
        logger.error(f"OpenAI failed: {e}")
        # Fallback: simple multi-match query
        es_query = {
            "multi_match": {
                "query": query,
                "fields": ["brief_title^3", "official_title^2", "brief_summaries_description", 
                           "conditions.name^2", "interventions.name^2", "keywords.name"]
            }
        }
    
    return es_client.search(index="clinical_trials", body=es_query)
```

**We always have a working search**, even if LLM fails.

---

## 8. Updated Risk Register & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| **OpenAI API rate limit or downtime** | Search fails | Low | Fallback to basic ES multi-match query. Always have a working search. Cache common queries. |
| **OpenAI parsing returns invalid entities** | Wrong search results | Medium | Validate extracted entities against known values (phases, statuses). Default to keyword search if validation fails. |
| **Elasticsearch won't start in Docker** | Blocks everything | Medium | Pre-pull image. Have a fallback: load data into SQLite + use basic FTS. |
| **Data ingestion fails (malformed records)** | Partial index | Medium | Validate + sanitize each record before indexing. Log failures. Use `bulk` API with error tolerance. |
| **Frontend ↔ Backend CORS issues** | UI can't call API | High | Configure CORS in FastAPI from the start (`allow_origins=["*"]` for dev). |
| **ES memory issues on laptop** | Crashes mid-demo | Medium | Limit ES JVM heap to 512MB in Docker Compose. 1,000 docs is tiny — should be fine. |
| **Embedding generation too slow** | Delays ingestion | Low | Only generate embeddings if time permits. Not critical for core functionality. Use batch API for faster processing. |
| **Scope creep** | Don't finish | High | Strict phase gates. Phase 1 complete before touching Phase 2. |

---

## 9. Folder Structure (Proposed)

```
vivpro/
├── docker-compose.yml          # ES + (optionally) backend
├── clinical_trials.json        # Source data
├── backend/
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # ES connection config + OpenAI API key
│   ├── models.py               # Pydantic schemas
│   ├── es_client.py            # Elasticsearch client wrapper
│   ├── data_preprocessing.py   # Data cleaning & validation (NEW!)
│   ├── openai_service.py       # OpenAI query parsing + embeddings
│   ├── query_builder.py        # Build ES queries from extracted entities
│   ├── ingest.py               # Data loading script (uses preprocessing)
│   ├── routers/
│   │   ├── search.py           # Intelligent search endpoint
│   │   └── trials.py           # Single trial detail + metadata
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ResultsList.tsx
│   │   │   ├── TrialDetail.tsx
│   │   │   ├── Filters.tsx
│   │   │   └── Dashboard.tsx
│   │   ├── hooks/
│   │   │   └── useSearch.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── trial.ts
│   └── tailwind.config.js
├── PLAN.md                     # This file
└── README.md                   # Final documentation
```

---

## 10. Updated Hour-by-Hour Execution Plan

| Hour | Goal | Deliverable | Checkpoint |
|---|---|---|---|
| **1** | Infra + Data Preprocessing + Ingestion | ES running in Docker, **data cleaning/validation implemented**, all records preprocessed and ingested with proper mapping, basic query works in Kibana/curl | Can search "asthma" via curl and get results. Preprocessing logs show stats (valid/skipped records). |
| **2** | Backend API + OpenAI Integration | FastAPI with OpenAI query parsing, `/search` endpoint that extracts entities and queries ES | Swagger UI: send "Phase 2 cancer trials" → returns structured entities + results |
| **3** | Frontend Shell | React app with search bar, results display (exact + similar sections), basic detail view | End-to-end: type query → see exact matches → see similar suggestions → click for details |
| **4** | Smart Search Features | Fuzzy matching, highlighting, field boosting, fallback logic (exact → relaxed → similar) | Search with typos works. Empty exact results show similar trials. |
| **5** | Filters & Metadata API | Aggregations endpoint for filter counts, UI shows available phases/statuses/conditions | `/filters` endpoint returns counts. UI displays dataset overview. |
| **6** | Semantic Embeddings (if time) | Pre-compute OpenAI embeddings for trials, implement vector similarity search | "blood pressure" finds "hypertension" trials via semantic matching |
| **7** | Polish + Dashboard | Loading states, error handling, empty states, stats dashboard, responsive design | Professional look. Handles API failures gracefully. No crashes on edge cases. |
| **8** | Presentation Prep | README with architecture diagram, demo script, practice defending decisions | Ready to present. Can explain every tech choice. Demo flows smoothly. |

---

## 11. Key Technical Decisions to Defend

0. **"Why preprocess data before ingesting?"**
   → Real-world data is messy. Without preprocessing: (1) Ingestion fails on malformed records, (2) Bad data gets indexed and breaks search, (3) Inconsistent data types cause query errors, (4) Null bytes crash Elasticsearch. Preprocessing ensures data quality, logs issues for debugging, and guarantees reliable search. **Production-grade practice.**

1. **"Why Elasticsearch instead of PostgreSQL full-text search?"**
   → ES gives us fuzzy matching, nested document queries (for multi-value fields like conditions/interventions), aggregations for facets, highlighting, and optional vector search — all out of the box. Postgres FTS would require custom implementations for each. ES is purpose-built for this use case.

2. **"Why FastAPI instead of Django/Flask/Express?"**
   → Async-first for concurrent ES and OpenAI I/O, automatic OpenAPI docs (great for demo), Pydantic validation catches bad data early. Python matches the data science/ML ecosystem. We can make both ES and OpenAI calls concurrently without blocking.

3. **"Why use OpenAI instead of just Elasticsearch analyzers?"**
   → Natural language query understanding requires **entity extraction** and **context understanding**. OpenAI GPT can parse "Phase 2 breast cancer trials with BRCA1 gene" into structured filters automatically. Writing regex/rule-based parsers for all query variations is brittle and time-consuming. LLM gives us flexibility and handles medical terminology naturally. Cost is negligible (~$0.0001/query).

4. **"What about OpenAI API reliability? What if it goes down?"**
   → We have a **fallback mechanism**: if OpenAI fails, we default to a basic Elasticsearch multi-match query across all text fields. The search always works, just less "intelligent" without entity extraction. We also cache OpenAI responses for common queries to reduce API calls.

5. **"How do you determine 'similar' trials when exact matches are insufficient?"**
   → **Two-tier approach:**
   - **Tier 1 (Fast):** Progressively relax filters (remove gene → remove phase → keep only condition)
   - **Tier 2 (Smart, if time):** Use OpenAI embeddings for semantic similarity — pre-compute embeddings for all trial descriptions, then do vector search for semantically related trials
   Both are sorted by relevance score from Elasticsearch.

6. **"How would this scale to millions of records?"**
   → ES is horizontally scalable (add shards/nodes). Our index mapping is already production-grade. We'd add:
   - **Caching layer** (Redis) for common queries and OpenAI responses
   - **Index aliases** for zero-downtime reindexing
   - **Pagination** with search_after cursors (already planned)
   - **Rate limiting** on OpenAI calls with local fallback
   - **Background job queue** for embedding generation

7. **"Why return both 'exact' and 'similar' results?"**
   → **User experience:** If a user searches for a very specific trial (Phase 2 + rare condition + specific gene), there might be 0-2 exact matches. Showing "no results" is a dead end. By also showing *similar* trials (e.g., same condition, different phase), we help users **discover alternatives** and understand what's available in the dataset. This is a core hackathon mentor suggestion.

8. **"What about data freshness in production?"**
   → In production, we'd set up a **scheduled pipeline** (Airflow/cron) to:
   - Pull latest trial data from ClinicalTrials.gov API
   - Detect changes (new trials, updated statuses)
   - Upsert into ES (using nct_id as unique key)
   - Regenerate embeddings for changed trials
   - Use ES index aliases to swap indices atomically
   The current bulk ingest script is the seed for that pipeline.

---

## 11. Fallback Plan

If Elasticsearch becomes a blocker:

1. **Fallback A:** Use **SQLite + FTS5** — Python stdlib, no Docker needed. Loses facets/fuzzy but basic search works.
2. **Fallback B:** Use **Typesense** — simpler to set up than ES, has typo tolerance and facets built in, single binary.
3. **Fallback C:** In-memory search with **Whoosh** (pure Python search library). Last resort but guarantees something works.

The key principle: **always have a working demo**, even if it's simpler than planned.
