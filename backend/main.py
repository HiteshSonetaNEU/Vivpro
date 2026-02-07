"""
FastAPI application for Clinical Trials Search.
"""

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import AsyncElasticsearch
from config import Config
from routers import search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global Elasticsearch client
es_client = None


async def connect_elasticsearch(max_retries=5, retry_delay=2) -> AsyncElasticsearch:
    """Connect to Elasticsearch with retry logic."""
    for attempt in range(max_retries):
        try:
            client = AsyncElasticsearch(
                [Config.ELASTICSEARCH_HOST],
                verify_certs=False
            )
            
            # Test connection
            if await client.ping():
                info = await client.info()
                logger.info(f"✓ Connected to Elasticsearch cluster: {info['cluster_name']}")
                logger.info(f"✓ Elasticsearch version: {info['version']['number']}")
                return client
            else:
                logger.warning(f"Elasticsearch ping failed (attempt {attempt + 1}/{max_retries})")
        except Exception as e:
            logger.warning(f"Failed to connect to Elasticsearch (attempt {attempt + 1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    raise ConnectionError("Failed to connect to Elasticsearch after maximum retries")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    global es_client
    
    # Startup
    logger.info("Starting Clinical Trials Search API...")
    try:
        es_client = await connect_elasticsearch()
        logger.info("✓ Application startup complete")
    except Exception as e:
        logger.error(f"✗ Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Clinical Trials Search API...")
    if es_client:
        await es_client.close()
        logger.info("✓ Elasticsearch connection closed")


# Initialize FastAPI app
app = FastAPI(
    title="Clinical Trials Search API",
    description="Intelligent search over clinical trials using NLP and Elasticsearch",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router)


@app.get("/")
async def root():
    """Root endpoint."""
    es_status = 'disconnected'
    if es_client:
        try:
            es_status = 'connected' if await es_client.ping() else 'disconnected'
        except:
            pass
    
    return {
        'message': 'Clinical Trials Search API',
        'version': '1.0.0',
        'status': 'running',
        'elasticsearch': es_status,
        'docs': '/docs',
        'endpoints': {
            'health': '/health',
            'status': '/api/status',
            'search': '/api/search',
            'trial': '/api/trial/{nct_id}',
            'filters': '/api/filters'
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        es_status = 'disconnected'
        if es_client:
            try:
                es_status = 'connected' if await es_client.ping() else 'disconnected'
            except:
                es_status = 'disconnected'
        
        health_status = {
            'status': 'healthy' if es_status == 'connected' else 'unhealthy',
            'elasticsearch': es_status,
            'timestamp': time.time()
        }
        
        if es_status != 'connected':
            raise HTTPException(status_code=503, detail="Elasticsearch unavailable")
        
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/api/status")
async def api_status():
    """API status endpoint with detailed information."""
    try:
        # Get ES cluster health
        cluster_health = None
        es_connected = False
        if es_client:
            try:
                cluster_health = await es_client.cluster.health()
                es_connected = await es_client.ping()
            except:
                pass
        
        # Get index stats
        index_stats = None
        if es_client:
            try:
                count_response = await es_client.count(index='clinical_trials')
                index_stats = {
                    'index_name': 'clinical_trials',
                    'document_count': count_response['count']
                }
            except:
                index_stats = {'error': 'Index not found or unavailable'}
        
        return {
            'api_version': '1.0.0',
            'status': 'operational',
            'elasticsearch': {
                'connected': es_connected,
                'cluster_health': cluster_health['status'] if cluster_health else None,
                'cluster_name': cluster_health['cluster_name'] if cluster_health else None
            },
            'index': index_stats,
            'openai': {
                'configured': bool(Config.OPENAI_API_KEY)
            },
            'timestamp': time.time()
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            'api_version': '1.0.0',
            'status': 'degraded',
            'error': str(e),
            'timestamp': time.time()
        }


def get_es_client() -> AsyncElasticsearch:
    """Get the Elasticsearch client instance."""
    if es_client is None:
        raise HTTPException(status_code=503, detail="Elasticsearch not connected")
    return es_client
