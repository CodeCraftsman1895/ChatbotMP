import json
import os

def save_to_json(data, file_path="data/processed_data.json"):
    os.makedirs("data", exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Data saved to {file_path}")