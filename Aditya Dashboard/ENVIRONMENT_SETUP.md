# WEELOCAL DASHBOARD - ENVIRONMENT SETUP GUIDE

**Date**: February 23, 2026  
**Status**: ✅ Complete and Ready

---

## ENVIRONMENT INFORMATION

### Python Environment
- **Python Version**: 3.11.5 (Anaconda)
- **Python Executable**: `C:\Users\archa\anaconda3\python.exe`
- **Environment Type**: System (Anaconda)

---

## INSTALLED PACKAGES

All required packages have been installed and verified:

| Package | Version | Purpose |
|---------|---------|---------|
| **Flask** | 2.2.5 | Web framework for dashboard server |
| **Werkzeug** | 2.2.0+ | WSGI utilities for Flask |
| **pandas** | ≥2.3.0 | Data processing and analysis |
| **numpy** | <2.0 | Numerical computing |
| **openpyxl** | ≥3.1.5 | Excel file reading/writing |
| **xlrd** | ≥2.0.1 | Legacy Excel support |
| **scikit-learn** | ≥1.3.0 | Machine learning utilities |
| **python-dotenv** | ≥1.0.0 | Environment variable management |

---

## REQUIREMENTS.TXT

The `requirements.txt` file contains all necessary dependencies:

```
# Core Data Processing
pandas>=2.3.0
numpy<2.0
scikit-learn>=1.3.0

# Excel Support
openpyxl>=3.1.5
xlrd>=2.0.1

# Web Framework
Flask==2.2.5
Werkzeug>=2.2.0

# Utilities
python-dotenv>=1.0.0
```

**Install all packages:**
```bash
pip install -r requirements.txt
```

---

## PROJECT FILES VERIFIED

| File | Size | Status |
|------|------|--------|
| `run_server.py` | 3.7 KB | ✅ Present |
| `dashboard.html` | 147 KB | ✅ Present |
| `data.json` | 438 KB | ✅ Present |
| `requirements.txt` | 207 bytes | ✅ Updated |

---

## DATA SOURCE FILES (Excel)

| File | Status | Rows | Columns |
|------|--------|------|---------|
| Book1.xlsx | ✅ Ready | 9,251 | 94 |
| Book2.xlsx | ✅ Ready | 1,594 | 74 |
| Book4.xlsx | ✅ Ready | 9,251 | 74 |
| Book5.xlsx | ✅ Ready | 1,592 | 26 |
| Book6.xlsx | ✅ Ready | 1,592 | 26 |

---

## HOW TO RUN THE PROJECT

### Step 1: Verify Environment
```bash
python --version
pip list
```

### Step 2: Start the Server
```bash
python run_server.py
```

**Expected Output:**
```
 * Serving Flask app 'run_server'
 * Debug mode: off
WARNING: This is a development server. Do not use it in production.
 * Running on http://0.0.0.0:8000
```

### Step 3: Access Dashboard
Open your browser and go to:
```
http://localhost:8000
```

### Step 4: Verify All Endpoints

**Health Check:**
```
GET http://localhost:8000/ping
```
Response: `{"status": "ok", "message": "Server is running", "service": "Weelocal Dashboard"}`

**Data API:**
```
GET http://localhost:8000/data.json
```
Response: Complete JSON with 16 data sections

**Dashboard:**
```
GET http://localhost:8000/
```
Response: Interactive HTML dashboard with Plotly charts

---

## TROUBLESHOOTING

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change port in run_server.py
# Edit: PORT = 8001
```

### Issue: "Module not found" errors
**Solution:**
```bash
pip install -r requirements.txt --upgrade
pip install --upgrade setuptools wheel
```

### Issue: "NumPy compatibility" error
**Solution:**
```bash
pip install "numpy<2.0" --force-reinstall
pip install pandas --upgrade
```

### Issue: "Connection refused"
**Solution:**
1. Ensure server is running: `python run_server.py`
2. Check port is available: `netstat -ano | findstr :8000`
3. Wait 3 seconds for server to start
4. Try: `http://localhost:8000/ping`

---

## SYSTEM REQUIREMENTS

- **OS**: Windows 10/11, macOS, Linux
- **Python**: 3.11+ (tested with 3.11.5)
- **RAM**: 512 MB minimum, 2 GB recommended
- **Disk**: 500 MB free space
- **Browser**: Modern browser (Chrome, Firefox, Edge, Safari)
- **Network**: Local or network access to port 8000

---

## DEVELOPMENT SETUP (Optional)

### Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Run in Production Mode
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run_server:app
```

### Enable Debug Mode
Edit `run_server.py`:
```python
app.run(host='0.0.0.0', port=PORT, debug=True)
```

---

## PROJECT STRUCTURE

```
Aditya Dashboard/
├── run_server.py              # Main Flask server
├── dashboard.html             # Frontend dashboard
├── data.json                  # Data API
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview
├── START_HERE.md             # Quick start guide
├── COMPLETION_REPORT.md      # Completion status
├── GRAPHS_INVENTORY.md       # All available graphs
├── ENVIRONMENT_SETUP.md      # This file
├── Book1-6.xlsx              # Source data files
├── data_loader.py            # Data loading utilities
├── export_data.py            # Export to JSON
├── metrics.py                # Metrics calculations
├── insights.py               # Insights generation
├── verify_project.py         # Project verification
└── .gitignore                # Git ignore rules
```

---

## NEXT STEPS

1. ✅ Environment configured
2. ✅ All packages installed
3. ✅ Project files verified
4. ⬜ Start server: `python run_server.py`
5. ⬜ Open browser: `http://localhost:8000`
6. ⬜ Explore dashboard and charts
7. ⬜ Share with stakeholders

---

## SUPPORT

**Quick Start:**
- Read: [START_HERE.md](START_HERE.md)
- Documentation: [README.md](README.md)
- Graphs: [GRAPHS_INVENTORY.md](GRAPHS_INVENTORY.md)

**API Endpoints:**
- Health: `GET /ping`
- Data: `GET /data.json`
- Dashboard: `GET /`

**Data Sources:**
- Excel files automatically loaded on startup
- Data exported to `data.json`
- Charts rendered in real-time

---

## VERIFICATION CHECKLIST

✅ Python 3.11.5 installed  
✅ Flask 2.2.5 installed  
✅ Pandas ≥2.3.0 installed  
✅ NumPy <2.0 installed  
✅ Excel support (openpyxl, xlrd) installed  
✅ requirements.txt updated  
✅ Project files present and clean  
✅ Data source files verified  
✅ Server ready to start  
✅ Dashboard ready to view  

---

**Status**: ✅ **ENVIRONMENT SETUP COMPLETE**

**Ready to run**: `python run_server.py`

---

*Setup completed on February 23, 2026*  
*All systems configured and verified ✅*
