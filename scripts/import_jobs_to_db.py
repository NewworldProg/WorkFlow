"""
Import parsed jobs to database
Takes jobs from previous node and saves to database
"""
import sys
import os
import json
from datetime import datetime

# Set UTF-8 encoding for console output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Import database manager file and class UpworkDatabase that holds functions
from data.database_manager import UpworkDatabase
# function to import jobs to database
def import_jobs_to_db():
    """Import jobs from n8n previous node to database"""
    try:
        # in var put database class
        db = UpworkDatabase()
        
        # Get latest scrape_id for linking
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        # query to get latest scrape_id from scraped_data table
        cursor.execute('''
            SELECT id FROM scraped_data 
            WHERE scrape_type = 'browser' 
            ORDER BY scrape_timestamp DESC 
            LIMIT 1
        ''')
        # fetch one row
        row = cursor.fetchone()
        # log error and return if no scrape data found
        if not row:
            print("❌ No scrape data found")
            conn.close()
            return {"success": False, "error": "No scrape data found"}
        
        # scrape_id is first column of row, get its value
        scrape_id = row[0]
        conn.close()
        # inside var put file path to temporary jobs file
        # Get jobs from previous node (in n8n this would be passed automatically)
        temp_jobs_file = "temp_parsed_jobs.json"
        # read jobs from temp file and get 'jobs' key
        if os.path.exists(temp_jobs_file):
            with open(temp_jobs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                jobs = data.get('jobs', [])
            # Clean up temp file
            os.unlink(temp_jobs_file)
        else:
            print("⚠️ No jobs data from previous node (testing mode)")
            return {
                "success": False,
                "error": "No jobs data from previous node",
                "note": "In n8n, this would receive data from Parse HTML node"
            }
        
        print(f"📥 Importing {len(jobs)} jobs to database...")
        print(f"🔗 Linking to scrape_id: {scrape_id}")
        
        # Save jobs to database
        jobs_added = 0
        for job in jobs:
            try:
                # Add job to database using add_job method, also link to scrape_id
                job_id = db.add_job(scrape_id, job)
                jobs_added += 1
                print(f"✅ Added job {job_id}: {job.get('title', 'Unknown title')[:50]}...")
            except Exception as e:
                print(f"⚠️ Error adding job: {e}")
                continue
        
        print(f"🎉 Successfully imported {jobs_added} jobs to database!")
        # prepare result
        result = {
            "success": True,
            "scrape_id": scrape_id,
            "jobs_imported": jobs_added,
            "jobs_total": len(jobs),
            "timestamp": datetime.now().isoformat()
        }
        
        # Return JSON for n8n
        print(json.dumps(result))
        return result
        # log error in except block
    except Exception as e:
        error_msg = f"Error importing jobs: {str(e)}"
        print(f"❌ {error_msg}")
        result = {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(result))
        return result

if __name__ == "__main__":
    import_jobs_to_db()