import os
import json
import psycopg2

# PostgreSQL connection details
DB_PARAMS = {
    "dbname": "random_user_sample",
    "user": "postgres",  # Replace with your username
    "password": "mysecretpassword",  # Replace with your actual password
    "host": "trustwallet-postgres",
    "port": 5432
}

PROCESSED_DATA_PATH = "data/processed/processed_data.json"

insert_identities = """
INSERT INTO identities (id, username)
VALUES (%s, %s)
ON CONFLICT (id) DO NOTHING
"""

insert_profiles = """
INSERT INTO profiles (identity_id, date_of_birth, gender, state, city, zip, picture_url, cell)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (identity_id) DO NOTHING
"""


def load_transformed_data():
    """Loads transformed raw into PostgreSQL database."""

    if not os.path.exists(PROCESSED_DATA_PATH):
        print(f"❌ Error: {PROCESSED_DATA_PATH} not found!")
        return

    with open(PROCESSED_DATA_PATH, "r") as file:
        processed_data = json.load(file)

    if not processed_data:
        print("⚠️ No raw found in processed_data.json")
        return

    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cursor:
            for user in processed_data:
                try:
                    # Insert into identities table
                    cursor.execute(insert_identities, (user["id"], user["username"]))

                    # Insert into profiles table
                    cursor.execute(insert_profiles, (
                        user["id"], user["date_of_birth"], user["gender"],
                        user["state"], user["city"], user["zip"],
                        user["picture_url"], user["cell"]
                    ))
                except Exception as e:
                    print(f"❌ Error inserting user {user['id']}: {e}")

        conn.commit()

    print("✅ Transformed raw successfully loaded into PostgreSQL!")


if __name__ == "__main__":
    load_transformed_data()
