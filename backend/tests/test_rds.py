"""CHECKPOINT 1: Test RDS PostgreSQL connection."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()


def test_rds():
    import psycopg2

    database_url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {database_url.split('@')[1]}")  # hide password

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    assert result == (1,)
    print(f"SELECT 1 = {result[0]}")

    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"PostgreSQL version: {version}")

    cur.close()
    conn.close()
    print("[PASS] RDS connection SUCCESS")


if __name__ == "__main__":
    try:
        test_rds()
    except Exception as e:
        print(f"[FAIL] RDS connection FAILED: {e}")
        print("\nTroubleshooting:")
        print("  1. RDS instance status = Available?")
        print("  2. Security group inbound rule: PostgreSQL 5432, My IP?")
        print("  3. DATABASE_URL correct?")
        sys.exit(1)
