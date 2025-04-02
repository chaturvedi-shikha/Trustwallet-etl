import os
import json
from datetime import datetime

RAW_DATA_PATH = "data/raw/raw_data.json"
PROCESSED_DATA_PATH = "data/processed/processed_data.json"


def transform_data():
    """Transforms raw raw by extracting relevant fields and normalizing timestamps."""

    if not os.path.exists(RAW_DATA_PATH):
        print(f"❌ Error: {RAW_DATA_PATH} not found!")
        return

    with open(RAW_DATA_PATH, "r") as file:
        raw_data = json.load(file)

    if not raw_data:
        print("⚠️ No raw found in raw_data.json")
        return

    print("🔍 Raw user raw example:", raw_data[0])

    transformed_data = []

    for user in raw_data:
        try:
            # Compute age from birthdate
            birth_date = datetime.strptime(user["dob"]["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
            age = (datetime.today() - birth_date).days // 365  # Convert days to years

            transformed_data.append({
                "id": f"{user['id'].get('name', '')}{user['id'].get('value', '')}".replace(" ", "").replace("\"", ""),
                "username": user["login"].get("username", "unknown"),
                "full_name": f"{user['name']['first']} {user['name']['last']}".title(),
                "date_of_birth": birth_date.isoformat(),
                "age": age,  # Added Age
                "gender": user.get("gender", "unknown"),
                "state": user["location"].get("state", "unknown").title(),
                "city": user["location"].get("city", "unknown").title(),
                "zip": str(user["location"].get("postcode", "unknown")),  # Standardized ZIP
                "picture_url": user["picture"].get("large", ""),
                "cell": user.get("cell", "N/A")
            })
        except Exception as e:
            print(f"❌ Error processing user: {user} | {e}")

    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)

    with open(PROCESSED_DATA_PATH, "w") as file:
        json.dump(transformed_data, file, indent=4)

    print(f"✅ Transformed raw saved to {PROCESSED_DATA_PATH}")

