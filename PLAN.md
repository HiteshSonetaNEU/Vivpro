# 🧪 Intelligent Clinical Trials Search — Project Plan

## 1. Project Overview

**Goal:** Build a full-stack, production-ready application that enables intelligent search over **1,000 clinical trial records** sourced from `clinical_trials.json`.

**Context:** 12-hour hackathon (~7–8 hours of build time). Evaluated by technical mentors and a non-technical CEO. Every technical decision must be justifiable.

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

---

## 3. Proposed Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                         │
│         React + TypeScript + Tailwind CSS           │
│  ┌───────────┐ ┌──────────┐ ┌────────────────────┐ │
│  │ Search Bar│ │ Filters  │ │ Results + Detail   │ │
│  └───────────┘ └──────────┘ └────────────────────┘ │
└────────────────────┬────────────────────────────────┘
                     │  REST API
┌────────────────────▼────────────────────────────────┐
│                   BACKEND                           │
│             FastAPI (Python)                        │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ Search API  │ │ Filter API   │ │ Detail API   │ │
│  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘ │
│         │               │                │         │
│  ┌──────▼───────────────▼────────────────▼───────┐ │
│  │          Elasticsearch Client                 │ │
│  └──────────────────┬───────────────────────────-┘ │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              ELASTICSEARCH (Docker)                 │
│         Full-text + Structured Search               │
│         Fuzzy matching, Synonyms, Aggregations      │
└─────────────────────────────────────────────────────┘
```

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

## 5. Elasticsearch Index Design

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

---

## 6. Do We Need an LLM for NLP?

**Short answer: Not necessarily, but it depends on the depth of "intelligent" search.**

| Approach | When to Use | Tradeoff |
|---|---|---|
| **Elasticsearch analyzers + synonyms** | Handles 80% of "smart" search needs (stemming, fuzzy, synonyms). Zero latency cost. | Must manually curate synonym lists. |
| **Sentence Transformers (e.g., `all-MiniLM-L6-v2`)** | For true semantic search — "find trials about blood pressure" matches "hypertension". ~80MB model, fast inference. | Adds complexity. Need to pre-compute embeddings. |
| **OpenAI / LLM API** | For natural language query understanding (e.g., "Show me Phase 3 cancer trials in California recruiting adults"). | Adds latency (~1–2s), API cost, external dependency. Risky for hackathon reliability. |

### Recommendation
- **Start with ES-native NLP** (analyzers, synonyms, fuzzy) — this is fast, reliable, and impressive.
- **Add sentence-transformer embeddings** only if Phase 1–2 are done early. Use `all-MiniLM-L6-v2` — it runs locally, is ~80MB, and encodes in <50ms per query.
- **Skip LLM API calls** unless you have a specific feature that needs it (e.g., natural language → structured query translation). The risk of API downtime or rate limits during a hackathon is not worth it.

---

## 7. Risk Register & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| **Elasticsearch won't start in Docker** | Blocks everything | Medium | Pre-pull image. Have a fallback: load data into SQLite + use basic FTS. |
| **Data ingestion fails (malformed records)** | Partial index | Medium | Validate + sanitize each record before indexing. Log failures. Use `bulk` API with error tolerance. |
| **Frontend ↔ Backend CORS issues** | UI can't call API | High | Configure CORS in FastAPI from the start (`allow_origins=["*"]` for dev). |
| **ES memory issues on laptop** | Crashes mid-demo | Medium | Limit ES JVM heap to 512MB in Docker Compose. 1,000 docs is tiny — should be fine. |
| **Semantic search model too slow** | Bad UX | Low | Pre-compute all 1,000 embeddings at ingestion. Only encode the query at search time. |
| **Scope creep** | Don't finish | High | Strict phase gates. Phase 1 complete before touching Phase 2. |

---

## 8. Folder Structure (Proposed)

```
vivpro/
├── docker-compose.yml          # ES + (optionally) backend
├── clinical_trials.json        # Source data
├── backend/
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # ES connection config
│   ├── models.py               # Pydantic schemas
│   ├── es_client.py            # Elasticsearch client wrapper
│   ├── ingest.py               # Data loading script
│   ├── routers/
│   │   ├── search.py           # Search + filter endpoints
│   │   └── trials.py           # Single trial detail
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

## 9. Hour-by-Hour Execution Plan

| Hour | Goal | Deliverable | Checkpoint |
|---|---|---|---|
| **1** | Infra + Data | ES running in Docker, data ingested, basic query works in Kibana/curl | Can search "asthma" via curl and get results |
| **2** | Backend API | FastAPI with `/search` and `/trials/{id}` endpoints | Swagger UI shows working endpoints |
| **3** | Frontend Shell | React app with search bar, results list, basic detail view | End-to-end flow: type query → see results → click → see detail |
| **4** | Filters + Facets | Sidebar filters with counts (phase, status, condition) | Filter by "PHASE3" + "RECRUITING" narrows results |
| **5** | Smart Search | Fuzzy matching, highlighting, field boosting, synonym support | Searching "diabetis" returns diabetes trials, matched terms highlighted |
| **6** | NLP Enhancement | Autocomplete + (if time) semantic vector search | Type "can" → suggests "cancer". Semantic: "blood pressure" finds "hypertension" |
| **7** | Polish + Dashboard | Loading states, error handling, stats dashboard, responsive | Professional look. No crashes on edge cases. |
| **8** | Present | README, architecture diagram, rehearse demo | Ready to present and defend decisions |

---

## 10. Key Technical Decisions to Defend

1. **"Why Elasticsearch instead of PostgreSQL full-text search?"**
   → ES gives us fuzzy matching, synonym dictionaries, nested document queries, aggregations for facets, highlighting, and optional vector search — all out of the box. Postgres FTS would require custom implementations for each.

2. **"Why FastAPI instead of Django/Flask/Express?"**
   → Async-first for ES I/O, automatic OpenAPI docs (great for demo), Pydantic validation catches bad data early. Python matches the data science ecosystem if we need NLP.

3. **"Why not use ChatGPT/OpenAI for search?"**
   → External API dependency is risky at a hackathon (rate limits, downtime). ES-native NLP (analyzers, synonyms, fuzzy) handles 80% of "intelligent" search without any external dependency. We can add a local sentence-transformer model for semantic search with zero API risk.

4. **"How would this scale to millions of records?"**
   → ES is horizontally scalable (add shards/nodes). Our index mapping is already production-grade. We'd add index aliases for zero-downtime reindexing, and caching at the API layer.

5. **"What about data freshness?"**
   → In production, we'd set up a scheduled pipeline (Airflow/cron) to pull from ClinicalTrials.gov API and upsert into ES. The current bulk ingest script is the seed for that pipeline.

---

## 11. Fallback Plan

If Elasticsearch becomes a blocker:

1. **Fallback A:** Use **SQLite + FTS5** — Python stdlib, no Docker needed. Loses facets/fuzzy but basic search works.
2. **Fallback B:** Use **Typesense** — simpler to set up than ES, has typo tolerance and facets built in, single binary.
3. **Fallback C:** In-memory search with **Whoosh** (pure Python search library). Last resort but guarantees something works.

The key principle: **always have a working demo**, even if it's simpler than planned.
