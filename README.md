# Clinical Trials Search Application

Intelligent search application for clinical trial data using Elasticsearch, OpenAI, and Flask.

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- OpenAI API key

### Setup

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```
   
2. **Add your OpenAI API key to `.env`:**
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **Check service health:**
   ```bash
   # Check Elasticsearch
   curl http://localhost:9200/_cluster/health
   
   # Check Flask API
   curl http://localhost:5000/health
   ```

### Services

- **Elasticsearch**: http://localhost:9200
- **Flask API**: http://localhost:5000

### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Remove volumes (clean slate)
docker-compose down -v
```

## Project Structure

```
vivpro/
├── backend/
│   ├── Dockerfile              # Flask API Docker image
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # Flask application
│   ├── config.py               # Configuration
│   ├── data_preprocessing.py   # (to be created)
│   ├── openai_service.py       # (to be created)
│   └── query_builder.py        # (to be created)
├── clinical_trials.json        # Source data
├── docker-compose.yml          # Docker orchestration
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
├── PLAN.md                     # Project plan
├── CONTEXT.md                  # Implementation guide
└── README.md                   # This file
```

## Next Steps

1. Implement data preprocessing (`backend/data_preprocessing.py`)
2. Implement OpenAI service (`backend/openai_service.py`)
3. Implement query builder (`backend/query_builder.py`)
4. Create Elasticsearch index with mapping
5. Ingest preprocessed data
6. Implement search endpoints
7. Build frontend (React)

## Documentation

- **PLAN.md**: Comprehensive project plan with architecture
- **CONTEXT.md**: Implementation guide with code examples
- **ANSWERS_TO_QUESTIONS.md**: Design decisions explained
- **QUICK_ANSWERS.md**: Recent clarifications
- **README_FIRST.md**: Navigation guide

## Development

### API Endpoints (Current)

- `GET /` - API information
- `GET /health` - Health check

### API Endpoints (Planned)

- `POST /api/search` - Natural language search
- `GET /api/trial/<nct_id>` - Trial details
- `GET /api/filters` - Available filter options
