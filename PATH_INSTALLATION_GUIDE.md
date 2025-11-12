# 🔧 Path Installation System

Automatski sistem za konfiguraciju putanja u n8n workflow fajlovima kada se prebacuje na novo okruženje.

## 🚀 Quick Start

```powershell
# Proverite trenutne putanje
.\show_current_paths.ps1

# Test promene bez primene
.\install_paths.ps1 -DryRun

# Primeni promene
.\install_paths.ps1
```

## 📋 Komande

### 🔍 Analiza Trenutnih Putanja
```powershell
.\show_current_paths.ps1
```
- Prikazuje sve putanje u n8n workflow fajlovima
- Proverava da li putanje postoje
- Detektuje inconsistentnosti

### 🔧 Automatska Instalacija
```powershell
# Automatski detektuje trenutni folder
.\install_paths.ps1

# Custom putanja
.\install_paths.ps1 -CustomPath "D:\NewLocation\UpworkNotif"

# Test run - samo prikazuje promene
.\install_paths.ps1 -DryRun
```

## 📁 Fajlovi Koji Se Ažuriraju

- `n8n_workflow_conditional.json`
- `n8n_chat_ai_workflow.json`  
- `n8n_ai_cover_letter_workflow.json`
- `n8n_database_cleanup_workflow.json`

## 🛡️ Sigurnost

- **Automatski backup** - kreira `.backup.TIMESTAMP` fajlove
- **DryRun mode** - testiraj pre primene
- **Validacija** - proverava da li potrebni folderi postoje

## 📊 Primer Izvršavanja

```
🔧 UPWORK NOTIFICATION SYSTEM - PATH INSTALLER
===============================================
📁 Auto-detected working directory: D:\NewLocation\UpworkNotif
🔄 Will replace: E:\Repoi\UpworkNotif  
🔄 With new path: D:\NewLocation\UpworkNotif

📋 Found n8n workflow files:
   ✅ n8n_workflow_conditional.json
   ✅ n8n_chat_ai_workflow.json
   ✅ n8n_ai_cover_letter_workflow.json
   ✅ n8n_database_cleanup_workflow.json

📝 Processing workflow files:
   🔄 n8n_workflow_conditional.json - Found 8 path references
     💾 Backup created: n8n_workflow_conditional.json.backup.20251112_051234
     ✅ Updated successfully!

📊 SUMMARY:
============
🔍 Files processed: 4
✅ Files updated: 4  
🔢 Total path references updated: 32

🎉 Path installation completed successfully!
```

## 🔄 Posle Instalacije

1. **Import workflow-ove u n8n**
2. **Test svih workflow-ova** 
3. **Obriši backup fajlove** (*.backup.*) kada sve radi

## ⚠️ Troubleshooting

### "No workflow files found"
- Proverite da li ste u ispravnom direktorijumu
- Workflow JSON fajlovi moraju postojati

### "Required directories missing"  
- Proverite postojanje: `run_scripts/`, `scripts/`, `data/`, `js_scrapers/`
- Možda niste u project root folderu

### Vraćanje na Staro
```powershell
# Kopiraj backup fajlove nazad
Copy-Item "*.backup.*" -Destination . -Force
# Ukloni .backup.TIMESTAMP iz imena
```

## 💡 Best Practices

1. **Uvek koristite `-DryRun` prvo**
2. **Proverite putanje pre i posle** sa `show_current_paths.ps1`
3. **Testirajte n8n workflow-ove** nakon instalacije
4. **Sačuvajte backup fajlove** dok ne potvrdite da sve radi
5. **Dokumentujte novu putanju** za buduće reference

---
*Kreiran za lako prebacivanje Upwork Notification System-a na nova okruženja.* 🚀