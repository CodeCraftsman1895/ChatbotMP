from app.services.extractor_service import run_extraction

if __name__ == "__main__":
    run_extraction(incremental=False, update_vectors=True)