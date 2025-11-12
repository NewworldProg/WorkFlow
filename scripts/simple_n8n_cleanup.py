#!/usr/bin/env python3
"""
Simple N8N Database Cleanup Script
No arguments - just runs cleanup with fixed parameters
"""
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from data.database_cleanup import DatabaseCleaner
    
    print("[INFO] Starting n8n database cleanup...")
    
    # Fixed parameters
    db_path = "upwork_data.db"
    keep_scrapes = 50
    
    # Make sure we're in the right directory
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    print(f"[INFO] Working directory: {os.getcwd()}")
    print(f"[INFO] Database path: {db_path}")
    print(f"[INFO] Keeping latest {keep_scrapes} scrapes")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        sys.exit(1)
    
    # Run cleanup
    cleaner = DatabaseCleaner(db_path)
    
    # Set keep_scrapes parameter
    cleaner.keep_scrapes = keep_scrapes
    
    # Get stats before cleanup
    before_stats = cleaner.get_database_stats()
    print(f"[INFO] Before cleanup: {before_stats}")
    
    # Run cleanup
    success = cleaner.run_cleanup(vacuum=True)
    
    if success:
        print("[OK] Database cleanup completed successfully!")
        print(f"[CLEANUP] Records deleted: {cleaner.cleanup_stats}")
        
        # Get stats after cleanup
        after_stats = cleaner.get_database_stats()
        space_saved = before_stats.get('db_size_mb', 0) - after_stats.get('db_size_mb', 0)
        print(f"[DISK] Space saved: {space_saved:.2f} MB")
        print(f"[INFO] After cleanup: {after_stats}")
        
    else:
        print("[ERROR] Database cleanup failed")
        sys.exit(1)

except ImportError as e:
    print(f"[ERROR] Cannot import database_cleanup: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Database cleanup failed: {e}")
    sys.exit(1)