"""
Enhanced HTML Dashboard Generator for Job Database
================================================
Generates paginated HTML dashboard with job links and neutral styling
"""

import os
import sys
import json
import sqlite3
import glob
from datetime import datetime
from pathlib import Path

# Add data directory to path to import database_manager
sys.path.append(str(Path(__file__).parent.parent / 'data'))

try:
    from database_manager import UpworkDatabase
except ImportError:
    print("Cannot import database_manager from data/ directory")
    sys.exit(1)

def cleanup_old_dashboards(output_path):
    """Remove old dashboard files before creating new one"""
    try:
        output_dir = os.path.dirname(output_path)
        output_filename = os.path.basename(output_path)
        
        # Don't delete the file we're about to create
        if not output_dir:
            output_dir = "."
            
        # Patterns to match dashboard files
        dashboard_patterns = [
            os.path.join(output_dir, "dashboard_*.html"),
            os.path.join(output_dir, "temp_dashboard_*.html"),
            os.path.join(output_dir, "test_dashboard_*.html"),
            "dashboard_*.html",  # Current directory
            "temp_dashboard_*.html",  # Current directory
            "test_dashboard_*.html"  # Current directory
        ]
        
        deleted_count = 0
        for pattern in dashboard_patterns:
            for file_path in glob.glob(pattern):
                # Skip the file we're about to create
                if os.path.basename(file_path) == output_filename:
                    continue
                    
                # Skip dashboard_latest.html (permanent copy)
                if os.path.basename(file_path) == "dashboard_latest.html":
                    continue
                    
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"Deleted old dashboard: {file_path}")
                except OSError as e:
                    print(f"Warning: Could not delete {file_path}: {e}")
        
        if deleted_count > 0:
            print(f"✅ Cleaned up {deleted_count} old dashboard files")
        else:
            print("ℹ️ No old dashboard files to clean up")
            
    except Exception as e:
        print(f"Warning: Error during dashboard cleanup: {e}")
        # Don't fail the main operation if cleanup fails

def generate_pagination_html(current_page, total_pages, base_url="?"):
    """Generate pagination HTML"""
    if total_pages <= 1:
        return ""
    
    pagination_html = '<div class="pagination">'
    
    # Previous button
    if current_page > 1:
        pagination_html += f'<a href="{base_url}page={current_page-1}" class="page-btn">← Previous</a>'
    
    # Page numbers
    start_page = max(1, current_page - 2)
    end_page = min(total_pages, current_page + 2)
    
    if start_page > 1:
        pagination_html += f'<a href="{base_url}page=1" class="page-btn">1</a>'
        if start_page > 2:
            pagination_html += '<span class="page-dots">...</span>'
    
    for page_num in range(start_page, end_page + 1):
        if page_num == current_page:
            pagination_html += f'<span class="page-btn active">{page_num}</span>'
        else:
            pagination_html += f'<a href="{base_url}page={page_num}" class="page-btn">{page_num}</a>'
    
    if end_page < total_pages:
        if end_page < total_pages - 1:
            pagination_html += '<span class="page-dots">...</span>'
        pagination_html += f'<a href="{base_url}page={total_pages}" class="page-btn">{total_pages}</a>'
    
    # Next button
    if current_page < total_pages:
        pagination_html += f'<a href="{base_url}page={current_page+1}" class="page-btn">Next →</a>'
    
    pagination_html += '</div>'
    return pagination_html

