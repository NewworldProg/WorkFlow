"""
Get latest job without cover letter from database
For AI cover letter generation workflow
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
# Import database_manager file and UpworkDatabase class from it and tables jobs and cover_letters
from data.database_manager import UpworkDatabase


# Function to get latest job without cover letter
# 1 . connect to database using UpworkDatabase class and tables jobs and cover_letters
def get_latest_job_without_cover_letter():
    """Get latest job without cover letter for AI generation"""
    try:
        # Initialize database
        db = UpworkDatabase()
        
        # Get latest job without cover letter
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Find jobs that don't have cover letters
        # query j.id from jobs table and lookup in cover_letters table for FOREIGN KEY job_id
        cursor.execute('''
            SELECT j.id, j.job_title, j.description, j.job_url, j.budget, 
                   j.skills, j.job_type, j.experience_level, j.parsed_timestamp
            FROM jobs j
            LEFT JOIN cover_letters cl ON j.id = cl.job_id
            WHERE cl.job_id IS NULL
            ORDER BY j.parsed_timestamp DESC
            LIMIT 1
        ''')
        # fetch one row
        row = cursor.fetchone()
        # error and return if no row found
        if not row:
            print("❌ No jobs found without cover letters")
            conn.close()
            return {"success": False, "message": "No pending jobs found"}
        # unpack row inside variables
        job_id, title, description, url, budget, skills, job_type, experience_level, parsed_timestamp = row
        conn.close()
        
        # Parse skills safely
        try:
            skills_list = json.loads(skills) if skills else []
        except:
            skills_list = []
        # Log found job details
        print(f"📋 Found job without cover letter:")
        print(f"🆔 Job ID: {job_id}")
        print(f"📝 Title: {title[:50]}...")
        print(f"💰 Budget: {budget}")
        print(f"🏷️ Type: {job_type}")
        print(f"📊 Skills: {len(skills_list)} skills")
        # log it as JSON result for n8n stdout
        result = {
            "success": True,
            "job": {
                "job_id": job_id,
                "title": title,
                "description": description,
                "url": url,
                "budget": budget,
                "skills": skills_list,
                "job_type": job_type,
                "experience_level": experience_level,
                "parsed_timestamp": parsed_timestamp
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Save job data for next node (in n8n this would be passed automatically)
        temp_job_file = "temp_selected_job.json"
        with open(temp_job_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # Return JSON for n8n
        print(json.dumps(result))
        return result
        
    except Exception as e:
        error_msg = f"Error getting job: {str(e)}"
        print(f"❌ {error_msg}")
        result = {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(result))
        return result

if __name__ == "__main__":
    get_latest_job_without_cover_letter()