# Database Cleanup System

Automated system for maintaining the Upwork database by keeping only the latest scrapes and removing old data.

## 🎯 Overview

The database cleanup system helps maintain optimal database performance by:
- Keeping only the latest N scrapes (default: 50)
- Removing associated jobs, proposals, and cover letters from old scrapes
- Cleaning up orphaned records
- Optimizing database size with VACUUM
- Running on a scheduled basis

## 📁 Files

- **`data/database_cleanup.py`** - Core cleanup functionality
- **`run_database_cleanup.ps1`** - Manual cleanup script
- **`scheduled_database_cleanup.py`** - Automated scheduled cleanup
- **`setup_database_maintenance.ps1`** - Setup automatic scheduling

## 🚀 Quick Start

### 1. Manual Cleanup (One-time)

```powershell
# Basic cleanup (keep latest 50 scrapes)
./run_database_cleanup.ps1

# Custom settings
./run_database_cleanup.ps1 -KeepScrapes 100 -DatabasePath "custom.db"

# Dry run to see what would be deleted
./run_database_cleanup.ps1 -DryRun
```

### 2. Setup Automatic Cleanup

```powershell
# Setup automatic cleanup every 24 hours, keeping 50 scrapes
./setup_database_maintenance.ps1

# Custom schedule (every 12 hours, keep 100 scrapes)
./setup_database_maintenance.ps1 -FrequencyHours 12 -KeepScrapes 100

# Remove automatic cleanup
./setup_database_maintenance.ps1 -Remove
```

### 3. Check Status

```powershell
# Check cleanup status and configuration
python scheduled_database_cleanup.py --status

# Force cleanup now
python scheduled_database_cleanup.py --force
```

## ⚙️ Configuration

The system uses a JSON configuration file (`cleanup_config.json`):

```json
{
  "enabled": true,
  "keep_scrapes": 50,
  "database_path": "upwork_data.db",
  "cleanup_frequency_hours": 24,
  "vacuum_database": true,
  "analytics_retention_days": 30,
  "min_keyword_frequency": 1,
  "last_cleanup": null,
  "notifications": {
    "log_to_file": true,
    "email_on_failure": false,
    "email_recipients": []
  }
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `enabled` | Enable/disable automatic cleanup | `true` |
| `keep_scrapes` | Number of recent scrapes to keep | `50` |
| `database_path` | Path to database file | `"upwork_data.db"` |
| `cleanup_frequency_hours` | Hours between cleanups | `24` |
| `vacuum_database` | Run VACUUM optimization | `true` |
| `analytics_retention_days` | Keep analytics for N days | `30` |
| `min_keyword_frequency` | Minimum keyword usage to keep | `1` |

## 🗃️ What Gets Cleaned

### 1. Old Scraped Data
- Keeps latest N scrapes based on `keep_scrapes` setting
- Deletes older scrape records from `scraped_data` table

### 2. Associated Jobs
- Removes job records linked to deleted scrapes
- Cleans `jobs` table based on `scrape_id` foreign key

### 3. Associated Proposals
- Removes proposal records linked to deleted scrapes
- Cleans `proposals` table based on `scrape_id` foreign key

### 4. Orphaned Cover Letters
- Removes cover letters for jobs that no longer exist
- Cleans broken foreign key references

### 5. Old Analytics
- Removes analytics data older than retention period
- Default: 30 days retention

### 6. Unused Keywords
- Removes keywords below frequency threshold
- Default: Remove keywords used only once

### 7. Database Optimization
- Runs SQLite VACUUM to reclaim space
- Rebuilds database file for optimal performance

## 📊 Monitoring

### Log Files
- Cleanup activities logged to `database_cleanup.log`
- Includes timestamps, statistics, and error messages

### Statistics Tracking
Before and after cleanup, the system tracks:
- Record counts for each table
- Database file size
- Space saved
- Cleanup duration

### Example Output
```
🧹 Starting database cleanup...
📊 Before cleanup: {'scraped_data_count': 150, 'jobs_count': 3000, 'db_size_mb': 25.4}
🗑️ Deleted 100 old scraped_data records
🗑️ Deleted 2000 old job records
💾 Space saved: 15.2 MB
✅ Cleanup completed successfully!
```

## 🛠️ Troubleshooting

### Common Issues

1. **"Database locked" error**
   - Ensure no other processes are using the database
   - Close dashboard or other applications accessing the DB

2. **Permission denied**
   - Check file permissions on database file
   - Run PowerShell as Administrator if needed

3. **Python not found**
   - Ensure Python is installed and in PATH
   - Use full path to Python executable if needed

4. **Task scheduler issues**
   - Check Windows Task Scheduler for error details
   - Verify task is enabled and properly configured

### Manual Recovery

If cleanup fails, you can manually check the database:

```sql
-- Check database integrity
PRAGMA integrity_check;

-- Get table sizes
SELECT name, COUNT(*) FROM sqlite_master sm 
JOIN sqlite_temp_master stm 
WHERE sm.type='table' GROUP BY sm.name;

-- Manual vacuum
VACUUM;
```

## 🔧 Advanced Usage

### Custom Python Script

```python
from data.database_cleanup import DatabaseCleaner

# Initialize cleaner
cleaner = DatabaseCleaner(
    db_path="upwork_data.db",
    keep_scrapes=75
)

# Run cleanup
success = cleaner.run_cleanup(vacuum=True)
print(f"Cleanup {'successful' if success else 'failed'}")
```

### Batch Operations

```powershell
# Cleanup multiple databases
$databases = @("upwork_data.db", "backup_data.db")
foreach ($db in $databases) {
    python data/database_cleanup.py --db-path $db --keep-scrapes 50
}
```

## 📈 Performance Impact

### Expected Results
- **Database size reduction**: 60-80% typical
- **Query performance**: Improved with fewer records
- **Cleanup duration**: 30 seconds - 2 minutes depending on data size
- **Disk I/O**: Temporary increase during VACUUM operation

### Best Practices
- Run cleanup during low-usage periods
- Keep at least 30-50 scrapes for historical data
- Monitor disk space before/after cleanup
- Test with dry-run first on production data

## 🔄 Integration

The cleanup system integrates with:
- **n8n workflows**: Can be triggered from automation workflows
- **Dashboard**: Cleanup stats can be displayed in web dashboard
- **Monitoring**: Log files can be monitored by external tools
- **Backup**: Run cleanup after creating database backups
