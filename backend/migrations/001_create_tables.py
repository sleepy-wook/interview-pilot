"""Migration 001: Create all initial tables."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

from core.database import create_tables

if __name__ == "__main__":
    create_tables()
    print("[PASS] All tables created successfully")
