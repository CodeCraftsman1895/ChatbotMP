import logging
import sys
import os

# Ensure the project root is in the path so we can import 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.extractor_service import run_extraction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sync_bot")

def main():
    """Run a single cycle of incremental extraction and synchronization."""
    logger.info("Starting one-shot synchronization cycle...")
    try:
        # Run incremental extraction and update the vector store
        run_extraction(incremental=True, update_vectors=True)
        logger.info("Synchronization cycle completed successfully.")
    except Exception as e:
        logger.error(f"Synchronization cycle failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
