#!/usr/bin/env python3
"""
Reset the 'used' field to 0 for all records in the traces table
"""
import sqlite3
import os
import sys

# Read environment variables
NAME = os.environ.get("NAME")
DB_PATH = os.environ.get("DB_PATH")

# Check required environment variables
if not NAME:
    print("Error: NAME environment variable is not set")
    sys.exit(1)

# Build trace_db_path
trace_db_path = f'../backend/{NAME}_trace.db'
if DB_PATH and DB_PATH != '':
    trace_db_path = f'{DB_PATH}/{NAME}_trace.db'

print(f"Using database path: {trace_db_path}")

try:
    # Connect to trace database
    trace_conn = sqlite3.connect(trace_db_path)
    trace_cursor_write = trace_conn.cursor()
    
    # Execute update operation
    print("Resetting 'used' field in traces table...")
    trace_cursor_write.execute("UPDATE traces SET used = 0")
    trace_conn.commit()
    
    # Get affected rows count
    affected_rows = trace_cursor_write.rowcount
    print(f"Successfully updated {affected_rows} records")
    
    # Close connection
    trace_conn.close()
    print("Operation completed!")
    
except sqlite3.Error as e:
    print(f"Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error occurred: {e}")
    sys.exit(1)

