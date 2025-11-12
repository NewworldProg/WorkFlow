#!/usr/bin/env python3
"""
Browser Scrape HTML Migrator
Migrates browser scrape HTML files to upwork_jobs.db
"""

import os
import sys
import json
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
import re
import sqlite3

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from data.database_manager import UpworkDatabase

class BrowserScrapeMigrator:
    def __init__(self, db_path="data/upwork_jobs.db"):
        self.db_path = os.path.join(project_root, db_path)
        self.db = UpworkDatabase(self.db_path)
        
    def parse_upwork_html(self, html_content):
        """Parse Upwork job listing HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract jobs from the HTML
        jobs = []
        
        # Find job cards/listings - multiple selectors to try
        job_selectors = [
            '[data-test="JobTile"]',
            '.job-tile',
            '.job-listing',
            '[class*="job"]',
            'article'
        ]
        
        job_elements = []
        for selector in job_selectors:
            elements = soup.select(selector)
            if elements:
                job_elements = elements
                print(f"Found {len(elements)} job elements with selector: {selector}")
                break
        
        if not job_elements:
            print("No job elements found, trying generic parsing...")
            # Try to find any text that looks like job titles
            return self.parse_generic_jobs(soup)
        
        for i, job_elem in enumerate(job_elements[:20]):  # Limit to 20 jobs
            try:
                job_data = self._extract_job_data(job_elem)
                if job_data:
                    jobs.append(job_data)
            except Exception as e:
                print(f"Error parsing job {i}: {e}")
                continue
        
        return jobs
    
    def parse_generic_jobs(self, soup):
        """Generic job parsing when no specific elements found"""
        jobs = []
        
        # Look for text patterns that might be job titles
        title_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b.*(?:Developer|Writer|Designer|Manager|Engineer|Specialist)',
            r'(?:Looking for|Seeking|Need|Want).*(?:Developer|Writer|Designer|Manager|Engineer)',
            r'\$\d+.*(?:hour|project|hourly|fixed)'
        ]
        
        text_content = soup.get_text()
        lines = [line.strip() for line in text_content.split('\n') if len(line.strip()) > 10]
        
        for i, line in enumerate(lines[:50]):  # Check first 50 lines
            for pattern in title_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    job_data = {
                        'job_id': f"generic_{i}_{int(datetime.now().timestamp())}",
                        'title': line[:100],  # First 100 chars
                        'description': line,
                        'budget': self._extract_budget_from_text(line),
                        'hourly_rate': None,
                        'fixed_price': None,
                        'skills': [],
                        'client_location': 'Unknown',
                        'job_type': 'Unknown',
                        'experience_level': 'Unknown',
                        'category': 'Content Writing',
                        'posted_date': datetime.now(),
                        'url': '',
                        'scraped_at': datetime.now()
                    }
                    jobs.append(job_data)
                    break
        
        return jobs[:10]  # Max 10 generic jobs
    
    def _extract_job_data(self, element):
        """Extract job data from HTML element"""
        try:
            # Extract title
            title_selectors = [
                '[data-test="UpCLineClamp JobTitle"]',
                'h4[data-test*="title"]',
                'h3',
                'h4',
                '.job-title',
                'a[href*="job"]'
            ]
            
            title = "Unknown Title"
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title:
                        break
            
            # Extract description
            desc_selectors = [
                '[data-test="job-description"]',
                '.job-description',
                'p',
                '.description'
            ]
            
            description = ""
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    if len(description) > 50:  # Good description
                        break
            
            # Extract budget/rate info
            budget_text = element.get_text()
            budget = self._extract_budget_from_text(budget_text)
            
            # Extract skills
            skills = self._extract_skills(element)
            
            # Extract URL
            url = ""
            link_elem = element.select_one('a[href*="job"]')
            if link_elem:
                url = link_elem.get('href', '')
                if url.startswith('/'):
                    url = 'https://www.upwork.com' + url
            
            # Generate job ID
            job_id = f"browser_{hash(title + description[:100])}_{int(datetime.now().timestamp())}"
            
            job_data = {
                'job_id': job_id,
                'title': title,
                'description': description[:1000],  # Limit description
                'budget': budget,
                'hourly_rate': None,
                'fixed_price': None,
                'skills': skills,
                'client_location': self._extract_location(element),
                'job_type': self._extract_job_type(element),
                'experience_level': self._extract_experience_level(element),
                'category': 'Content Writing',  # Default from HTML content
                'posted_date': datetime.now(),
                'url': url,
                'scraped_at': datetime.now()
            }
            
            return job_data
            
        except Exception as e:
            print(f"Error extracting job data: {e}")
            return None
    
    def _extract_budget_from_text(self, text):
        """Extract budget information from text"""
        # Look for price patterns
        patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*)\s*USD',
            r'Budget:\s*\$?(\d+(?:,\d{3})*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_skills(self, element):
        """Extract skills from job element"""
        skills = []
        
        # Look for skill tags/badges
        skill_selectors = [
            '.skill',
            '.tag',
            '.badge',
            '[data-test*="skill"]'
        ]
        
        for selector in skill_selectors:
            skill_elems = element.select(selector)
            for skill_elem in skill_elems[:10]:  # Max 10 skills
                skill_text = skill_elem.get_text(strip=True)
                if len(skill_text) < 30 and skill_text not in skills:
                    skills.append(skill_text)
        
        return skills
    
    def _extract_location(self, element):
        """Extract client location"""
        location_selectors = [
            '[data-test*="location"]',
            '.location',
            '.client-location'
        ]
        
        for selector in location_selectors:
            loc_elem = element.select_one(selector)
            if loc_elem:
                location = loc_elem.get_text(strip=True)
                if location:
                    return location
        
        return "Unknown"
    
    def _extract_job_type(self, element):
        """Extract job type (hourly vs fixed)"""
        text = element.get_text().lower()
        if 'hourly' in text or '/hr' in text:
            return 'hourly'
        elif 'fixed' in text or 'project' in text:
            return 'fixed'
        return 'Unknown'
    
    def _extract_experience_level(self, element):
        """Extract experience level"""
        text = element.get_text().lower()
        if 'expert' in text or 'senior' in text:
            return 'Expert'
        elif 'intermediate' in text:
            return 'Intermediate'
        elif 'entry' in text or 'beginner' in text:
            return 'Entry Level'
        return 'Unknown'
    
    def migrate_html_files(self, html_dir="data"):
        """Migrate all browser scrape HTML files"""
        html_dir_path = os.path.join(project_root, html_dir)
        
        # Find all browser scrape HTML files
        html_files = []
        for file in os.listdir(html_dir_path):
            if file.startswith('browser_scrape_') and file.endswith('.html'):
                html_files.append(os.path.join(html_dir_path, file))
        
        print(f"Found {len(html_files)} browser scrape HTML files")
        
        total_jobs = 0
        processed_files = []
        
        for html_file in html_files:
            print(f"\nProcessing: {os.path.basename(html_file)}")
            
            try:
                # Read HTML content
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Parse jobs from HTML
                jobs = self.parse_upwork_html(html_content)
                
                if jobs:
                    # First create a scrape record
                    scrape_id = self.db.add_scraped_data(
                        scrape_type='browser',
                        raw_content=html_content[:1000],  # First 1000 chars
                        source_url='file://' + html_file,
                        file_path=html_file,
                        notes=f'Migrated browser scrape from {os.path.basename(html_file)}'
                    )
                    
                    # Save jobs to database
                    saved_count = 0
                    for job in jobs:
                        try:
                            # Format job data for database
                            formatted_job = {
                                'job_uid': job['job_id'],
                                'title': job['title'],
                                'url': job['url'],
                                'posted_time': job['posted_date'].isoformat() if job['posted_date'] else None,
                                'description': job['description'],
                                'skills': job['skills'],
                                'job_info': {
                                    'type': job['job_type'],
                                    'experience_level': job['experience_level'],
                                    'budget': job['budget'],
                                    'hourly_rate_min': None,
                                    'hourly_rate_max': None,
                                    'duration': None
                                }
                            }
                            
                            self.db.add_job(scrape_id, formatted_job)
                            saved_count += 1
                        except Exception as e:
                            print(f"Error saving job: {e}")
                            continue
                    
                    print(f"Migrated {saved_count} jobs from {os.path.basename(html_file)}")
                    total_jobs += saved_count
                    processed_files.append(html_file)
                else:
                    print(f"No jobs found in {os.path.basename(html_file)}")
                    
            except Exception as e:
                print(f"Error processing {html_file}: {e}")
                continue
        
        result = {
            'success': True,
            'total_jobs_migrated': total_jobs,
            'files_processed': len(processed_files),
            'processed_files': [os.path.basename(f) for f in processed_files],
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\nMigration completed!")
        print(f"Total jobs migrated: {total_jobs}")
        print(f"Files processed: {len(processed_files)}")
        
        return result

def main():
    parser = argparse.ArgumentParser(description='Migrate browser scrape HTML to database')
    parser.add_argument('--html-dir', default='data', help='Directory with HTML files')
    
    args = parser.parse_args()
    
    try:
        migrator = BrowserScrapeMigrator()
        result = migrator.migrate_html_files(args.html_dir)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()