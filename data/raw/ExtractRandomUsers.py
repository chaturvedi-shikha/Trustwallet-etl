import requests as r
import psycopg2
import os
import json

# PostgreSQL connection details
DB_PARAMS = {
    "dbname": "random_user_sample",
    "user": "postgres",  # Replace with your PostgreSQL username
    "password": "admin",  # Replace with your actual password
    "host": "localhost",
    "port": 5432

}

create_api_results_table = """
CREATE TABLE IF NOT EXISTS api_results (
    raw json
)
"""

create_identities_table = """
CREATE TABLE IF NOT EXISTS identities (
    id TEXT NOT NULL PRIMARY KEY,
    username TEXT
)
"""

create_profiles_table = """
CREATE TABLE IF NOT EXISTS profiles (
    identity_id TEXT NOT NULL UNIQUE REFERENCES identities(id),
    date_of_birth TIMESTAMP,
    gender TEXT,
    state TEXT,
    city TEXT,
    zip TEXT,
    picture_url TEXT,
    cell TEXT
)
"""

populate_identities_table = """
INSERT INTO identities (id, username)
SELECT 
    CONCAT(raw->'id'->'name', raw->'id'->'value'),
    raw->'login'->>'username'
FROM api_results
ON CONFLICT (id) DO NOTHING
"""

populate_profiles_table = """
INSERT INTO profiles (identity_id, date_of_birth, gender, state, city, zip, picture_url, cell)
SELECT
    DISTINCT CONCAT(raw->'id'->'name', raw->'id'->'value'),
    to_timestamp(raw->'dob'->>'date', 'YYYY-MM-DDTHH:MI:SS.MSZ'),
    raw->>'gender',
    raw->'location'->>'state',
    raw->'location'->>'city',
    raw->'location'->>'postcode', 
    raw->'picture'->>'large',
    raw->>'cell'
FROM api_results
ON CONFLICT (identity_id) DO NOTHING
"""


def setup_db():
    """Creates any missing tables from api_results, identities, and profiles"""
    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cursor:
            cursor.execute(create_api_results_table)
            cursor.execute(create_identities_table)
            cursor.execute(create_profiles_table)
        conn.commit()


def get_random_users(amount=20):
    """Fetch random user raw from API"""
    return r.get(f"https://randomuser.me/api/?results={amount}").json()["results"]


def load_users_into_api_results(users):
    """Load user raw into api_results table"""
    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cursor:
            for user in users:
                cursor.execute("INSERT INTO api_results (raw) VALUES (%s)", [json.dumps(user)])
        conn.commit()


def load_results_into_identities_and_profiles():
    """Populate identities and profiles tables from api_results"""
    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cursor:
            cursor.execute(populate_identities_table)
            cursor.execute(populate_profiles_table)
        conn.commit()


def export_data_to_json():
    """Extracts processed raw from PostgreSQL and saves it as JSON"""
    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cursor:
            # Fetching raw from identities and profiles
            cursor.execute("""
                SELECT i.id, i.username, p.date_of_birth, p.gender, p.state, 
                       p.city, p.zip, p.picture_url, p.cell
                FROM identities i
                LEFT JOIN profiles p ON i.id = p.identity_id
            """)
            data = cursor.fetchall()

            # Convert to a structured dictionary format
            records = []
            for row in data:
                records.append({
                    "id": row[0],
                    "username": row[1],
                    "date_of_birth": row[2].isoformat() if row[2] else None,
                    "gender": row[3],
                    "state": row[4],
                    "city": row[5],
                    "zip": row[6],
                    "picture_url": row[7],
                    "cell": row[8]
                })

            # Ensure the directory exists
            os.makedirs("raw/raw", exist_ok=True)

            # Save to JSON file
            with open("raw/raw_data.json", "w") as f:
                json.dump(records, f, indent=4)

            print("✅ Data exported successfully to raw/raw/raw_data.json")


def main():
    print("Running ETL job...")
    setup_db()
    users = get_random_users()
    load_users_into_api_results(users)
    load_results_into_identities_and_profiles()
    export_data_to_json()  # <-- Add this function call
    print("ETL job completed.")

if __name__ == "__main__":
    main()