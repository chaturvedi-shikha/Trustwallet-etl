import os
import json
import requests as r
import psycopg2
import logging
from datetime import datetime
from transform import transform_data
from load_transformed_data import load_transformed_data
from flask import Flask, jsonify

# Configure logging: Save scripts in 'scripts/etl.log' in structured JSON format
LOG_FILE = "logs/etl.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=json.dumps({
        "timestamp": "%(asctime)s",
        "level": "%(levelname)s",
        "message": "%(message)s"
    }),
    datefmt="%Y-%m-%d %H:%M:%S"
)

# PostgreSQL connection details
DB_PARAMS = {
    "dbname": "random_user_sample",
    "user": "postgres",
    "password": "admin",
    "host": "localhost",
    "port": 5432
}


def log_event(level, message, extra=None):
    """Custom logging function with structured JSON format"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
    }
    if extra:
        log_entry.update(extra)
    logging.info(json.dumps(log_entry))


def setup_db():
    """Creates any missing tables"""
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cursor:
                cursor.execute("CREATE TABLE IF NOT EXISTS api_results (raw json)")
                cursor.execute("CREATE TABLE IF NOT EXISTS identities (id TEXT NOT NULL PRIMARY KEY, username TEXT)")
                cursor.execute("""
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
                """)
            conn.commit()
        log_event("INFO", "Database setup completed")
    except Exception as e:
        log_event("ERROR", "Error setting up database", {"error": str(e)})


def get_random_users(amount=20):
    """Fetch random user raw from API"""
    try:
        response = r.get(f"https://randomuser.me/api/?results={amount}")
        response.raise_for_status()
        log_event("INFO", f"Fetched {amount} random users from API")
        return response.json()["results"]
    except Exception as e:
        log_event("ERROR", "Failed to fetch raw from API", {"error": str(e)})
        return []


def save_raw_data(users, filepath="raw/raw/raw_data.json"):
    """Save raw user raw to local JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(users, f, indent=4)
        log_event("INFO", f"Raw raw saved to {filepath}")
    except Exception as e:
        log_event("ERROR", "Error saving raw raw", {"error": str(e)})


def load_users_into_api_results(users):
    """Load user raw into PostgreSQL"""
    if not users:
        log_event("WARNING", "No users to load into the database")
        return

    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cursor:
                for user in users:
                    cursor.execute("INSERT INTO api_results (raw) VALUES (%s)", [json.dumps(user)])
            conn.commit()
        log_event("INFO", "Data loaded into PostgreSQL (api_results table)")
    except Exception as e:
        log_event("ERROR", "Error loading raw into PostgreSQL", {"error": str(e)})


def load_results_into_identities_and_profiles():
    """Populate identities and profiles tables from api_results"""
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO identities (id, username)
                    SELECT 
                        CONCAT(raw->'id'->'name', raw->'id'->'value'),
                        raw->'login'->>'username'
                    FROM api_results
                    ON CONFLICT (id) DO NOTHING
                """)
                cursor.execute("""
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
                """)
            conn.commit()
        log_event("INFO", "Tables identities and profiles updated")
    except Exception as e:
        log_event("ERROR", "Error populating identities and profiles", {"error": str(e)})


def main():
    """Main function to run the pipeline"""
    log_event("INFO", "🚀 Pipeline execution started")

    setup_db()
    users = get_random_users()

    if users:
        save_raw_data(users)
        load_users_into_api_results(users)
        load_results_into_identities_and_profiles()

    transform_data()
    load_transformed_data()

    log_event("INFO", "🏁 Pipeline execution completed successfully")


if __name__ == "__main__":
    main()
