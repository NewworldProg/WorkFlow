"""
Script to save latest raw HTML file to database
Called from n8n workflow after JS scraper
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

from data.database_manager import UpworkDatabase # Import custom class for database management

"""
Script to save latest raw HTML file to database
Called from n8n workflow after JS scraper
"""
import sys
import os
import json
from datetime import datetime
from data.database_manager import UpworkDatabase # Import custom class for database management 

# Set UTF-8 encoding for console output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# function to find latest HTML file and return its path
# 1. find path to data/data_raw/
# 2 inside var put all HTML files in that directory
# 3 find latest by modification time
# 4. return path to latest HTML file if it exists latest_filepath 
def find_latest_html_file():
    """Find latest HTML file in data_raw directory"""
    try:
        # inside data_raw_dir save path to data/data_raw/
        data_raw_dir = os.path.join("data", "data_raw")   
        # log error and return None if data_raw_dir does not exist
        if not os.path.exists(data_raw_dir):
            print(f"❌ Directory {data_raw_dir} does not exist")
            return None, f"data_raw directory not found"
        
        # Find HTML files, by listing all files in data_raw_dir that end with .html
        html_files = [f for f in os.listdir(data_raw_dir) if f.endswith('.html')]
        # log error and return None if no HTML files found
        if not html_files:
            print("❌ No HTML files found in data_raw")
            return None, "No HTML files found"
        
        # placeholder for latest file and time
        latest_file = None
        latest_time = 0
        # Iterate through files inside variable (html_files) that holds HTML files
        for filename in html_files:
            filepath = os.path.join(data_raw_dir, filename)
            mtime = os.path.getmtime(filepath)
            if mtime > latest_time:
                latest_time = mtime
                latest_file = filename
        # log error and return None
        if not latest_file:
            print("❌ Could not determine latest file")
            return None, "Could not find latest file"
        
        # Return full path to latest file by joining data_raw_dir and latest_file or None if not found
        latest_filepath = os.path.join(data_raw_dir, latest_file)
        print(f"📁 Found latest file: {latest_file}")
        return latest_filepath, None
        # log error in except block
    except Exception as e:
        error_msg = f"Error finding latest HTML file: {str(e)}"
        print(f"❌ {error_msg}")
        return None, error_msg
# function to save HTML file to database
# 1. initialize database component
# 2. inside var put filepath of HTML file
# 3. from HTML that is found at html_filepath read content
# 4. inside var put content length
# 5. inside var put boolean if job content is found
# 6. save to database and get scrape_id
# 7. return result dict and None for error
# 8. log error in except block
def save_html_to_database(html_filepath):
    """Save HTML file to database and return result"""
    try:
        # inside var put database component
        db = UpworkDatabase()
        
        # inside var put filepath of HTML file
        filename = os.path.basename(html_filepath)
        
        # from HTML that is found at html_filepath read content and put into var(html_content)
        with open(html_filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # inside var put content length
        content_length = len(html_content)
        # inside var put boolean if job content is found
        has_job_content = 'job-tile' in html_content or 'job' in html_content.lower()
        
        # Save to database and get scrape_id
        scrape_id = db.add_scraped_data(
            scrape_type="browser",
            source_url="https://www.upwork.com/search/jobs/",
            raw_content=html_content,
            file_path=html_filepath,
            notes=f"Browser scrape from {filename} - {content_length} chars"
        )
        
        # Print metadata
        print(f"✅ HTML saved to database with scrape_id: {scrape_id}")
        print(f"📁 File: {filename}")
        print(f"📊 Content length: {content_length:,} characters")
        print(f"🔍 Contains job content: {has_job_content}")
        
        # Prepare result
        result = {
            "success": True,
            "scrape_id": scrape_id,
            "filename": filename,
            "content_length": content_length,
            "has_job_content": has_job_content,
            "timestamp": datetime.now().isoformat()
        }
        
        return result, None
        # log error in except block
    except Exception as e:
        error_msg = f"Error saving HTML to database: {str(e)}"
        print(f"❌ {error_msg}")
        return None, error_msg

# main function - find latest HTML and save to database 
# 1. for save_html_to_database take input from find_latest_html_file
# 2. with html_filepath call save_html_to_database
# 3. Return JSON for n8n stdout
def main():
    """Main function - find latest HTML and save to database"""
    try:
        # for save_html_to_database take input from find_latest_html_file 
        html_filepath, error = find_latest_html_file()
        if error:
            result = {
                "success": False,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
            print(json.dumps(result))
            return result
        
        # with html_filepath call save_html_to_database
        result, error = save_html_to_database(html_filepath)
        if error:
            result = {
                "success": False,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
            print(json.dumps(result))
            return result
        
        # Return JSON for n8n stdout
        print(json.dumps(result))
        return result
        
    except Exception as e:
        error_msg = f"Critical error in main: {str(e)}"
        print(f"💥 {error_msg}")
        result = {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(result))
        return result

if __name__ == "__main__":
    main()