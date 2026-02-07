#!/usr/bin/env python3
"""
Quick script to run data ingestion from the host machine or inside container.
"""

import subprocess
import sys

def main():
    print("=" * 70)
    print("Clinical Trials Data Ingestion")
    print("=" * 70)
    print("\nRunning ingestion script in Docker container...\n")
    
    try:
        # Run ingest.py inside the flask-api container
        result = subprocess.run(
            ["docker", "exec", "vivpro-flask-api", "python", "ingest.py"],
            check=True,
            capture_output=False,
            text=True
        )
        
        print("\n" + "=" * 70)
        print("✓ Ingestion completed successfully!")
        print("=" * 70)
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 70)
        print("✗ Ingestion failed!")
        print("=" * 70)
        sys.exit(1)
    except FileNotFoundError:
        print("\n✗ Docker command not found. Make sure Docker is installed and running.")
        sys.exit(1)


if __name__ == "__main__":
    main()
