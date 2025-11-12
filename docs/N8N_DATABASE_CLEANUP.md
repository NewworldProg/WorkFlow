# N8n Database Cleanup Workflow

## Pregled

Ovaj n8n workflow automatski čisti bazu podataka i održava samo poslednjih 50 scrape-ova. Workflow može da se pokreće ručno ili automatski na svakih 6 sati.

## Komponente

### Fajlovi
- `n8n_database_cleanup_workflow.json` - N8n workflow definicija
- `scripts/n8n_database_cleanup.py` - Python script za cleanup
- `run_n8n_database_cleanup.ps1` - PowerShell wrapper

### Workflow Nodovi

1. **Manual Trigger** - Za ručno pokretanje
2. **Schedule Trigger** - Automatsko pokretanje svakih 6 sati
3. **Database Cleanup** - Izvršava PowerShell script
4. **Process Results** - Parsira rezultate cleanup-a
5. **Check Success** - Proverava da li je cleanup uspešan
6. **Success/Error Notification** - Šalje notifikacije na Slack
7. **Log Results** - Zapisuje rezultate u log fajl

## Instalacija

### 1. Import Workflow-a

```bash
# U n8n interfejsu:
# 1. Idi na Workflows
# 2. Klikni "Import from file"
# 3. Izaberi n8n_database_cleanup_workflow.json
```

### 2. Konfiguracija Slack Notifikacija (opciono)

```bash
# U n8n:
# 1. Idi na Credentials
# 2. Dodaj novi Slack credential
# 3. Konfiguriši Success/Error Notification nodove
```

### 3. Proveri Putanje

Proveri da PowerShell script može da se pokrene:

```powershell
# Test da li script radi
.\run_n8n_database_cleanup.ps1 -KeepScrapes 50 -JsonOutput
```

## Korišćenje

### Ručno Pokretanje

1. Otvori workflow u n8n
2. Klikni na "Manual Trigger" node
3. Klikni "Execute Node"

### Automatsko Pokretanje

Workflow će se automatski pokrenuti svakih 6 sati kada je aktiviran.

### Konfiguracija Parametara

Da promeniš broj scrape-ova koji se čuvaju:

1. Otvori "Database Cleanup" node
2. Promeni parametar `-KeepScrapes 50` na željeni broj

## Output

Workflow vraća JSON sa sledećim informacijama:

```json
{
  "success": true,
  "message": "Database cleaned successfully",
  "timestamp": "2024-01-01T12:00:00",
  "metrics": {
    "space_saved_mb": 15.2,
    "total_records_deleted": 150,
    "cleanup_details": {
      "scraped_data_deleted": 100,
      "jobs_deleted": 25,
      "proposals_deleted": 15,
      "cover_letters_deleted": 10
    }
  },
  "config": {
    "database_path": "data/upwork_jobs.db",
    "keep_scrapes": 50
  },
  "before_stats": {
    "scraped_data_count": 150,
    "jobs_count": 75
  },
  "after_stats": {
    "scraped_data_count": 50,
    "jobs_count": 50
  }
}
```

## Monitoring

### Log Fajl

Rezultati se automatski zapisuju u `database_cleanup_log.json`:

```bash
# Prikaz poslednje 10 linija loga
Get-Content database_cleanup_log.json | Select-Object -Last 10
```

### Slack Notifikacije

Ako je konfigurisan Slack:
- Uspešan cleanup šalje zelenu notifikaciju
- Neuspešan cleanup šalje crvenu notifikaciju sa detaljima greške

## Troubleshooting

### Greške sa PowerShell

```powershell
# Proveri da li su svi fajlovi na mestu
Test-Path .\run_n8n_database_cleanup.ps1
Test-Path .\scripts\n8n_database_cleanup.py
Test-Path .\data\upwork_jobs.db
```

### Python Greške

```powershell
# Test Python script direktno
python scripts\n8n_database_cleanup.py --keep-scrapes 50 --json-output
```

### N8n Greške

1. Proveri da li je workflow aktivan
2. Proveri log u n8n interfejsu
3. Proveri da li su svi nodovi pravilno povezani

## Customizacija

### Promena Schedule-a

Za promenu schedule-a, otvori "Schedule Trigger" node i promeni interval.

### Dodavanje Novih Notifikacija

Možeš dodati email, Discord, ili druge notifikacije umesto/pored Slack-a.

### Custom Log Format

Promeni "Log Results" node da koristi custom format za log fajl.