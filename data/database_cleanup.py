"""
Database Cleanup Script
Cleans up the Upwork database, keeping only the latest 50 scrapes
"""
import os
import sys
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data.database_manager import UpworkDatabase

class DatabaseCleaner:
    """Handles database cleanup operations"""
    
    def __init__(self, db_path: str = "upwork_data.db", keep_scrapes: int = 50):
        self.db_path = db_path
        self.keep_scrapes = keep_scrapes
        self.cleanup_stats = {
            'scraped_data_deleted': 0,
            'jobs_deleted': 0,
            'proposals_deleted': 0,
            'cover_letters_deleted': 0,
            'analytics_deleted': 0,
            'keywords_deleted': 0
        }
        
    def get_database_stats(self) -> Dict:
        """Get current database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Count records in each table
        tables = ['scraped_data', 'jobs', 'proposals', 'cover_letters', 'analytics', 'keywords']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                stats[f'{table}_count'] = 0
                
        # Get database file size
        try:
            stats['db_size_mb'] = round(os.path.getsize(self.db_path) / 1024 / 1024, 2)
        except:
            stats['db_size_mb'] = 0
            
        # Get oldest and newest scrape dates
        try:
            cursor.execute("SELECT MIN(scrape_timestamp), MAX(scrape_timestamp) FROM scraped_data")
            oldest, newest = cursor.fetchone()
            stats['oldest_scrape'] = oldest
            stats['newest_scrape'] = newest
        except:
            stats['oldest_scrape'] = None
            stats['newest_scrape'] = None
            
        conn.close()
        return stats
        
    def get_scrapes_to_keep(self) -> List[int]:
        """Get IDs of the latest scrapes to keep"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM scraped_data 
            ORDER BY scrape_timestamp DESC 
            LIMIT ?
        ''', (self.keep_scrapes,))
        
        scrape_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return scrape_ids
        
    def cleanup_scraped_data(self, keep_ids: List[int]):
        """Clean up scraped_data table"""
        if not keep_ids:
            logger.warning("No scrape IDs to keep found!")
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count records that will be deleted
        placeholders = ','.join(['?' for _ in keep_ids])
        cursor.execute(f'''
            SELECT COUNT(*) FROM scraped_data 
            WHERE id NOT IN ({placeholders})
        ''', keep_ids)
        
        delete_count = cursor.fetchone()[0]
        
        if delete_count > 0:
            # Delete old scraped data
            cursor.execute(f'''
                DELETE FROM scraped_data 
                WHERE id NOT IN ({placeholders})
            ''', keep_ids)
            
            self.cleanup_stats['scraped_data_deleted'] = delete_count
            logger.info(f"🗑️ Deleted {delete_count} old scraped_data records")
        else:
            logger.info("✅ No old scraped_data records to delete")
            
        conn.commit()
        conn.close()
        
    def cleanup_jobs(self, keep_scrape_ids: List[int]):
        """Clean up jobs table based on scrape_ids"""
        if not keep_scrape_ids:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count records that will be deleted
        placeholders = ','.join(['?' for _ in keep_scrape_ids])
        cursor.execute(f'''
            SELECT COUNT(*) FROM jobs 
            WHERE scrape_id NOT IN ({placeholders})
        ''', keep_scrape_ids)
        
        delete_count = cursor.fetchone()[0]
        
        if delete_count > 0:
            # Delete old jobs
            cursor.execute(f'''
                DELETE FROM jobs 
                WHERE scrape_id NOT IN ({placeholders})
            ''', keep_scrape_ids)
            
            self.cleanup_stats['jobs_deleted'] = delete_count
            logger.info(f"🗑️ Deleted {delete_count} old job records")
        else:
            logger.info("✅ No old job records to delete")
            
        conn.commit()
        conn.close()
        
    def cleanup_proposals(self, keep_scrape_ids: List[int]):
        """Clean up proposals table based on scrape_ids"""
        if not keep_scrape_ids:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Count records that will be deleted
            placeholders = ','.join(['?' for _ in keep_scrape_ids])
            cursor.execute(f'''
                SELECT COUNT(*) FROM proposals 
                WHERE scrape_id NOT IN ({placeholders})
            ''', keep_scrape_ids)
            
            delete_count = cursor.fetchone()[0]
            
            if delete_count > 0:
                # Delete old proposals
                cursor.execute(f'''
                    DELETE FROM proposals 
                    WHERE scrape_id NOT IN ({placeholders})
                ''', keep_scrape_ids)
                
                self.cleanup_stats['proposals_deleted'] = delete_count
                logger.info(f"🗑️ Deleted {delete_count} old proposal records")
            else:
                logger.info("✅ No old proposal records to delete")
                
        except sqlite3.OperationalError:
            logger.info("ℹ️ Proposals table not found or empty")
            
        conn.commit()
        conn.close()
        
    def cleanup_orphaned_cover_letters(self):
        """Clean up cover letters that reference deleted jobs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Count orphaned cover letters
            cursor.execute('''
                SELECT COUNT(*) FROM cover_letters cl
                LEFT JOIN jobs j ON cl.job_id = j.id
                WHERE j.id IS NULL
            ''')
            
            orphaned_count = cursor.fetchone()[0]
            
            if orphaned_count > 0:
                # Delete orphaned cover letters
                cursor.execute('''
                    DELETE FROM cover_letters 
                    WHERE job_id NOT IN (SELECT id FROM jobs)
                ''')
                
                self.cleanup_stats['cover_letters_deleted'] = orphaned_count
                logger.info(f"🗑️ Deleted {orphaned_count} orphaned cover letter records")
            else:
                logger.info("✅ No orphaned cover letter records to delete")
                
        except sqlite3.OperationalError:
            logger.info("ℹ️ Cover letters table not found or empty")
            
        conn.commit()
        conn.close()
        
    def cleanup_old_analytics(self, days_to_keep: int = 30):
        """Clean up analytics data older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Count old analytics records
            cursor.execute('''
                SELECT COUNT(*) FROM analytics 
                WHERE created_timestamp < datetime('now', '-' || ? || ' days')
            ''', (days_to_keep,))
            
            old_count = cursor.fetchone()[0]
            
            if old_count > 0:
                # Delete old analytics
                cursor.execute('''
                    DELETE FROM analytics 
                    WHERE created_timestamp < datetime('now', '-' || ? || ' days')
                ''', (days_to_keep,))
                
                self.cleanup_stats['analytics_deleted'] = old_count
                logger.info(f"🗑️ Deleted {old_count} old analytics records (older than {days_to_keep} days)")
            else:
                logger.info(f"✅ No analytics records older than {days_to_keep} days to delete")
                
        except sqlite3.OperationalError:
            logger.info("ℹ️ Analytics table not found or empty")
            
        conn.commit()
        conn.close()
        
    def cleanup_unused_keywords(self, min_frequency: int = 1):
        """Clean up keywords with frequency below threshold"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Count unused keywords
            cursor.execute('''
                SELECT COUNT(*) FROM keywords 
                WHERE frequency <= ?
            ''', (min_frequency,))
            
            unused_count = cursor.fetchone()[0]
            
            if unused_count > 0:
                # Delete unused keywords
                cursor.execute('''
                    DELETE FROM keywords 
                    WHERE frequency <= ?
                ''', (min_frequency,))
                
                self.cleanup_stats['keywords_deleted'] = unused_count
                logger.info(f"🗑️ Deleted {unused_count} unused keyword records")
            else:
                logger.info("✅ No unused keyword records to delete")
                
        except sqlite3.OperationalError:
            logger.info("ℹ️ Keywords table not found or empty")
            
        conn.commit()
        conn.close()
        
    def vacuum_database(self):
        """Optimize database by running VACUUM"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            logger.info("🗜️ Database optimized with VACUUM")
        except Exception as e:
            logger.error(f"❌ Failed to vacuum database: {e}")
            
    def run_cleanup(self, vacuum: bool = True):
        """Run complete cleanup process"""
        logger.info("🧹 Starting database cleanup...")
        logger.info(f"📊 Keeping latest {self.keep_scrapes} scrapes")
        
        # Get stats before cleanup
        before_stats = self.get_database_stats()
        logger.info(f"📈 Before cleanup: {before_stats}")
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            logger.error(f"❌ Database file not found: {self.db_path}")
            return False
            
        try:
            # Get scrape IDs to keep
            keep_scrape_ids = self.get_scrapes_to_keep()
            
            if not keep_scrape_ids:
                logger.warning("⚠️ No scrape data found in database")
                return False
                
            logger.info(f"📋 Found {len(keep_scrape_ids)} recent scrapes to keep")
            
            # Run cleanup operations
            self.cleanup_jobs(keep_scrape_ids)
            self.cleanup_proposals(keep_scrape_ids)
            self.cleanup_scraped_data(keep_scrape_ids)
            self.cleanup_orphaned_cover_letters()
            self.cleanup_old_analytics(days_to_keep=30)
            self.cleanup_unused_keywords(min_frequency=1)
            
            # Optimize database
            if vacuum:
                self.vacuum_database()
                
            # Get stats after cleanup
            after_stats = self.get_database_stats()
            
            # Log results
            logger.info("🎉 Database cleanup completed!")
            logger.info(f"📊 Cleanup summary: {self.cleanup_stats}")
            logger.info(f"📈 After cleanup: {after_stats}")
            
            # Calculate space saved
            if before_stats.get('db_size_mb') and after_stats.get('db_size_mb'):
                space_saved = before_stats['db_size_mb'] - after_stats['db_size_mb']
                logger.info(f"💾 Space saved: {space_saved:.2f} MB")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up Upwork database')
    parser.add_argument('--keep-scrapes', type=int, default=50, 
                       help='Number of recent scrapes to keep (default: 50)')
    parser.add_argument('--db-path', type=str, default="upwork_data.db",
                       help='Database file path (default: upwork_data.db)')
    parser.add_argument('--no-vacuum', action='store_true',
                       help='Skip database optimization (VACUUM)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No data will be deleted")
        
    # Initialize cleaner
    cleaner = DatabaseCleaner(
        db_path=args.db_path,
        keep_scrapes=args.keep_scrapes
    )
    
    if args.dry_run:
        # Show what would be deleted
        stats = cleaner.get_database_stats()
        keep_ids = cleaner.get_scrapes_to_keep()
        
        print(f"\n📊 Current Database Stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
        print(f"\n🔍 Would keep {len(keep_ids)} scrapes")
        print(f"📋 Keep scrapes: {args.keep_scrapes}")
        print(f"🗑️ This would delete older data beyond the latest {args.keep_scrapes} scrapes")
        
    else:
        # Run actual cleanup
        success = cleaner.run_cleanup(vacuum=not args.no_vacuum)
        
        if success:
            print("\n✅ Database cleanup completed successfully!")
            return 0
        else:
            print("\n❌ Database cleanup failed!")
            return 1

if __name__ == "__main__":
    exit(main())
