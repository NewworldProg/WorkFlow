import os
import sys
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from data.database_manager import UpworkDatabase

# ======= 🧱 function to parse Upwork job listings from HTML =======
# 1. takes HTML content as input (raw data)
# 2. with BeautifulSoup, extracts job elements and their details
# 3. returns structured job data as a list of dictionaries
def parse_upwork_jobs(soup):
    """
    Parse jobs from BeautifulSoup object (optimized - no HTML parsing here)
    """
    # array to hold job data
    jobs = []
    
    # inside job elements append jobs that are based on JobTile article tags
    # Try multiple selectors for different Upwork versions
    job_elements = soup.select('article[data-test="JobTile"]')
    if not job_elements:
        # Try newer format
        job_elements = soup.select('section[data-qa="job-tile"]')
    if not job_elements:
        # Try alternative selectors
        job_elements = soup.select('[data-qa="job-tile"]')
    
    # print number of job elements found
    print(f'🔍 Found {len(job_elements)} job elements')
    
    # loop through each job element and extract data
    for job_element in job_elements:
        # data dictionary for each job
        job_data = {}
        
        # Extract job UID
        # ===================================== Extract job UID ===========================
        job_uid = job_element.get('data-ev-job-uid', '')
        if job_uid:
            job_data['job_uid'] = job_uid

        # ========================== Extract job title and URL ==============================
        title_link = job_element.select_one('h2.job-tile-title a[data-test="job-tile-title-link"]')
        if not title_link:
            # Try alternative selectors for newer version
            title_link = job_element.select_one('h2 a[data-qa="job-title"]')
        if not title_link:
            # Try more generic selectors
            title_link = job_element.select_one('h2 a')
            if not title_link:
                title_link = job_element.select_one('a[data-test="job-tile-title-link"]')
                if not title_link:
                    title_link = job_element.select_one('a[data-qa="job-title"]')
        if title_link:
            job_data['title'] = title_link.get_text(strip=True)
            href = title_link.get('href', '')
            if href and not href.startswith('http'):
                job_data['url'] = f'https://www.upwork.com{href}'
            else:
                job_data['url'] = href

        # ========================== Extract posted time ===========================
        posted_time = job_element.select_one('small[data-test="job-pubilshed-date"]')
        if not posted_time:
            posted_time = job_element.select_one('small')
        
        if posted_time:
            job_data['posted_time'] = posted_time.get_text(strip=True)

        # =============== Extract job info (type, experience level, budget) ================
        job_info = {}
        job_info_items = job_element.select('ul[data-test="JobInfo"] li')
        if not job_info_items:
            job_info_items = job_element.select('ul li')
        
        for item in job_info_items:
            text = item.get_text(strip=True)
            # ==========================  fixed price ===========================
            if 'Fixed price' in text:
                job_info['type'] = 'Fixed price'
            # ==========================  hourly rate ===========================
            elif 'Hourly:' in text:
                job_info['type'] = 'Hourly'
                # Extract hourly rate
                rate_match = re.search(r'Hourly:\s*\$([0-9,.]+)\s*-\s*\$([0-9,.]+)', text)
                if rate_match:
                    job_info['hourly_rate_min'] = rate_match.group(1)
                    job_info['hourly_rate_max'] = rate_match.group(2)
            # ==========================  budget ===========================
            elif 'Est. budget:' in text:
                budget_match = re.search(r'Est\. budget:\s*\$([0-9,.]+)', text)
                if budget_match:
                    job_info['budget'] = budget_match.group(1)
            # ==========================  experience level ===========================
            elif 'Entry Level' in text or 'Intermediate' in text or 'Expert' in text:
                if 'Entry Level' in text:
                    job_info['experience_level'] = 'Entry Level'
                elif 'Intermediate' in text:
                    job_info['experience_level'] = 'Intermediate'
                elif 'Expert' in text:
                    job_info['experience_level'] = 'Expert'
            elif 'Est. time:' in text:
                job_info['duration'] = text.replace('Est. time:', '').strip()
        
        job_data['job_info'] = job_info

        # ========================== Extract description ===========================
        description_elem = job_element.select_one('[data-test="UpCLineClamp JobDescription"] .air3-line-clamp p')
        if not description_elem:
            description_elem = job_element.select_one('.air3-line-clamp p')
        if not description_elem:
            description_elem = job_element.select_one('p')
        
        if description_elem:
            job_data['description'] = description_elem.get_text(strip=True)

        # ========================== Extract skills/tokens ===========================
        skills = []
        skill_elements = job_element.select('[data-test="TokenClamp JobAttrs"] .air3-token span')
        if not skill_elements:
            skill_elements = job_element.select('.air3-token span')
        
        for skill_elem in skill_elements:
            skill_text = skill_elem.get_text(strip=True)
            if skill_text and skill_text not in ['+1', '+2', '+3', '+4', '+5']:  # Skip "more" indicators
                skills.append(skill_text)
        job_data['skills'] = skills
        
        # Only add job if it has at least a title
        if job_data.get('title'):
            jobs.append(job_data)
    
    return jobs
