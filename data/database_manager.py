"""
SQLite Database Manager for Upwork Scraper
==========================================
Manages scraped data, parsed data, and analytics
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

# class to call database functions
class UpworkDatabase:
    def __init__(self, db_path: str = "upwork_data.db"):
        # Initialize database working directory
        self.db_path = db_path
        # Create database tables if they don't exist
        self.init_database()
    # ========================= 🧱🪣 database creation function =========================
    def init_database(self):
        # inside variable and working directory Create sqlite database
        conn = sqlite3.connect(self.db_path)
        # connect cursor to database
        cursor = conn.cursor()
        
        # ==== scraped_data =======
        # Table for raw scraped data
        # 1. scrape_type: 'browser' or 'api'
        # 2. source_url: URL of the scraped page
        # 3. scrape_timestamp: timestamp of the scrape
        # 4. raw_content: raw HTML or JSON content
        # 5. file_path: path to saved file if applicable
        # 6. status: 'active', 'archived', 'deleted'
        # 7. notes: any additional notes 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scrape_type TEXT NOT NULL,  -- 'browser' or 'api'
                source_url TEXT,
                scrape_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                raw_content TEXT NOT NULL,
                file_path TEXT,
                status TEXT DEFAULT 'active',
                notes TEXT
            )
        ''')

        # =========== parsed data tables =============
        # Table for parsed job data
        # 1. scrape_id: foreign key to scraped_data
        # 2. job_uid: unique job identifier
        # 3. job_title: title of the job
        # 4. job_url: URL of the job posting
        # 5. posted_time: when the job was posted
        # 6. job_type: 'Fixed price' or 'Hourly'
        # 7. experience_level: required experience level
        # 8. budget: total budget for fixed price jobs
        # 9. hourly_rate_min: minimum hourly rate for hourly jobs
        # 10. hourly_rate_max: maximum hourly rate for hourly jobs
        # 11. duration: expected duration of the job
        # 12. skills: JSON array of required skills
        # 13. description: full job description
        # 14. parsed_timestamp: timestamp when the job was parsed
        # 15. FOREIGN KEY = scraped_data (id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scrape_id INTEGER,
                job_uid TEXT UNIQUE,
                job_title TEXT NOT NULL,
                job_url TEXT,
                posted_time TEXT,
                job_type TEXT,  -- 'Fixed price' or 'Hourly'
                experience_level TEXT,
                budget TEXT,
                hourly_rate_min TEXT,
                hourly_rate_max TEXT,
                duration TEXT,
                skills TEXT,  -- JSON array of skills
                description TEXT,
                parsed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scrape_id) REFERENCES scraped_data (id)
            )
        ''')
        # ============== proposal data =================
        # Table for parsed proposal data
        # 1. scrape_id: foreign key to scraped_data
        # 2. job_title: title of the job
        # 3. proposal_text: full text of the proposal
        # 4. bid_amount: amount bid for the job
        # 5. proposal_status: 'submitted', 'accepted', 'rejected'
        # 6. submitted_date: date when the proposal was submitted
        # 7. client_feedback: feedback from the client if any
        # 8. response_rate: client's response rate
        # 9. parsed_timestamp: timestamp when the proposal was parsed
        # 10. FOREIGN KEY = scraped_data (id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scrape_id INTEGER,
                job_title TEXT,
                proposal_text TEXT,
                bid_amount TEXT,
                proposal_status TEXT,
                submitted_date DATETIME,
                client_feedback TEXT,
                response_rate TEXT,
                parsed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scrape_id) REFERENCES scraped_data (id)
            )
        ''')
        
        # ============== analytics and metrics =================
        # Table for analytics and metrics
        # 1. metric_name: name of the metric
        # 2. metric_value: value of the metric
        # 3. metric_date: date of the metric
        # 4. category: 'jobs', 'proposals', 'performance'
        # 5. created_timestamp: timestamp when the metric was recorded
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value TEXT NOT NULL,
                metric_date DATE DEFAULT CURRENT_DATE,
                category TEXT,  -- 'jobs', 'proposals', 'performance'
                created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ============== keywords and search patterns =================
        # Table for keywords and search patterns
        # 1. keyword: the keyword or pattern
        # 2. category: category of the keyword
        # 3. frequency: how often the keyword appears
        # 4. last_seen: last seen timestamp
        # 5. importance_score: score indicating importance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL UNIQUE,
                category TEXT,
                frequency INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                importance_score REAL DEFAULT 1.0
            )
        ''')
        
        # Table for AI-generated cover letters
        # 1. job_id: foreign key to jobs
        # 2. ai_provider: 'openai' or 'local_ai'
        # 3. cover_letter_text: full text of the cover letter
        # 4. generated_timestamp: timestamp when the cover letter was generated
        # 5. status: 'generated', 'edited', 'sent'
        # 6. rating: user rating 1-5
        # 7. notes: any additional notes
        # 8. FOREIGN KEY = jobs (id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cover_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                ai_provider TEXT NOT NULL,  -- 'openai' or 'local_ai'
                cover_letter_text TEXT NOT NULL,
                generated_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'generated',  -- 'generated', 'edited', 'sent'
                rating INTEGER,  -- User rating 1-5
                notes TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()

    # ======================== 🛸➕🪣 function to add scraped RAW data ========================
    def add_scraped_data(self, scrape_type: str, raw_content: str,
                        source_url: str = None, file_path: str = None,
                        notes: str = None) -> int:
        # create a new entry for raw scraped data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # insert scraped data into table scraped_data
        # collumns where data will be inserted
        # placeholders for values
        # execute insert statement
        cursor.execute('''
            INSERT INTO scraped_data (scrape_type, source_url, raw_content, file_path, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (scrape_type, source_url, raw_content, file_path, notes))
        
        scrape_id = cursor.lastrowid
        conn.commit()
        conn.close()
        # return the ID of the newly inserted scrape data
        return scrape_id
    
    # ======================== 🛸➕🪣 function to add parsed job data ========================
    def add_job(self, scrape_id: int, job_data: Dict) -> int:
        """Add parsed job data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert skills list to JSON string
        skills_json = json.dumps(job_data.get('skills', []))
        
        cursor.execute('''INSERT OR IGNORE INTO jobs (scrape_id, job_uid, job_title, job_url, posted_time, 
                             job_type, experience_level, budget, hourly_rate_min, hourly_rate_max,
                             duration, skills, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            scrape_id,
            job_data.get('job_uid'),
            job_data.get('title'),
            job_data.get('url'),
            job_data.get('posted_time'),
            job_data.get('job_info', {}).get('type'),
            job_data.get('job_info', {}).get('experience_level'),
            job_data.get('job_info', {}).get('budget'),
            job_data.get('job_info', {}).get('hourly_rate_min'),
            job_data.get('job_info', {}).get('hourly_rate_max'),
            job_data.get('job_info', {}).get('duration'),
            skills_json,
            job_data.get('description')
        ))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id
    
    # ======================== 🛸➕🪣 function to add parsed proposal data ========================
    def add_proposal(self, scrape_id: int, proposal_data: Dict) -> int:
        """Add parsed proposal data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO proposals (scrape_id, job_title, proposal_text, bid_amount,
                                 proposal_status, submitted_date, client_feedback, response_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            scrape_id,
            proposal_data.get('job_title'),
            proposal_data.get('text'),
            proposal_data.get('bid_amount'),
            proposal_data.get('status'),
            proposal_data.get('submitted_date'),
            proposal_data.get('client_feedback'),
            proposal_data.get('response_rate')
        ))
        
        proposal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return proposal_id
    
    # ======================== 🛸➕🪣 function to add cover letter data ========================
    def add_cover_letter(self, job_id: int, ai_provider: str, cover_letter_text: str, 
                        notes: str = None) -> int:
        """Add AI-generated cover letter to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''INSERT INTO cover_letters (job_id, ai_provider, cover_letter_text, notes)
                         VALUES (?, ?, ?, ?)''', (job_id, ai_provider, cover_letter_text, notes))
        
        cover_letter_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return cover_letter_id
    
    def get_cover_letters_for_job(self, job_id: int) -> List[Dict]:
        """Get all cover letters for a specific job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''SELECT id, ai_provider, cover_letter_text, generated_timestamp, 
                         status, rating, notes FROM cover_letters 
                         WHERE job_id = ? ORDER BY generated_timestamp DESC''', (job_id,))
        
        cover_letters = []
        for row in cursor.fetchall():
            cover_letters.append({
                'id': row[0],
                'ai_provider': row[1],
                'cover_letter_text': row[2],
                'generated_timestamp': row[3],
                'status': row[4],
                'rating': row[5],
                'notes': row[6]
            })
        
        conn.close()
        return cover_letters
    
    # ======================== 🛸➕🪣 function to get recent cover letters ========================
    def get_recent_cover_letters(self, limit: int = 20) -> List[Dict]:
        """Get recent cover letters with job information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''SELECT cl.id, cl.ai_provider, cl.cover_letter_text, cl.generated_timestamp,
                         cl.status, cl.rating, cl.notes, j.job_title, j.job_type, j.budget
                         FROM cover_letters cl
                         JOIN jobs j ON cl.job_id = j.id
                         ORDER BY cl.generated_timestamp DESC LIMIT ?''', (limit,))
        
        cover_letters = []
        for row in cursor.fetchall():
            cover_letters.append({
                'id': row[0],
                'ai_provider': row[1],
                'cover_letter_text': row[2],
                'generated_timestamp': row[3],
                'status': row[4],
                'rating': row[5],
                'notes': row[6],
                'job_title': row[7],
                'job_type': row[8],
                'budget': row[9]
            })
        
        conn.close()
        return cover_letters
    
    def update_cover_letter_status(self, cover_letter_id: int, status: str, rating: int = None, notes: str = None):
        """Update cover letter status, rating, and notes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''UPDATE cover_letters SET status = ?, rating = ?, notes = ? 
                         WHERE id = ?''', (status, rating, notes, cover_letter_id))
        
        conn.commit()
        conn.close()
    
    def delete_cover_letter(self, cover_letter_id: int):
        """Delete a cover letter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cover_letters WHERE id = ?', (cover_letter_id,))
        
        conn.commit()
        conn.close()
    
    # ======================== 🛸➕🪣 function to get dashboard statistics ========================
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total scrapes
        cursor.execute("SELECT COUNT(*) FROM scraped_data WHERE status = 'active'")
        stats['total_scrapes'] = cursor.fetchone()[0]
        
        # Total jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        stats['total_jobs'] = cursor.fetchone()[0]
        
        # Total proposals
        cursor.execute("SELECT COUNT(*) FROM proposals")
        stats['total_proposals'] = cursor.fetchone()[0]
        
        # Recent scrapes (last 7 days)
        cursor.execute('''
            SELECT COUNT(*) FROM scraped_data 
            WHERE scrape_timestamp >= datetime('now', '-7 days')
            AND status = 'active'
        ''')
        stats['recent_scrapes'] = cursor.fetchone()[0]
        
        # Jobs by type
        cursor.execute('''
            SELECT job_type, COUNT(*) FROM jobs 
            WHERE job_type IS NOT NULL 
            GROUP BY job_type
        ''')
        stats['jobs_by_type'] = dict(cursor.fetchall())
        
        # Top skills (from last 30 days)
        cursor.execute('''
            SELECT skills FROM jobs 
            WHERE parsed_timestamp >= datetime('now', '-30 days')
            AND skills IS NOT NULL AND skills != '[]'
        ''')
        
        skill_counts = {}
        for (skills_json,) in cursor.fetchall():
            try:
                skills = json.loads(skills_json)
                for skill in skills:
                    if skill:
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1
            except:
                continue
        
        # Top 10 skills
        stats['top_skills'] = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Scrapes by day (last 7 days)
        cursor.execute('''
            SELECT DATE(scrape_timestamp) as date, COUNT(*) as count
            FROM scraped_data 
            WHERE scrape_timestamp >= datetime('now', '-7 days')
            AND status = 'active'
            GROUP BY DATE(scrape_timestamp)
            ORDER BY date
        ''')
        stats['scrapes_by_day'] = cursor.fetchall()
        
        conn.close()
        return stats
    
    def get_recent_jobs(self, limit: int = 20) -> List[Dict]:
        """Get recent jobs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT job_title, job_type, budget, hourly_rate_min, hourly_rate_max,
                   experience_level, posted_time, parsed_timestamp, skills
            FROM jobs 
            ORDER BY parsed_timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        jobs = []
        for row in cursor.fetchall():
            # Parse skills safely
            try:
                skills = json.loads(row[8]) if row[8] else []
            except:
                skills = []
                
            jobs.append({
                'title': row[0],
                'type': row[1],
                'budget': row[2],
                'hourly_min': row[3],
                'hourly_max': row[4],
                'experience_level': row[5],
                'posted_time': row[6],
                'parsed_timestamp': row[7],
                'skills': skills[:5]  # First 5 skills only
            })
        
        conn.close()
        return jobs
    
    def get_detailed_jobs(self, limit: int = 20) -> List[Dict]:
        """Get detailed jobs for card display"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT job_uid, job_title, job_url, posted_time, job_type, 
                   experience_level, budget, hourly_rate_min, hourly_rate_max,
                   duration, skills, description, parsed_timestamp
            FROM jobs 
            ORDER BY parsed_timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        jobs = []
        for row in cursor.fetchall():
            # Parse skills safely
            try:
                skills = json.loads(row[10]) if row[10] else []
            except:
                skills = []
                
            jobs.append({
                'job_uid': row[0],
                'job_title': row[1],
                'job_url': row[2],
                'posted_time': row[3],
                'job_type': row[4],
                'experience_level': row[5],
                'budget': row[6],
                'hourly_rate_min': row[7],
                'hourly_rate_max': row[8],
                'duration': row[9],
                'skills': skills,
                'description': row[11],
                'parsed_timestamp': row[12]
            })
        
        conn.close()
        return jobs
    # ======================== 🛸➕🪣 function to get latest jobs for n8n workflow ========================
    def get_latest_jobs(self, limit: int = 20) -> List[Tuple]:
        """Get latest jobs as tuples (id, title, description) for n8n workflow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, job_title, description
            FROM jobs 
            ORDER BY parsed_timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        jobs = cursor.fetchall()
        conn.close()
        return jobs
    
    def get_recent_proposals(self, limit: int = 20) -> List[Dict]:
        """Get recent proposals"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT job_title, bid_amount, proposal_status, 
                   submitted_date, client_feedback, parsed_timestamp
            FROM proposals 
            ORDER BY parsed_timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        proposals = []
        for row in cursor.fetchall():
            proposals.append({
                'job_title': row[0],
                'bid_amount': row[1],
                'status': row[2],
                'submitted_date': row[3],
                'client_feedback': row[4],
                'parsed_timestamp': row[5]
            })
        
        conn.close()
        return proposals
    
    # ======================== 🛸➕🪣 function to search jobs with filters ========================
    def search_jobs(self, keyword: str = None, job_type: str = None, 
                   min_budget: float = None) -> List[Dict]:
        """Search jobs with filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        if keyword:
            query += " AND (job_title LIKE ? OR description LIKE ? OR skills LIKE ?)"
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        if job_type:
            query += " AND job_type = ?"
            params.append(job_type)
        
        query += " ORDER BY parsed_timestamp DESC"
        
        cursor.execute(query, params)
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                'id': row[0],
                'title': row[2],
                'client': row[4],
                'budget': row[5],
                'type': row[7],
                'skills': json.loads(row[8]) if row[8] else [],
                'description': row[9][:200] + '...' if row[9] and len(row[9]) > 200 else row[9],
                'posted_date': row[10],
                'parsed_timestamp': row[13]
            })
        
        conn.close()
        return jobs
    
    def import_from_json_file(self, file_path: str, scrape_type: str = 'imported') -> Tuple[int, int]:
        """Import data from existing JSON files"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add to scraped_data
        scrape_id = self.add_scraped_data(
            scrape_type=scrape_type,
            raw_content=json.dumps(data),
            source_url=data.get('metadata', {}).get('url'),
            file_path=file_path,
            notes=f"Imported from {os.path.basename(file_path)}"
        )
        
        # Parse and add jobs if they exist
        jobs_added = 0
        if 'jobs' in data:
            for job in data['jobs']:
                self.add_job(scrape_id, job)
                jobs_added += 1
        
        return scrape_id, jobs_added
    
    # ======================== 🛸➕🪣 function to export data to JSON ========================
    def export_to_json(self, output_file: str):
        """Export all data to JSON file"""
        conn = sqlite3.connect(self.db_path)
        
        # Get all data
        jobs_df = conn.execute("SELECT * FROM jobs").fetchall()
        proposals_df = conn.execute("SELECT * FROM proposals").fetchall()
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'stats': self.get_dashboard_stats(),
            'jobs': [dict(zip([col[0] for col in conn.execute("PRAGMA table_info(jobs)").fetchall()], row)) for row in jobs_df],
            'proposals': [dict(zip([col[0] for col in conn.execute("PRAGMA table_info(proposals)").fetchall()], row)) for row in proposals_df]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        conn.close()
        return len(export_data['jobs']), len(export_data['proposals'])
    
    def load_existing_parsed_data(self, data_parsed_dir: str = "data/data_parsed") -> Tuple[int, int]:
        """Load all existing parsed data from data_parsed directory"""
        if not os.path.exists(data_parsed_dir):
            return 0, 0
        
        total_files = 0
        total_jobs = 0
        
        for filename in os.listdir(data_parsed_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(data_parsed_dir, filename)
                try:
                    scrape_id, jobs_added = self.import_from_json_file(file_path, "existing_data")
                    total_files += 1
                    total_jobs += jobs_added
                    print(f"Loaded {filename}: {jobs_added} jobs")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        return total_files, total_jobs

# Utility functions
def get_database_info(db_path: str = "upwork_data.db") -> Dict:
    """Get database file information"""
    if not os.path.exists(db_path):
        return {'exists': False}
    
    stat = os.stat(db_path)
    return {
        'exists': True,
        'size_mb': stat.st_size / (1024 * 1024),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
    }

if __name__ == "__main__":
    # Test database creation
    db = UpworkDatabase()
    print("✅ Database initialized successfully!")
    
    # Test adding sample data
    scrape_id = db.add_scraped_data(
        scrape_type="test",
        raw_content='{"test": "data"}',
        notes="Test data"
    )
    
    print(f"✅ Test scrape added with ID: {scrape_id}")
    
    # Get stats
    stats = db.get_dashboard_stats()
    print(f"📊 Dashboard stats: {stats}")