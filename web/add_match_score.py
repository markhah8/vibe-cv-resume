#!/usr/bin/env python3
"""
Add match_score column to cv_variants table
"""
import sqlite3
import sys
from pathlib import Path

# Get the database path
DB_PATH = Path(__file__).parent / 'vibe_cv.db'

def add_match_score_column():
    """Add match_score column to cv_variants table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(cv_variants)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'match_score' in columns:
            print("✅ Column 'match_score' already exists")
            return True
        
        # Add the column
        cursor.execute("""
            ALTER TABLE cv_variants 
            ADD COLUMN match_score INTEGER
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully added 'match_score' column to cv_variants table")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = add_match_score_column()
    sys.exit(0 if success else 1)
