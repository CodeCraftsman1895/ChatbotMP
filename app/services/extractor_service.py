import logging
from app.db.mongo import users_col, spaces_col, contents_col

from app.extractors.youtube import extract_youtube
from app.extractors.pdf import extract_pdf
from app.extractors.article import extract_article
from app.extractors.notes import extract_note

from app.storage.file_store import save_to_json
from app.chatbot.chat_service import update_vector_db

import json
import os

logger = logging.getLogger(__name__)

def process_content(content):
    """
    Process a single content item based on its type and extract text.

    Args:
        content (dict): Content document from MongoDB.

    Returns:
        dict: {"content": str, "error": str or None}
    """
    try:
        ctype = content.get("type")
        link = content.get("link")
        
        if not ctype:
            return {"content": "", "error": "Content type is missing"}

        if ctype == "youtube":
            if not link:
                return {"content": "", "error": "YouTube link is missing"}
            return extract_youtube(link)

        elif ctype == "document":
            if not link:
                return {"content": "", "error": "Document link is missing"}
            return extract_pdf(link)

        elif ctype == "note":
            return extract_note(content)

        elif ctype == "article":
            if not link:
                return {"content": "", "error": "Article link is missing"}
            return extract_article(link)

        else:
            return {"content": "", "error": f"Unsupported content type: {ctype}"}
    except Exception as e:
        logger.error(f"Error processing content {content.get('_id')}: {e}")
        return {"content": "", "error": f"Processing failed: {str(e)}"}


def run_extraction(incremental=False, update_vectors=False):
    """
    Extract text from all content in the database and save to JSON.

    If incremental=True, only process content not already in processed_data.json.

    Args:
        incremental (bool): Whether to process only new content.
        update_vectors (bool): Whether to update vector store after extraction.
    """
    try:
        contents = list(contents_col.find())
        users = list(users_col.find())
        spaces = list(spaces_col.find())

        if not contents:
            logger.warning("No content found in database")
            return

        # Create lookup maps
        user_map = {
            str(u["_id"]): f"{u.get('firstName','')} {u.get('lastName','')}".strip()
            for u in users
        }

        space_map = {
            str(s["_id"]): s.get("name", "")
            for s in spaces
        }

        # Load existing processed data if incremental
        processed_file = "data/processed_data.json"
        if incremental and os.path.exists(processed_file):
            try:
                with open(processed_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                existing_ids = {record["contentId"] for record in existing_data}
            except Exception as e:
                logger.error(f"Error loading existing processed data: {e}")
                existing_data = []
                existing_ids = set()
        else:
            existing_data = []
            existing_ids = set()

        new_processed_data = []
        successful_extractions = 0
        failed_extractions = 0

        for content in contents:
            content_id = str(content.get("_id"))
            if incremental and content_id in existing_ids:
                continue  # Skip already processed

            title = content.get('title', 'Untitled')
            logger.info(f"Processing: {title}")

            extraction_result = process_content(content)
            if isinstance(extraction_result, dict):
                extracted_text = extraction_result.get("content", "")
                extraction_error = extraction_result.get("error")
            else:
                extracted_text = extraction_result or ""
                extraction_error = None

            if extraction_error:
                failed_extractions += 1
                logger.warning(f"Extraction failed for {title}: {extraction_error}")
            else:
                successful_extractions += 1

            record = {
                "userId": str(content.get("userId")),
                "userName": user_map.get(str(content.get("userId")), "Unknown"),

                "spaceId": str(content.get("spaceId")),
                "spaceName": space_map.get(str(content.get("spaceId")), "Unknown"),

                "contentId": content_id,
                "title": title,
                "type": content.get("type"),
                "sourceLink": content.get("link"),

                "contentText": extracted_text,
                "contentError": extraction_error,
                "status": "failed" if extraction_error else "success"
            }

            new_processed_data.append(record)

        # Merge with existing if incremental
        if incremental:
            all_data = existing_data + new_processed_data
        else:
            all_data = new_processed_data

        save_to_json(all_data)
        logger.info(f"Extraction completed. Success: {successful_extractions}, Failed: {failed_extractions}")

        # Update vector store optionally
        if update_vectors:
            try:
                update_vector_db(all_data)
                logger.info("Vector store updated successfully")
            except Exception as e:
                logger.error(f"Failed to update vector store: {e}")
                
    except Exception as e:
        logger.error(f"Critical error in run_extraction: {e}")
        raise
