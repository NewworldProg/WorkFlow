"""
Scheduled Database Cleanup
Automated database cleanup that runs periodically to maintain database size
"""
import os
import sys
import logging
from datetime import datetime, timedelta
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data.database_cleanup import DatabaseCleaner

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScheduledCleaner:
    """Handles scheduled database cleanup with configuration"""
    
    def __init__(self, config_file: str = "cleanup_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self) -> dict:
        """Load cleanup configuration"""
        default_config = {
            "enabled": True,
            "keep_scrapes": 50,
            "database_path": "upwork_data.db",
            "cleanup_frequency_hours": 24,
            "vacuum_database": True,
            "analytics_retention_days": 30,
            "min_keyword_frequency": 1,
            "last_cleanup": None,
            "notifications": {
                "log_to_file": True,
                "email_on_failure": False,
                "email_recipients": []
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
            else:
                # Create default config file
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"📄 Created default config: {self.config_file}")
                
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            
        return default_config
        
    def save_config(self):
        """Save current configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Error saving config: {e}")
            
    def should_run_cleanup(self) -> bool:
        """Check if cleanup should run based on schedule"""
        if not self.config.get("enabled", True):
            logger.info("🔒 Cleanup is disabled in config")
            return False
            
        last_cleanup = self.config.get("last_cleanup")
        frequency_hours = self.config.get("cleanup_frequency_hours", 24)
        
        if not last_cleanup:
            logger.info("🆕 No previous cleanup found, running cleanup")
            return True
            
        try:
            last_cleanup_time = datetime.fromisoformat(last_cleanup)
            next_cleanup_time = last_cleanup_time + timedelta(hours=frequency_hours)
            current_time = datetime.now()
            
            if current_time >= next_cleanup_time:
                hours_since = (current_time - last_cleanup_time).total_seconds() / 3600
                logger.info(f"⏰ Last cleanup was {hours_since:.1f} hours ago, running cleanup")
                return True
            else:
                hours_until = (next_cleanup_time - current_time).total_seconds() / 3600
                logger.info(f"⏰ Next cleanup in {hours_until:.1f} hours")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking cleanup schedule: {e}")
            return True  # Run cleanup on error
            
    def run_scheduled_cleanup(self, force: bool = False):
        """Run cleanup if scheduled or forced"""
        try:
            if not force and not self.should_run_cleanup():
                return {"status": "skipped", "reason": "not_scheduled"}
                
            logger.info("🧹 Starting scheduled database cleanup...")
            
            # Initialize cleaner with config
            cleaner = DatabaseCleaner(
                db_path=self.config.get("database_path", "upwork_data.db"),
                keep_scrapes=self.config.get("keep_scrapes", 50)
            )
            
            # Check database exists
            if not os.path.exists(cleaner.db_path):
                error_msg = f"Database file not found: {cleaner.db_path}"
                logger.error(f"❌ {error_msg}")
                return {"status": "error", "error": error_msg}
                
            # Get stats before cleanup
            before_stats = cleaner.get_database_stats()
            logger.info(f"📊 Database stats before cleanup: {before_stats}")
            
            # Run cleanup
            success = cleaner.run_cleanup(
                vacuum=self.config.get("vacuum_database", True)
            )
            
            if success:
                # Update last cleanup time
                self.config["last_cleanup"] = datetime.now().isoformat()
                self.save_config()
                
                # Get stats after cleanup
                after_stats = cleaner.get_database_stats()
                
                cleanup_result = {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "before_stats": before_stats,
                    "after_stats": after_stats,
                    "cleanup_stats": cleaner.cleanup_stats,
                    "config": {
                        "keep_scrapes": self.config.get("keep_scrapes"),
                        "database_path": self.config.get("database_path")
                    }
                }
                
                # Calculate space saved
                if before_stats.get('db_size_mb') and after_stats.get('db_size_mb'):
                    space_saved = before_stats['db_size_mb'] - after_stats['db_size_mb']
                    cleanup_result["space_saved_mb"] = round(space_saved, 2)
                    
                logger.info("✅ Scheduled cleanup completed successfully!")
                return cleanup_result
                
            else:
                error_msg = "Cleanup process failed"
                logger.error(f"❌ {error_msg}")
                return {"status": "error", "error": error_msg}
                
        except Exception as e:
            error_msg = f"Cleanup failed with exception: {str(e)}"
            logger.error(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": error_msg}

def main():
    """Main function for scheduled cleanup"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scheduled database cleanup')
    parser.add_argument('--force', action='store_true', 
                       help='Force cleanup regardless of schedule')
    parser.add_argument('--config', type=str, default="cleanup_config.json",
                       help='Configuration file path')
    parser.add_argument('--status', action='store_true',
                       help='Show cleanup status and configuration')
    
    args = parser.parse_args()
    
    # Initialize scheduled cleaner
    cleaner = ScheduledCleaner(config_file=args.config)
    
    if args.status:
        # Show status
        print("📊 Database Cleanup Status")
        print("=========================")
        print(f"Enabled: {cleaner.config.get('enabled', True)}")
        print(f"Database: {cleaner.config.get('database_path', 'upwork_data.db')}")
        print(f"Keep scrapes: {cleaner.config.get('keep_scrapes', 50)}")
        print(f"Frequency: {cleaner.config.get('cleanup_frequency_hours', 24)} hours")
        print(f"Last cleanup: {cleaner.config.get('last_cleanup', 'Never')}")
        
        # Check if should run
        should_run = cleaner.should_run_cleanup()
        print(f"Should run now: {should_run}")
        
        return 0
        
    # Run cleanup
    result = cleaner.run_scheduled_cleanup(force=args.force)
    
    print(f"\n📋 Cleanup Result:")
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        print("✅ Cleanup completed successfully!")
        if 'space_saved_mb' in result:
            print(f"💾 Space saved: {result['space_saved_mb']} MB")
        return 0
    elif result.get('status') == 'skipped':
        print("⏭️ Cleanup skipped (not scheduled)")
        return 0
    else:
        print(f"❌ Cleanup failed: {result.get('error', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    exit(main())
