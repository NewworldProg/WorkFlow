"""
Parse HTML from database (without saving jobs)
Returns parsed jobs as JSON for next node
"""
import sys
import os
import json
from datetime import datetime
import tempfile

# Set UTF-8 encoding for console output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Import database manager file and class that holds functions
from data.database_manager import UpworkDatabase

# Import existing parser (now in same directory)
from upwork_data_parser import parse_html_file
# 1. Initialize database using UpworkDatabase class
# 2. Get latest raw HTML from database
# 3. open temporary file to write HTML content
# 4. use parse_html_file function from upwork_data_parser.py and UpworkDataParser class to parse HTML file
# 5. extract jobs from parsed result
# 6. return jobs as JSON file for n8n
def parse_html_only():
    """Parse latest HTML from database and return jobs as JSON"""
    try:
        # Initialize database
        db = UpworkDatabase()
        
        # Get latest raw HTML from database
        import sqlite3
        # Connect to database using UpworkDatabase and db_path
        conn = sqlite3.connect(db.db_path)
        # Create cursor
        cursor = conn.cursor()
        # query to enter table scraped_data and get latest browser scrape
        # by selecting scrape_type = 'browser' ordered by scrape_timestamp descending limit 1
        cursor.execute('''
            SELECT id, raw_content, file_path, scrape_timestamp 
            FROM scraped_data 
            WHERE scrape_type = 'browser' 
            ORDER BY scrape_timestamp DESC 
            LIMIT 1
        ''')
        # fetch one row
        row = cursor.fetchone()
        # check if there is raw HTML content
        if not row:
            print("❌ No browser scrape data found in database")
            conn.close()
            return {"success": False, "error": "No raw HTML data found"}
        # inside row put content of columns
        scrape_id, html_content, file_path, scrape_timestamp = row
        conn.close()
        # log it
        print(f"📥 Processing scrape_id: {scrape_id}")
        print(f"📊 Content length: {len(html_content):,} characters")
        print(f"⏰ Scraped at: {scrape_timestamp}")
        
        # inside temp_file_path write HTML content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(html_content)
            # set filepath to temp file name
            temp_file_path = temp_file.name
        
        try:
            # try to Parse using 
            # upwork_data_parser.py class UpworkDataParser and its function parse_html_file
            parse_result = parse_html_file(temp_file_path)
            
            # Extract jobs from result
            if isinstance(parse_result, dict) and 'jobs' in parse_result:
                jobs = parse_result['jobs']
                # Log number of jobs found
                print(f"🔍 Parser returned {len(jobs)} jobs")
            else:
                # if parse_result is list assume it's list of jobs
                jobs = parse_result if isinstance(parse_result, list) else []
                print(f"🔍 Parser returned {len(jobs)} jobs (direct list)")
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        # if no jobs found
        if not jobs:
            # log it
            print("⚠️ No jobs found in HTML content")
            return {
                "success": True,
                "scrape_id": scrape_id,
                "jobs": [],
                "message": "No jobs found in content"
            }
        # log it
        print(f"✅ Successfully parsed {len(jobs)} jobs from database!")
        # prepare result for next node
        result = {
            "success": True,
            "scrape_id": scrape_id,
            "jobs": jobs,
            "jobs_count": len(jobs),
            "content_length": len(html_content),
            "timestamp": datetime.now().isoformat()
        }
        # make result JSON serializable so that n8n can use it
        # Save jobs to temp file for next node (in n8n this would be passed automatically)
        temp_jobs_file = "temp_parsed_jobs.json"
        with open(temp_jobs_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # Return JSON for n8n
        print(json.dumps(result))
        return result
        # log error in except block
    except Exception as e:
        error_msg = f"Error parsing HTML: {str(e)}"
        print(f"❌ {error_msg}")
        result = {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(result))
        return result

if __name__ == "__main__":
    parse_html_only()