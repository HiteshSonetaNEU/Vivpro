from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from elasticsearch import Elasticsearch
import time

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app, origins=app.config['CORS_ORIGINS'])

# Initialize Elasticsearch client
es_client = None

def init_elasticsearch():
    """Initialize Elasticsearch connection with retry logic"""
    global es_client
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            es_client = Elasticsearch(
                [app.config['ELASTICSEARCH_HOST']],
                request_timeout=30
            )
            if es_client.ping():
                print(f"✓ Connected to Elasticsearch at {app.config['ELASTICSEARCH_HOST']}")
                return True
            else:
                print(f"✗ Elasticsearch ping failed (attempt {attempt + 1}/{max_retries})")
        except Exception as e:
            print(f"✗ Elasticsearch connection error (attempt {attempt + 1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            print(f"  Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print("✗ Failed to connect to Elasticsearch after multiple attempts")
    return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    es_status = 'connected' if es_client and es_client.ping() else 'disconnected'
    
    return jsonify({
        'status': 'ok',
        'elasticsearch': es_status,
        'environment': app.config['FLASK_ENV']
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Clinical Trials Search API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'search': '/api/search (coming soon)',
            'trial': '/api/trial/<nct_id> (coming soon)',
            'filters': '/api/filters (coming soon)'
        }
    }), 200

if __name__ == '__main__':
    print("=" * 60)
    print("Clinical Trials Search API - Starting...")
    print("=" * 60)
    
    # Initialize Elasticsearch
    if init_elasticsearch():
        print("\n✓ Flask API ready to serve requests")
    else:
        print("\n⚠ Flask API starting without Elasticsearch connection")
    
    print(f"\nServer running on: http://0.0.0.0:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
