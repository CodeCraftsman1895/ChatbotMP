import json
from app.chatbot.chat_service import update_vector_db

if __name__ == '__main__':
    with open('data/processed_data.json', 'r', encoding='utf-8') as f:
        processed_data = json.load(f)
    update_vector_db(processed_data)
    print('Vector store update complete.')
