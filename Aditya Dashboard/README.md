# Weelocal Economic Engine Dashboard

**Professional analytics platform** for Series A investor presentations. Provides real-time KPI metrics, 6-year revenue forecasting, geographic analysis, efficiency metrics, Pareto analysis, and valuation scenarios.

## 🎯 Key Features

### Dashboard Sections

1. **Top KPI Row** - Six key performance indicators:
   - Total Revenue (filterable by year)
   - CAGR (2026-2031)
   - Total Shops
   - Total Service Providers
   - Revenue per Shop
   - Revenue per Service Provider

2. **Growth Engine** - Revenue analysis and trends:
   - Revenue trend line chart (2026-2031)
   - Revenue by category bar chart
   - Revenue by state geographic distribution

3. **Ecosystem Efficiency** - Performance metrics:
   - Revenue per shop by state
   - Revenue per service provider by state
   - Ecosystem size vs revenue scatter plot

4. **Top Performers** - Leading metrics:
   - Top 10 cities by revenue
   - Pareto chart (80/20 revenue concentration)

5. **Automated Insights** - AI-generated analysis:
   - Year-over-year growth percentages
   - Revenue acceleration rate
   - Efficiency improvements
   - Network density trends

6. **Scenario Projection** - Future forecasting:
   - Linear regression forecast (2032-2034)
   - Historical + projected data visualization

7. **Valuation Lens** - Investment analysis:
   - Revenue multiple simulation (3x, 5x, 8x)
   - Current and projected 2034 valuations

## 🏗️ Architecture

### Modular Design

```
├── export_data.py        # Exports Excel data to JSON
├── dashboard.html        # Standalone HTML dashboard
├── data_loader.py        # Excel file loading & transformation
├── precomputed_data.py   # Pre-aggregated data for performance
├── metrics.py            # Metric calculations (dictionary lookups)
└── insights.py          # Automated insights & projections
```

### Key Design Principles

- **Static HTML**: No server required, runs entirely in browser
- **Separation of Concerns**: Each module has a single responsibility
- **Performance Optimized**: Pre-aggregated data, dictionary lookups (O(1))
- **Type Hints**: Full type annotations for better code quality
- **Error Handling**: Graceful handling of edge cases
- **Client-Side Rendering**: Plotly.js for interactive charts

## 📊 Data Structure

### Input Format

Excel files with special structure:
- **Row 1**: Years (2026-2031)
- **Row 2**: Column headers
- **Row 3+**: Monthly data

### Required Files

- `Book1.xlsx` → sheet: `shopsrestraunt`
- `Book2.xlsx` → sheet: `service_providers`
- `Book4.xlsx` → sheet: `helpers`
- `Book5.xlsx` → sheet: `number of shops`
- `Book6.xlsx` → sheet: `number of service providers`

### Output Schema

Cleaned master dataframe:
- State
- City
- Area (if exists)
- Category
- Year
- Month
- Monthly_Value
- Revenue

## 🚀 Installation

### Prerequisites

- Python 3.14 or higher (tested with Python 3.14.3)
- pip package manager
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Export data to JSON**:
   ```bash
   python export_data.py
   ```

   This generates `data.json` which the HTML dashboard uses.

## 💻 Usage

### Option 1: Automated (Recommended)

Double-click `run_dashboard.bat` or run:
```bash
run_dashboard.bat
```

This will:
- Export data from Excel files to JSON
- Open the HTML dashboard in your browser

### Option 2: Manual

1. **Export data**:
   ```bash
   python export_data.py
   ```

2. **Open dashboard**:
   - Double-click `dashboard.html`
   - Or open it in your browser

### Updating Data

When Excel files change, re-run:
```bash
python export_data.py
```

Then refresh the browser to see updated data.

### Filters

Use the sidebar to filter by:
- **Year**: Select specific year or "All Years"
- **State**: Multi-select states
- **City**: Select specific city or "All Cities"

## ⚡ Performance

### Optimizations

- **Pre-aggregated Data**: All aggregations computed once at load time
- **Dictionary Lookups**: O(1) access instead of O(n log n) groupby operations
- **Caching**: `@st.cache_data` prevents redundant computations
- **Vectorized Operations**: No loops, pure pandas/numpy operations

### Performance Metrics

- **Filter Response Time**: <1 second
- **Data Loading**: Cached after first load
- **Chart Rendering**: Optimized Plotly visualizations

## 📈 Technical Highlights

### Code Quality

- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Error handling
- ✅ No code duplication
- ✅ Clean separation of concerns

### Performance Features

- ✅ Precomputed aggregations
- ✅ Dictionary-based lookups
- ✅ Memoization for expensive calculations
- ✅ No nested groupby in UI loops
- ✅ Optimized data structures

## 📦 Dependencies

**Python (for data export):**
- `pandas>=2.3.0` - Data processing
- `numpy>=2.4.0` - Numerical operations
- `openpyxl>=3.1.5` - Excel file reading
- `scikit-learn>=1.8.0` - Machine learning for projections

**Browser (included via CDN):**
- Plotly.js 2.26.0 - Interactive visualizations (loaded from CDN)

## 🎨 Design

- Clean white background
- Minimal color palette (blue, green, purple accents)
- Investor-grade typography
- Responsive layout
- Professional visualizations

## 📝 Project Structure

```
Aditya Dashboard/
├── export_data.py          # Data export to JSON
├── dashboard.html          # HTML dashboard (open in browser)
├── data.json              # Exported data (generated by export_data.py)
├── data_loader.py         # Data loading
├── precomputed_data.py    # Performance optimization
├── metrics.py             # Metrics calculation
├── insights.py            # Insights & projections
├── requirements.txt       # Python dependencies
├── run_dashboard.bat     # Quick start script
├── README.md             # This file
├── CHANGELOG.md          # Version history
└── PERFORMANCE.md        # Performance documentation
```

## 🔧 Troubleshooting

### Common Issues

**Python not found**: Install Python from python.org and check "Add Python to PATH"

**Module not found**: Run `pip install -r requirements.txt`

**Port 8501 in use**: Streamlit will automatically try port 8502, 8503, etc.

**Excel file errors**: Verify all files are in the dashboard directory with correct sheet names

## 📄 License

This project is a demonstration of data engineering and dashboard development capabilities.

## 👤 Author

Built for Weelocal investor dashboard requirements.

---

**Ready to explore your data!** 🚀