def generate_html_dashboard(output_path="dashboard.html", page=1, per_page=20):
    """Generate HTML dashboard from database with pagination"""
    
    try:
        # Initialize database
        db_path = "upwork_data.db"
        if not os.path.exists(db_path):
            print(f"Database not found: {db_path}")
            return False
            
        db = UpworkDatabase(db_path)
        
        # Get data from database
        print("Loading data from database...")
        stats = db.get_dashboard_stats()
        
        # Get paginated jobs
        offset = (page - 1) * per_page
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total jobs count
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]
        total_pages = (total_jobs + per_page - 1) // per_page
        
        # Get paginated jobs with cover letter info
        cursor.execute('''
            SELECT j.job_uid, j.job_title, j.job_url, j.posted_time, j.job_type, 
                   j.experience_level, j.budget, j.hourly_rate_min, j.hourly_rate_max,
                   j.duration, j.skills, j.description, j.parsed_timestamp, j.id,
                   cl.id as cover_letter_id, cl.ai_provider, cl.cover_letter_text
            FROM jobs j
            LEFT JOIN cover_letters cl ON j.id = cl.job_id
            ORDER BY j.parsed_timestamp DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        jobs_data = cursor.fetchall()
        jobs = []
        for row in jobs_data:
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
                'parsed_timestamp': row[12],
                'job_id': row[13],
                'has_cover_letter': row[14] is not None,
                'cover_letter_id': row[14],
                'ai_provider': row[15],
                'cover_letter_text': row[16]
            })
        
        conn.close()
        
        # Generate HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Opportunities Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #4a90e2 0%, #7b68ee 100%);
            min-height: 100vh;
            padding: 15px;
            font-size: 14px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 1.8em;
            margin-bottom: 8px;
        }}
        
        .header p {{
            font-size: 0.95em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            padding: 20px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 18px;
            border-radius: 8px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-3px);
        }}
        
        .stat-number {{
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .content-section {{
            padding: 20px;
        }}
        
        .section-title {{
            font-size: 1.4em;
            color: #333;
            margin-bottom: 15px;
            border-bottom: 2px solid #14A76C;
            padding-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .pagination-info {{
            font-size: 0.9em;
            color: #666;
        }}
        
        .jobs-grid {{
            display: grid;
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .job-card {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .job-card:hover {{
            box-shadow: 0 4px 15px rgba(0,0,0,0.12);
            transform: translateY(-1px);
        }}
        
        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}
        
        .job-title {{
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
            line-height: 1.3;
            flex: 1;
            margin-right: 10px;
        }}
        
        .job-title a {{
            color: #2c3e50;
            text-decoration: none;
            transition: color 0.3s ease;
        }}
        
        .job-title a:hover {{
            color: #34495e;
            text-decoration: underline;
        }}
        
        .cover-letter-badge {{
            display: inline-flex;
            align-items: center;
            background: #27ae60;
            color: white;
            font-size: 0.75em;
            padding: 3px 8px;
            border-radius: 12px;
            margin-left: 8px;
            white-space: nowrap;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.3s ease;
        }}
        
        .cover-letter-badge:hover {{
            background: #219a52;
            text-decoration: none;
            color: white;
        }}
        
        .cover-letter-badge.pending {{
            background: #e74c3c;
            cursor: default;
        }}
        
        .cover-letter-badge.pending:hover {{
            background: #c0392b;
        }}
        
        .cover-letter-badge .icon {{
            margin-right: 4px;
        }}
        
        /* Modal styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }}
        
        .modal-content {{
            background-color: white;
            margin: 5% auto;
            padding: 20px;
            border-radius: 10px;
            width: 80%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
        }}
        
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        
        .modal-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }}
        
        .close-modal {{
            font-size: 24px;
            cursor: pointer;
            color: #999;
            background: none;
            border: none;
        }}
        
        .close-modal:hover {{
            color: #333;
        }}
        
        .cover-letter-content {{
            line-height: 1.6;
            white-space: pre-wrap;
            color: #444;
            font-family: Georgia, serif;
        }}
        
        .external-link {{
            background: #3498db;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 0.8em;
            font-weight: bold;
            transition: all 0.3s ease;
            white-space: nowrap;
        }}
        
        .external-link:hover {{
            background: #2980b9;
            transform: scale(1.05);
        }}
        
        .job-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 12px;
        }}
        
        .job-meta-item {{
            background: #f0f0f0;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            color: #666;
        }}
        
        .job-type-fixed {{
            background: #e3f2fd;
            color: #1976d2;
        }}
        
        .job-type-hourly {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}
        
        .job-description {{
            color: #555;
            line-height: 1.5;
            margin-bottom: 12px;
            font-size: 0.9em;
        }}
        
        .skills-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .skill-tag {{
            background: #3498db;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75em;
        }}
        
        .skills-section {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 8px;
        }}
        
        .skill-item {{
            background: white;
            padding: 8px;
            border-radius: 6px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .skill-name {{
            font-weight: bold;
            color: #333;
            font-size: 0.85em;
        }}
        
        .skill-count {{
            color: #3498db;
            font-size: 0.8em;
        }}
        
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        
        .page-btn {{
            padding: 8px 12px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            text-decoration: none;
            color: #333;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }}
        
        .page-btn:hover {{
            background: #3498db;
            color: white;
            border-color: #3498db;
        }}
        
        .page-btn.active {{
            background: #3498db;
            color: white;
            border-color: #3498db;
        }}
        
        .page-dots {{
            padding: 8px 4px;
            color: #999;
        }}
        
        .timestamp {{
            text-align: center;
            color: #666;
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            font-size: 0.85em;
        }}
        
        .no-data {{
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 30px;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                padding: 15px;
            }}
            
            .job-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            .job-title {{
                margin-right: 0;
                margin-bottom: 8px;
            }}
            
            .job-meta {{
                flex-direction: column;
                gap: 8px;
            }}
            
            .external-link {{
                align-self: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💼 Job Opportunities Dashboard</h1>
            <p>Freelance jobs overview - {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_jobs', 0)}</div>
                <div class="stat-label">Total Opportunities</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_scrapes', 0)}</div>
                <div class="stat-label">Data Collections</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('recent_scrapes', 0)}</div>
                <div class="stat-label">Last 7 Days</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(stats.get('top_skills', []))}</div>
                <div class="stat-label">Active Skills</div>
            </div>
        </div>
"""

        # Add jobs by type section if data exists
        if stats.get('jobs_by_type'):
            html_content += f"""
        <div class="content-section">
            <h2 class="section-title">📊 Opportunities by Type</h2>
            <div class="stats-grid">
"""
            for job_type, count in stats['jobs_by_type'].items():
                html_content += f"""
                <div class="stat-card">
                    <div class="stat-number">{count}</div>
                    <div class="stat-label">{job_type or 'Unspecified'}</div>
                </div>
"""
            html_content += """
            </div>
        </div>
"""

        # Add top skills section if data exists
        if stats.get('top_skills'):
            html_content += f"""
        <div class="content-section">
            <h2 class="section-title">🏆 Most Popular Skills</h2>
            <div class="skills-section">
                <div class="skills-grid">
"""
            for skill, count in stats['top_skills'][:12]:  # Top 12 skills
                html_content += f"""
                    <div class="skill-item">
                        <div class="skill-name">{skill}</div>
                        <div class="skill-count">{count} times</div>
                    </div>
"""
            html_content += """
                </div>
            </div>
        </div>
"""

        # Add jobs section with pagination
        html_content += f"""
        <div class="content-section">
            <h2 class="section-title">
                <span>💼 Opportunities (Page {page} of {total_pages})</span>
                <span class="pagination-info">Showing {len(jobs)} of {total_jobs} opportunities</span>
            </h2>
"""

        # Add pagination at top
        pagination_html = generate_pagination_html(page, total_pages)
        if pagination_html:
            html_content += pagination_html

        if jobs:
            html_content += """
            <div class="jobs-grid">
"""
            for job in jobs:
                # Prepare job info
                job_type_class = "job-type-fixed" if job.get('job_type') == 'Fixed price' else "job-type-hourly"
                
                budget_text = ""
                if job.get('budget'):
                    budget_text = f"${job['budget']}"
                elif job.get('hourly_rate_min') and job.get('hourly_rate_max'):
                    budget_text = f"${job['hourly_rate_min']}-${job['hourly_rate_max']}/h"
                elif job.get('hourly_rate_min'):
                    budget_text = f"${job['hourly_rate_min']}/h"
                
                description = job.get('description', '')
                if description and len(description) > 300:
                    description = description[:300] + "..."
                
                posted_time = job.get('posted_time', 'Unknown')
                job_title = job.get('job_title', 'No title')
                job_url = job.get('job_url', '')
                
                html_content += f"""
                <div class="job-card">
                    <div class="job-header">
                        <div class="job-title">
"""
                
                if job_url:
                    html_content += f"""
                            <a href="{job_url}" target="_blank">{job_title}</a>
"""
                else:
                    html_content += f"""
                            {job_title}
"""
                
                html_content += """
                        </div>
"""
                
                # Add cover letter badge
                if job.get('has_cover_letter'):
                    ai_provider = job.get('ai_provider', 'AI')
                    cover_letter_text = job.get('cover_letter_text', '').replace("'", "&#39;").replace('"', '&quot;').replace('\n', '\\n')
                    job_title_escaped = job_title.replace("'", "&#39;").replace('"', '&quot;')
                    html_content += f"""
                        <a href="#" class="cover-letter-badge" onclick="openCoverLetterModal('{job_title_escaped}', '{ai_provider}', `{cover_letter_text}`)">
                            <span class="icon">📄</span> View Cover Letter
                        </a>
"""
                else:
                    html_content += """
                        <div class="cover-letter-badge pending">
                            <span class="icon">⏳</span> No Cover Letter
                        </div>
"""
                
                if job_url:
                    html_content += f"""
                        <a href="{job_url}" target="_blank" class="external-link">View Opportunity →</a>
"""
                
                html_content += """
                    </div>
                    <div class="job-meta">
"""
                
                if job.get('job_type'):
                    html_content += f"""
                        <span class="job-meta-item {job_type_class}">{job['job_type']}</span>
"""
                
                if budget_text:
                    html_content += f"""
                        <span class="job-meta-item">{budget_text}</span>
"""
                
                if job.get('experience_level'):
                    html_content += f"""
                        <span class="job-meta-item">{job['experience_level']}</span>
"""
                
                if job.get('duration'):
                    html_content += f"""
                        <span class="job-meta-item">{job['duration']}</span>
"""
                
                html_content += f"""
                        <span class="job-meta-item">📅 {posted_time}</span>
                    </div>
"""
                
                if description:
                    html_content += f"""
                    <div class="job-description">{description}</div>
"""
                
                if job.get('skills'):
                    html_content += """
                    <div class="skills-container">
"""
                    for skill in job['skills'][:10]:  # Max 10 skills per job
                        html_content += f"""
                        <span class="skill-tag">{skill}</span>
"""
                    if len(job['skills']) > 10:
                        html_content += f"""
                        <span class="skill-tag">+{len(job['skills']) - 10} more</span>
"""
                    html_content += """
                    </div>
"""
                
                html_content += """
                </div>
"""
                
            html_content += """
            </div>
"""
        else:
            html_content += """
            <div class="no-data">
                📭 No opportunity data found in database
            </div>
"""

        # Add pagination at bottom
        if pagination_html:
            html_content += pagination_html

        html_content += """
        </div>
"""

        # Add footer with timestamp
        html_content += f"""
        <div class="timestamp">
            <p>📊 Dashboard generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
            <p>🗃️ Database: {db_path} | Page: {page}/{total_pages} | Total Opportunities: {total_jobs}</p>
        </div>
    </div>
    
    <script>
        // Auto-refresh page every 5 minutes
        setTimeout(function() {{
            location.reload();
        }}, 300000);
        
        // Add keyboard navigation
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowLeft') {{
                const prevBtn = document.querySelector('.page-btn[href*="page={page-1}"]');
                if (prevBtn) prevBtn.click();
            }}
            if (e.key === 'ArrowRight') {{
                const nextBtn = document.querySelector('.page-btn[href*="page={page+1}"]');
                if (nextBtn) nextBtn.click();
            }}
        }});
        
        // Cover Letter Modal Functions
        function openCoverLetterModal(jobTitle, provider, coverLetterText) {{
            const modal = document.getElementById('coverLetterModal');
            const modalTitle = document.getElementById('modalJobTitle');
            const modalProvider = document.getElementById('modalProvider');
            const modalContent = document.getElementById('coverLetterContent');
            
            modalTitle.textContent = jobTitle;
            modalProvider.textContent = provider;
            modalContent.textContent = coverLetterText.replace(/\\\\n/g, '\\n');
            
            modal.style.display = 'block';
        }}
        
        function closeCoverLetterModal() {{
            document.getElementById('coverLetterModal').style.display = 'none';
        }}
        
        // Close modal when clicking outside
        window.onclick = function(event) {{
            const modal = document.getElementById('coverLetterModal');
            if (event.target === modal) {{
                closeCoverLetterModal();
            }}
        }}
        
        // Close modal with Escape key
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                closeCoverLetterModal();
            }}
        }});
    </script>
    
    <!-- Cover Letter Modal -->
    <div id="coverLetterModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div>
                    <div class="modal-title" id="modalJobTitle">Job Title</div>
                    <div style="font-size: 0.9em; color: #666; margin-top: 4px;">
                        Generated by: <span id="modalProvider">AI</span>
                    </div>
                </div>
                <button class="close-modal" onclick="closeCoverLetterModal()">&times;</button>
            </div>
            <div class="cover-letter-content" id="coverLetterContent">
                Cover letter content will appear here...
            </div>
        </div>
    </div>
</body>
</html>
"""

        # Clean up old dashboard files before creating new one
        cleanup_old_dashboards(output_path)
        
        # Write HTML file 
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Dashboard generated: {output_path}")
        print(f"Stats: {total_jobs} total jobs, {len(jobs)} on page {page}/{total_pages}")
        
        return True
        
    except Exception as e:
        print(f"Error generating dashboard: {e}")
        return False

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate HTML dashboard from freelance jobs database')
    parser.add_argument('--output', '-o', default='dashboard.html', help='Output HTML file path')
    parser.add_argument('--page', '-p', type=int, default=1, help='Page number (default: 1)')
    parser.add_argument('--per-page', type=int, default=20, help='Jobs per page (default: 20)')
    
    args = parser.parse_args()
    
    print('JOB OPPORTUNITIES DASHBOARD GENERATOR')
    print('=========================================')
    
    success = generate_html_dashboard(args.output, args.page, args.per_page)
    
    if success:
        print(f'SUCCESS! Dashboard saved to: {args.output}')
        # Try to get absolute path
        abs_path = os.path.abspath(args.output)
        print(f'Full path: {abs_path}')
        print(f'Open in browser: file:///{abs_path}')
        sys.exit(0)
    else:
        print('FAILED! Could not generate dashboard')
        sys.exit(1)

if __name__ == '__main__':
    main()