# ======= 🧱 function to extract metadata from HTML =======
def extract_metadata(soup):
    """
    Extract metadata from BeautifulSoup object (optimized - no HTML parsing here)
    """
    # metadata of the page currently being parsed
    metadata = {
        'title': soup.title.get_text(strip=True) if soup.title else '',
        'url': '',
        'scraped_at': datetime.now().isoformat(),
        'total_jobs_found': 0,
        'jobs_count_text': ''
    }
    
    # Try to extract URL from canonical link
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical:
        metadata['url'] = canonical.get('href', '')
    
    # Extract jobs count from the page
    jobs_count_elem = soup.select_one('[data-test="JobsCountQA JobsCount"]')
    if jobs_count_elem:
        count_text = jobs_count_elem.get_text(strip=True)
        metadata['jobs_count_text'] = count_text
        # Extract number from text like "5,679 jobs found"
        count_match = re.search(r'([\d,]+)\s+jobs?\s+found', count_text)
        if count_match:
            try:
                metadata['total_jobs_on_page'] = int(count_match.group(1).replace(',', ''))
            except ValueError:
                pass
    
    return metadata
# ======= 🗃️ Function that parses file and orchestrates other functions =======
def parse_html_file(file_path):

    # open and read HTML file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # inside variable call BeautifulSoup amd parse HTML file
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # inside variable call
        # 1. parse_upwork_jobs to get elements
        jobs = parse_upwork_jobs(soup)
        # 2. extract_metadata to get page metadata
        metadata = extract_metadata(soup)
        
        metadata['total_jobs_found'] = len(jobs)
        metadata['source_file'] = os.path.basename(file_path)
        # return combined result
        return {
            'metadata': metadata,
            'jobs': jobs,
            'parsing_stats': {
                'html_length': len(html_content),
                'jobs_extracted': len(jobs),
                'parsing_successful': len(jobs) > 0
            }
        }
    # handle exceptions and return error info
    except Exception as e:
        return {
            'error': str(e),
            'source_file': os.path.basename(file_path),
            'parsing_stats': {
                'parsing_successful': False
            }
        }

def main():

    # inside varable call argparse to handle powershell arguments
    parser = argparse.ArgumentParser(description='Parse Upwork HTML files and optionally import to DB')
    parser.add_argument('--input', '-i', help='Input HTML file or directory (default: data/data_raw)', default=None)
    parser.add_argument('--import-db', action='store_true', help='Import parsed JSON into SQLite DB')
    args = parser.parse_args()

    print('🔍 UPWORK DATA PARSER')
    print('=====================')
    # Setup directories
    base_dir = Path(__file__).parent
    data_raw_dir = base_dir / 'data' / 'data_raw'
    parsed_dir = base_dir / 'data' / 'data_parsed'
    parsed_dir.mkdir(exist_ok=True)

    # Determine files to parse
    input_path = Path(args.input) if args.input else data_raw_dir
    html_files = []
    # Check if input path is file or directory
    if input_path.is_file():
        html_files = [input_path]
    elif input_path.is_dir():
        html_files = list(input_path.glob('*.html'))
    else:
        print(f'❌ Input path not found: {input_path}')
        return

    if not html_files:
        print('❌ No HTML files found to parse')
        return

    print(f'📁 Found {len(html_files)} HTML files to parse')

    total_jobs = 0
    successful_parses = 0
    # inside variable call database manager to handle DB import
    db = UpworkDatabase() if args.import_db else None
    # loop through each HTML file
    for html_file in html_files:
        print(f'\n📄 Processing: {html_file.name}')
        # call parse_html_file function that orchestrates parsing
        result = parse_html_file(html_file)
        # error handling
        if 'error' not in result:
            jobs_count = result['parsing_stats']['jobs_extracted']
            print(f'✅ Extracted {jobs_count} jobs')
            total_jobs += jobs_count
            successful_parses += 1
        else:
            print(f'❌ Error: {result["error"]}')

        # Save parsed data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'parsed_{html_file.stem}_{timestamp}.json'
        output_path = parsed_dir / output_filename
        # save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f'💾 Saved to: data/data_parsed/{output_filename}')

        # Optionally import into DB
        if db:
            try:
                scrape_id, jobs_added = db.import_from_json_file(str(output_path), scrape_type='browser')
                print(f'📥 Imported to DB: {jobs_added} jobs (scrape_id={scrape_id})')
            except Exception as e:
                print(f'❌ Failed to import into DB: {e}')

    # Summary
    print(f'\n📊 PARSING SUMMARY')
    print(f'================')
    print(f'Files processed: {len(html_files)}')
    print(f'Successful parses: {successful_parses}')
    print(f'Total jobs extracted: {total_jobs}')
    print(f'Results saved in: data/data_parsed/')

if __name__ == '__main__':
    main()