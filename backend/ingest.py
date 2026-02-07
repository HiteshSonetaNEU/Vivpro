"""
Data ingestion script for clinical trials.
Loads, preprocesses, and indexes data into Elasticsearch.
"""

import json
import logging
import sys
from elasticsearch import Elasticsearch, helpers
from config import Config
from data_preprocessing import DataPreprocessor
from es_mapping import CLINICAL_TRIALS_MAPPING

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_clinical_trials(file_path: str) -> list:
    """Load clinical trials data from JSON file."""
    logger.info(f"Loading data from {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✓ Loaded {len(data)} records from JSON")
        return data
    except FileNotFoundError:
        logger.error(f"✗ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"✗ Invalid JSON format: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Error loading file: {e}")
        sys.exit(1)


def create_index(es_client: Elasticsearch, index_name: str) -> bool:
    """Create Elasticsearch index with mapping."""
    try:
        # Delete existing index if it exists
        if es_client.indices.exists(index=index_name):
            logger.warning(f"Index '{index_name}' already exists. Deleting...")
            es_client.indices.delete(index=index_name)
            logger.info(f"✓ Deleted existing index")
        
        # Create new index with mapping
        es_client.indices.create(index=index_name, body=CLINICAL_TRIALS_MAPPING)
        logger.info(f"✓ Created index '{index_name}' with mapping")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to create index: {e}")
        return False


def bulk_index_trials(es_client: Elasticsearch, index_name: str, trials: list) -> dict:
    """Bulk index trials into Elasticsearch."""
    logger.info(f"Starting bulk indexing of {len(trials)} records...")
    
    # Prepare bulk actions
    actions = [
        {
            "_index": index_name,
            "_id": trial["nct_id"],
            "_source": trial
        }
        for trial in trials
    ]
    
    try:
        # Perform bulk indexing
        success_count, errors = helpers.bulk(
            es_client,
            actions,
            stats_only=False,
            raise_on_error=False,
            chunk_size=500
        )
        
        # Count failures if any
        failed_count = len(errors) if errors else 0
        
        logger.info(f"✓ Bulk indexing complete: {success_count} successful, {failed_count} failed")
        
        if errors:
            logger.warning(f"First error: {errors[0] if errors else 'None'}")
        
        # Refresh index to make documents searchable immediately
        es_client.indices.refresh(index=index_name)
        logger.info(f"✓ Index refreshed")
        
        return {
            "success": success_count,
            "failed": failed_count
        }
        
    except Exception as e:
        logger.error(f"✗ Bulk indexing failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": 0, "failed": len(trials)}


def verify_ingestion(es_client: Elasticsearch, index_name: str):
    """Verify data was indexed correctly."""
    logger.info("Verifying ingestion...")
    
    try:
        # Get index stats
        count = es_client.count(index=index_name)
        total_docs = count['count']
        logger.info(f"✓ Total documents in index: {total_docs}")
        
        # Sample search
        sample_query = {
            "size": 1,
            "query": {"match_all": {}}
        }
        result = es_client.search(index=index_name, body=sample_query)
        
        if result['hits']['total']['value'] > 0:
            sample_doc = result['hits']['hits'][0]['_source']
            logger.info(f"✓ Sample document NCT ID: {sample_doc.get('nct_id', 'N/A')}")
            logger.info(f"✓ Sample title: {sample_doc.get('brief_title', 'N/A')[:100]}...")
        
        # Test search by condition
        test_query = {
            "size": 5,
            "query": {
                "nested": {
                    "path": "conditions",
                    "query": {
                        "match": {"conditions.name": "cancer"}
                    }
                }
            }
        }
        cancer_results = es_client.search(index=index_name, body=test_query)
        logger.info(f"✓ Cancer trials found: {cancer_results['hits']['total']['value']}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        return False


def main():
    """Main ingestion pipeline."""
    logger.info("=" * 70)
    logger.info("Clinical Trials Data Ingestion Pipeline")
    logger.info("=" * 70)
    
    # Step 1: Initialize Elasticsearch client
    logger.info("\n[Step 1/5] Connecting to Elasticsearch...")
    try:
        es_client = Elasticsearch([Config.ELASTICSEARCH_HOST], request_timeout=30)
        
        if not es_client.ping():
            logger.error("✗ Cannot connect to Elasticsearch")
            sys.exit(1)
        
        logger.info(f"✓ Connected to Elasticsearch at {Config.ELASTICSEARCH_HOST}")
        
        # Get cluster info
        info = es_client.info()
        logger.info(f"  Cluster: {info['cluster_name']}")
        logger.info(f"  Version: {info['version']['number']}")
        
    except Exception as e:
        logger.error(f"✗ Elasticsearch connection failed: {e}")
        sys.exit(1)
    
    # Step 2: Load data
    logger.info("\n[Step 2/5] Loading clinical trials data...")
    trials_data = load_clinical_trials("clinical_trials.json")
    
    # Step 3: Preprocess data
    logger.info("\n[Step 3/5] Preprocessing data...")
    preprocessor = DataPreprocessor()
    cleaned_trials = preprocessor.preprocess_batch(trials_data)
    
    stats = preprocessor.get_stats()
    logger.info(f"""
    Preprocessing Results:
    ----------------------
    Total records:    {stats['total_records']}
    Valid records:    {stats['valid_records']}
    Skipped records:  {stats['skipped_records']}
    Warnings:         {len(stats['warnings'])}
    Success rate:     {(stats['valid_records'] / stats['total_records'] * 100):.2f}%
    """)
    
    if stats['warnings']:
        logger.info(f"  First 5 warnings:")
        for warning in stats['warnings'][:5]:
            logger.info(f"    - {warning}")
    
    if not cleaned_trials:
        logger.error("✗ No valid records to index")
        sys.exit(1)
    
    # Step 4: Create index
    logger.info("\n[Step 4/5] Creating Elasticsearch index...")
    index_name = Config.ELASTICSEARCH_INDEX
    
    if not create_index(es_client, index_name):
        logger.error("✗ Failed to create index")
        sys.exit(1)
    
    # Step 5: Bulk index data
    logger.info("\n[Step 5/5] Indexing data into Elasticsearch...")
    result = bulk_index_trials(es_client, index_name, cleaned_trials)
    
    logger.info(f"""
    Indexing Results:
    -----------------
    Successfully indexed: {result['success']}
    Failed:              {result['failed']}
    """)
    
    # Verify ingestion
    logger.info("\n[Verification] Checking indexed data...")
    verify_ingestion(es_client, index_name)
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("✓ Data Ingestion Complete!")
    logger.info("=" * 70)
    logger.info(f"""
    Summary:
    --------
    Index name:           {index_name}
    Total documents:      {result['success']}
    Elasticsearch URL:    {Config.ELASTICSEARCH_HOST}
    
    Test queries:
    -------------
    1. Count all documents:
       curl '{Config.ELASTICSEARCH_HOST}/{index_name}/_count'
    
    2. Search for cancer trials:
       curl '{Config.ELASTICSEARCH_HOST}/{index_name}/_search?q=cancer&size=5'
    
    3. Get trial by NCT ID (example):
       curl '{Config.ELASTICSEARCH_HOST}/{index_name}/_doc/NCT00000105'
    
    4. View index mapping:
       curl '{Config.ELASTICSEARCH_HOST}/{index_name}/_mapping'
    """)


if __name__ == "__main__":
    main()
