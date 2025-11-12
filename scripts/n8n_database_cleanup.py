"""
N8N Database Cleanup Script
Cleans up Upwork database for n8n workflow integration
"""
import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data.database_cleanup import DatabaseCleaner

def cleanup_for_n8n(keep_scrapes=50, db_path="upwork_data.db"):
    """
    Run database cleanup and return n8n-compatible JSON response
    """
    try:
        print(f"[INFO] Starting database cleanup for n8n...")
        print(f"[INFO] Keeping latest {keep_scrapes} scrapes")
        print(f"[INFO] Database: {db_path}")
        
        # Check if database exists
        if not os.path.exists(db_path):
            return {
                "success": False,
                "error": f"Database file not found: {db_path}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Initialize cleaner
        cleaner = DatabaseCleaner(
            db_path=db_path,
            keep_scrapes=keep_scrapes
        )
        
        # Get stats before cleanup
        before_stats = cleaner.get_database_stats()
        print(f"📈 Before cleanup: {before_stats}")
        
        # Run cleanup
        success = cleaner.run_cleanup(vacuum=True)
        
        if success:
            # Get stats after cleanup
            after_stats = cleaner.get_database_stats()
            
            # Calculate space saved
            space_saved_mb = 0
            if before_stats.get('db_size_mb') and after_stats.get('db_size_mb'):
                space_saved_mb = round(before_stats['db_size_mb'] - after_stats['db_size_mb'], 2)
            
            result = {
                "success": True,
                "message": "Database cleanup completed successfully",
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "keep_scrapes": keep_scrapes,
                    "database_path": db_path
                },
                "before_stats": before_stats,
                "after_stats": after_stats,
                "cleanup_stats": cleaner.cleanup_stats,
                "space_saved_mb": space_saved_mb
            }
            
            print(f"[OK] Cleanup completed successfully!")
            print(f"[CLEANUP] Cleanup summary: {cleaner.cleanup_stats}")
            print(f"[DISK] Space saved: {space_saved_mb} MB")
            
            return result
            
        else:
            return {
                "success": False,
                "error": "Database cleanup process failed",
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "keep_scrapes": keep_scrapes,
                    "database_path": db_path
                }
            }
            
    except Exception as e:
        error_msg = f"Database cleanup failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "keep_scrapes": keep_scrapes,
                "database_path": db_path
            }
        }

def main():
    """Main function for n8n integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database cleanup for n8n')
    parser.add_argument('--keep-scrapes', type=int, default=50,
                       help='Number of recent scrapes to keep (default: 50)')
    parser.add_argument('--db-path', type=str, default="upwork_data.db",
                       help='Database file path (default: upwork_data.db)')
    parser.add_argument('--json-output', action='store_true',
                       help='Output result as JSON for n8n')
    
    args = parser.parse_args()
    
    # Run cleanup
    result = cleanup_for_n8n(
        keep_scrapes=args.keep_scrapes,
        db_path=args.db_path
    )
    
    if args.json_output:
        # Output JSON for n8n
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        if result["success"]:
            print(f"\n[OK] Database cleanup completed!")
            if "space_saved_mb" in result:
                print(f"[DISK] Space saved: {result['space_saved_mb']} MB")
        else:
            print(f"\n[ERROR] Database cleanup failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Return appropriate exit code
    return 0 if result["success"] else 1

if __name__ == "__main__":
    exit(main())
