"""
Data export script - Converts Excel data to JSON for HTML dashboard
Run this script to generate data.json for the HTML dashboard
"""

import pandas as pd
import numpy as np
import json
from data_loader import DataLoader
from precomputed_data import PrecomputedData
from metrics import MetricsCalculator
from insights import InsightsGenerator
import warnings
warnings.filterwarnings('ignore')


def _validate_kpi_totals(precomputed, metrics) -> None:
    """
    Validate that KPI totals agree across different sources.
    
    Compares:
    1. sum(precomputed.yearly_totals.values())
    2. metrics.get_total_revenue()
    3. sum(revenue_trend['Revenue'])
    
    If mismatch >0.5%, prints WARNING with diff report by year.
    """
    # Get totals from different sources
    yearly_totals_sum = sum(precomputed.yearly_totals.values())
    kpi_total_revenue = metrics.get_total_revenue()
    trend_df = precomputed.get_revenue_trend()
    trend_total = trend_df['Revenue'].sum() if not trend_df.empty and 'Revenue' in trend_df.columns else 0.0
    
    # Calculate mismatches
    base_total = yearly_totals_sum if yearly_totals_sum > 0 else 1.0  # Avoid division by zero
    
    mismatch_kpi = abs(yearly_totals_sum - kpi_total_revenue) / base_total * 100 if base_total > 0 else 0
    mismatch_trend = abs(yearly_totals_sum - trend_total) / base_total * 100 if base_total > 0 else 0
    
    # Check if any mismatch exceeds 0.5%
    if mismatch_kpi > 0.5 or mismatch_trend > 0.5:
        print(f"\n[WARNING] ========================================")
        print(f"[WARNING] KPI totals mismatch detected!")
        print(f"[WARNING] ========================================")
        print(f"[WARNING] Yearly Totals Sum:     ${yearly_totals_sum:,.2f}")
        print(f"[WARNING] KPI Total Revenue:     ${kpi_total_revenue:,.2f} (diff: {mismatch_kpi:.2f}%)")
        print(f"[WARNING] Revenue Trend Sum:     ${trend_total:,.2f} (diff: {mismatch_trend:.2f}%)")
        print(f"[WARNING] ========================================")
        
        # Generate diff report by year
        print(f"\n[WARNING] Year-by-year comparison:")
        print(f"  {'Year':<8} {'Yearly_Totals':<18} {'Trend_Revenue':<18} {'Difference':<15} {'Diff_%':<10}")
        print(f"  {'-'*8} {'-'*18} {'-'*18} {'-'*15} {'-'*10}")
        
        for year in sorted(precomputed.yearly_totals.keys()):
            yearly_val = precomputed.yearly_totals.get(year, 0.0)
            trend_row = trend_df[trend_df['Year'] == year] if not trend_df.empty else pd.DataFrame()
            trend_val = trend_row['Revenue'].iloc[0] if not trend_row.empty and 'Revenue' in trend_row.columns else 0.0
            
            diff = abs(yearly_val - trend_val)
            diff_pct = (diff / yearly_val * 100) if yearly_val > 0 else 0.0
            
            print(f"  {int(year):<8} ${yearly_val:>15,.2f} ${trend_val:>15,.2f} ${diff:>12,.2f} {diff_pct:>8.2f}%")
        
        print(f"[WARNING] ========================================\n")
    else:
        print(f"[OK] KPI totals validation passed:")
        print(f"  Yearly Totals Sum: ${yearly_totals_sum:,.2f}")
        print(f"  KPI Total Revenue: ${kpi_total_revenue:,.2f} (diff: {mismatch_kpi:.2f}%)")
        print(f"  Revenue Trend Sum: ${trend_total:,.2f} (diff: {mismatch_trend:.2f}%)")


def compute_data_health(master_df: pd.DataFrame) -> dict:
    """
    Compute data health metrics for debugging.
    Returns a dictionary with data quality metrics.
    """
    if master_df.empty:
        return {
            'total_rows': 0,
            'distinct_years': [],
            'distinct_states': [],
            'distinct_cities': [],
            'revenue_by_year': [],
            'missing_revenue_pct': 100.0,
            'min_revenue': None,
            'max_revenue': None
        }
    
    # Total rows
    total_rows = len(master_df)
    
    # Distinct values (convert to appropriate types)
    if 'year' in master_df.columns:
        distinct_years = sorted([int(y) for y in master_df['year'].dropna().unique() if pd.notna(y)])
    else:
        distinct_years = []
    
    if 'state' in master_df.columns:
        distinct_states = sorted([str(s) for s in master_df['state'].dropna().unique() if pd.notna(s)])
    else:
        distinct_states = []
    
    if 'city' in master_df.columns:
        distinct_cities = sorted([str(c) for c in master_df['city'].dropna().unique() if pd.notna(c)])
    else:
        distinct_cities = []
    
    # Revenue by Year (revenue is already numeric at this point)
    revenue_by_year = []
    if 'year' in master_df.columns and 'revenue' in master_df.columns:
        # Revenue is already numeric, so we can use it directly
        year_revenue = master_df.groupby('year')['revenue'].agg(['sum', 'count']).reset_index()
        for _, row in year_revenue.iterrows():
            revenue_by_year.append({
                'Year': int(row['year']) if pd.notna(row['year']) else None,
                'Total_Revenue': float(row['sum']) if pd.notna(row['sum']) else 0.0,
                'Row_Count': int(row['count']) if pd.notna(row['count']) else 0
            })
        revenue_by_year.sort(key=lambda x: x['Year'] if x['Year'] is not None else 0)
    
    # Missing revenue percentage (revenue is already numeric)
    if 'revenue' in master_df.columns:
        missing_revenue = master_df['revenue'].isna().sum()
        missing_revenue_pct = (missing_revenue / total_rows * 100) if total_rows > 0 else 100.0
    else:
        missing_revenue_pct = 100.0
    
    # Min/Max revenue (revenue is already numeric)
    if 'revenue' in master_df.columns:
        revenue_values = master_df['revenue'].dropna()  # Already numeric, no need for to_numeric
        min_revenue = float(revenue_values.min()) if len(revenue_values) > 0 else None
        max_revenue = float(revenue_values.max()) if len(revenue_values) > 0 else None
    else:
        min_revenue = None
        max_revenue = None
    
    return {
        'total_rows': int(total_rows),
        'distinct_years': distinct_years,
        'distinct_states': distinct_states,
        'distinct_cities': distinct_cities,
        'revenue_by_year': revenue_by_year,
        'missing_revenue_pct': round(missing_revenue_pct, 2),
        'min_revenue': min_revenue,
        'max_revenue': max_revenue
    }


def export_all_data():
    """
    Export all dashboard data to JSON format.
    
    Raises:
        ValueError: If data loading fails
        IOError: If JSON export fails
    """
    try:
        print("Loading data...")
        loader = DataLoader()
        master_df = loader.load_all_files()
        city_metrics = loader.load_city_metrics()
        
        if master_df.empty:
            raise ValueError(
                "No data loaded. Please check that Excel files are in the correct format:\n"
                "  - Row 1: Years (2026-2031)\n"
                "  - Row 2: Column headers\n"
                "  - Row 3+: Monthly data"
            )
        
        # Validate required columns
        required_cols = ['state', 'city', 'year', 'revenue']
        missing_cols = [col for col in required_cols if col not in master_df.columns]
        if missing_cols:
            raise ValueError(f"Master dataframe missing required columns: {missing_cols}")
        
        # Track rows before sanitization
        rows_before_sanitization = len(master_df)
        
        # Additional sanitization check (data_loader already sanitizes, but this is a safety net)
        from data_loader import sanitize_master_df
        master_df, sanitize_metrics = sanitize_master_df(master_df)
        rows_after_sanitization = len(master_df)
        
        if rows_after_sanitization < rows_before_sanitization:
            print(f"[EXPORT] Additional sanitization removed {rows_before_sanitization - rows_after_sanitization:,} rows")
        
        # Enforce strict numeric revenue cleaning
        print("\n[REVENUE] Enforcing strict numeric revenue conversion...")
        if 'revenue' not in master_df.columns:
            raise ValueError("Revenue column not found in master dataframe")
        
        # Track revenue before conversion
        revenue_before_count = master_df['revenue'].notna().sum()
        
        # Create strict numeric revenue column
        master_df['revenue_numeric'] = pd.to_numeric(master_df['revenue'], errors='coerce')
        
        # Check for coercion failures
        nan_count = master_df['revenue_numeric'].isna().sum()
        total_rows = len(master_df)
        nan_percentage = (nan_count / total_rows * 100) if total_rows > 0 else 0
        
        # Track rows dropped due to bad revenue (rows that had revenue but became NaN after conversion)
        rows_dropped_bad_revenue = revenue_before_count - (total_rows - nan_count)
        if rows_dropped_bad_revenue < 0:
            rows_dropped_bad_revenue = 0  # Can't be negative
        
        if nan_count > 0:
            print(f"[REVENUE] {nan_count:,} rows ({nan_percentage:.2f}%) have non-numeric revenue values")
            
            # If more than 0.5% are NaN, print WARNING with examples
            if nan_percentage > 0.5:
                print(f"\n[WARNING] Revenue coercion failure rate ({nan_percentage:.2f}%) exceeds 0.5% threshold!")
                print(f"[WARNING] {nan_count:,} rows have non-numeric revenue values that were coerced to NaN")
                
                # Get sample of raw values causing failures (up to 20)
                failed_rows = master_df[master_df['revenue_numeric'].isna()].copy()
                sample_size = min(20, len(failed_rows))
                sample_rows = failed_rows.head(sample_size)
                
                print(f"\n[WARNING] Sample of {sample_size} raw revenue values that failed conversion:")
                for idx, row in sample_rows.iterrows():
                    raw_value = row['revenue']
                    state = row.get('state', 'N/A')
                    city = row.get('city', 'N/A')
                    year = row.get('year', 'N/A')
                    print(f"  Row {idx}: revenue='{raw_value}' (type: {type(raw_value).__name__}) | State: {state}, City: {city}, Year: {year}")
                
                if len(failed_rows) > sample_size:
                    print(f"  ... and {len(failed_rows) - sample_size} more rows with non-numeric revenue")
            else:
                print(f"[REVENUE] Coercion failure rate ({nan_percentage:.2f}%) is within acceptable range (<=0.5%)")
        
        # Replace revenue column with numeric version
        master_df['revenue'] = master_df['revenue_numeric']
        master_df = master_df.drop(columns=['revenue_numeric'], errors='ignore')
        
        # Calculate revenue NaN percentage after conversion
        revenue_nan_pct_after = nan_percentage
        
        # Track categories loaded and their revenue sums
        categories_loaded = {}
        if 'category' in master_df.columns and 'revenue' in master_df.columns:
            category_revenue = master_df.groupby('category')['revenue'].sum()
            for category, revenue_sum in category_revenue.items():
                categories_loaded[str(category)] = float(revenue_sum) if pd.notna(revenue_sum) else 0.0
        
        # Log final revenue statistics
        valid_revenue_count = master_df['revenue'].notna().sum()
        print(f"[REVENUE] Valid numeric revenue values: {valid_revenue_count:,} / {total_rows:,} rows ({100 - nan_percentage:.2f}%)")
        if valid_revenue_count > 0:
            revenue_stats = master_df['revenue'].describe()
            print(f"[REVENUE] Revenue statistics: min=${revenue_stats['min']:,.2f}, max=${revenue_stats['max']:,.2f}, mean=${revenue_stats['mean']:,.2f}")
        
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error during data loading: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    try:
        print("Precomputing aggregations...")
        precomputed = PrecomputedData(master_df, city_metrics)
        metrics = MetricsCalculator(precomputed)
        
        # Get yearly aggregated data for insights
        yearly_agg_df = precomputed.get_yearly_aggregated_df()
        if yearly_agg_df.empty:
            raise ValueError("Yearly aggregated dataframe is empty")
        
        insights_gen = InsightsGenerator(yearly_agg_df, city_metrics)
        
        print("Calculating metrics...")
    except Exception as e:
        print(f"Error during precomputation: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    # Get actual years for CAGR calculation
    actual_years = sorted(precomputed.yearly_totals.keys())
    cagr_start = actual_years[0] if actual_years else 2026
    cagr_end = actual_years[-1] if actual_years else 2031
    
    # Calculate CAGR using all available years (default: 'All Years')
    print("\n=== CAGR Calculation ===")
    cagr_value = metrics.get_cagr()  # Uses all available years by default
    cagr_display = cagr_value if cagr_value is not None else None
    cagr_label = f"{cagr_start}-{cagr_end}"
    
    # Check for revenue trend anomalies
    trend_df = precomputed.get_revenue_trend()
    if len(trend_df) > 1:
        first_rev = trend_df.iloc[0]['Revenue']
        second_rev = trend_df.iloc[1]['Revenue']
        if first_rev > second_rev * 1.5:
            drop_pct = ((first_rev - second_rev) / first_rev * 100)
            print(f"WARNING: Revenue drops {drop_pct:.1f}% from {trend_df.iloc[0]['Year']:.0f} to {trend_df.iloc[1]['Year']:.0f}")
            print("This may indicate data quality issues or different data structures across years.")
    
    # Compute data health metrics
    data_health = compute_data_health(master_df)
    
    # Build sanitation report
    sanitation_report = {
        'rows_before': int(rows_before_sanitization),
        'rows_after': int(rows_after_sanitization),
        'rows_dropped_header_state_city': int(sanitize_metrics.get('rows_dropped_header_state_city', 0)),
        'rows_dropped_bad_year': int(sanitize_metrics.get('rows_dropped_bad_year', 0)),
        'rows_dropped_bad_revenue': int(rows_dropped_bad_revenue),
        'revenue_nan_pct_after': float(round(revenue_nan_pct_after, 2)),
        'categories_loaded': categories_loaded
    }
    
    print(f"\n[SANITATION_REPORT] Sanitation summary:")
    print(f"  Rows before: {sanitation_report['rows_before']:,}")
    print(f"  Rows after: {sanitation_report['rows_after']:,}")
    print(f"  Dropped (header state/city): {sanitation_report['rows_dropped_header_state_city']:,}")
    print(f"  Dropped (bad year): {sanitation_report['rows_dropped_bad_year']:,}")
    print(f"  Dropped (bad revenue): {sanitation_report['rows_dropped_bad_revenue']:,}")
    print(f"  Revenue NaN % after: {sanitation_report['revenue_nan_pct_after']:.2f}%")
    print(f"  Categories loaded: {len(categories_loaded)} ({', '.join(categories_loaded.keys())})")
    for category, revenue_sum in categories_loaded.items():
        print(f"    - {category}: ${revenue_sum:,.2f}")
    
    # Validate KPI totals agree before export
    _validate_kpi_totals(precomputed, metrics)
    
    # Export all data
    # Get global efficiency metrics and log the denominator used
    global_efficiency = precomputed.get_global_efficiency()
    total_revenue_all_years = metrics.get_total_revenue()
    total_shops_all_years = precomputed.total_shops if hasattr(precomputed, 'total_shops') else metrics.get_total_shops()
    total_providers_all_years = precomputed.total_providers if hasattr(precomputed, 'total_providers') else metrics.get_total_service_providers()
    
    print(f"\n[EFFICIENCY] KPI Efficiency Metrics (All-years aggregates):")
    print(f"  Total Revenue (all years): ${total_revenue_all_years:,.2f}")
    print(f"  Total Shops (all-years total): {total_shops_all_years:,.0f}")
    print(f"  Total Providers (all-years total): {total_providers_all_years:,.0f}")
    print(f"  Revenue per Shop: ${global_efficiency.get('revenue_per_shop', 0):,.2f} (denominator: all-years shop total)")
    print(f"  Revenue per Provider: ${global_efficiency.get('revenue_per_provider', 0):,.2f} (denominator: all-years provider total)")
    
    export_data = {
        'kpis': {
            'total_revenue': total_revenue_all_years,
            'cagr': cagr_display,  # Can be None for N/A cases
            'cagr_years': cagr_label,  # Store actual years used
            'total_shops': total_shops_all_years,
            'total_providers': total_providers_all_years,
            'revenue_per_shop': global_efficiency.get('revenue_per_shop', 0.0),
            'revenue_per_provider': global_efficiency.get('revenue_per_provider', 0.0)
        },
        'data_health': data_health,  # Developer debug panel data
        'sanitation_report': sanitation_report,  # Data ingestion quality metrics
        'revenue_trend': precomputed.get_revenue_trend().to_dict('records'),
        'revenue_by_category': precomputed.get_revenue_by_category().to_dict('records'),
        'revenue_by_state': precomputed.get_revenue_by_state().to_dict('records'),
        'revenue_per_shop_by_state': precomputed.get_revenue_per_shop_by_state(top_n=None).to_dict('records'),  # Export all for dynamic Top N
        'revenue_per_provider_by_state': precomputed.get_revenue_per_provider_by_state(top_n=None).to_dict('records'),  # Export all for dynamic Top N
        'ecosystem_size_vs_revenue': precomputed.get_ecosystem_size_vs_revenue().to_dict('records'),
        'top_cities': precomputed.get_top_cities(10).to_dict('records'),
        'top_cities_pareto': precomputed.get_top_cities_pareto(15).to_dict('records'),  # Default Top 15
        'pareto_data': precomputed.get_pareto_data().to_dict('records'),
        'insights': insights_gen.get_all_insights(),
        'projections': insights_gen.get_projection([2032, 2033, 2034]).to_dict('records'),
        'valuation': insights_gen.get_valuation([3.0, 5.0, 8.0]),
        'filters': {
            'years': sorted([int(y) for y in master_df['year'].dropna().unique() if pd.notna(y)]) if 'year' in master_df.columns else [],
            'states': sorted([str(s) for s in master_df['state'].dropna().unique() if pd.notna(s) and str(s).lower() != 'city' and str(s).lower() != 'state']) if 'state' in master_df.columns else [],
            'cities': sorted([str(c) for c in master_df['city'].dropna().unique() if pd.notna(c) and str(c).lower() != 'city' and str(c).lower() != 'state']) if 'city' in master_df.columns else []
        }
    }
    
    # Convert numpy types to native Python types and filter negative values
    def convert_to_native(obj):
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                # Special handling for sanitation_report - preserve integer types
                if k == 'sanitation_report' and isinstance(v, dict):
                    sanitized = {}
                    for sk, sv in v.items():
                        if sk in ['rows_before', 'rows_after', 'rows_dropped_header_state_city', 
                                 'rows_dropped_bad_year', 'rows_dropped_bad_revenue']:
                            # Preserve as integer
                            sanitized[sk] = int(sv) if pd.notna(sv) else 0
                        elif sk == 'categories_loaded' and isinstance(sv, dict):
                            # Preserve category revenue sums as floats
                            sanitized[sk] = {cat: float(rev) if pd.notna(rev) else 0.0 
                                           for cat, rev in sv.items()}
                        else:
                            sanitized[sk] = convert_to_native(sv)
                    result[k] = sanitized
                    continue
                
                # Filter out negative values for revenue-related metrics
                if isinstance(v, (int, float, np.integer, np.floating)) and pd.notna(v):
                    if 'revenue' in k.lower() and 'cagr' not in k.lower():
                        # Set negative values to 0 for revenue metrics (but allow negative CAGR/growth)
                        if v < 0:
                            v = 0.0
                    elif 'cagr' in k.lower() or 'growth' in k.lower():
                        # Allow negative CAGR and growth rates (they indicate decline)
                        pass
                    elif v < 0:
                        # For other metrics, set to 0 if negative
                        v = 0.0
                result[k] = convert_to_native(v)
            return result
        elif isinstance(obj, list):
            result = []
            for item in obj:
                converted = convert_to_native(item)
                # Filter out records with negative revenue values
                if isinstance(converted, dict):
                    has_negative_revenue = False
                    for key, val in converted.items():
                        if 'revenue' in key.lower() and isinstance(val, (int, float)) and val < 0:
                            has_negative_revenue = True
                            break
                    if not has_negative_revenue:
                        # Also set any negative revenue to 0
                        cleaned = {}
                        for key, val in converted.items():
                            if 'revenue' in key.lower() and isinstance(val, (int, float)) and val < 0:
                                cleaned[key] = 0.0
                            else:
                                cleaned[key] = val
                        result.append(cleaned)
                    else:
                        # Skip records with negative revenue
                        continue
                else:
                    result.append(converted)
            return result
        elif isinstance(obj, pd.Timestamp):
            return None
        elif pd.isna(obj):
            return None
        elif isinstance(obj, (int, float, np.integer, np.floating)):
            if pd.notna(obj):
                # Preserve integers for sanitation_report fields
                if isinstance(obj, (int, np.integer)):
                    return int(obj)
                else:
                    return float(obj)
            return None
        elif isinstance(obj, (bool, np.bool_)):
            return bool(obj)
        elif isinstance(obj, str):
            return obj
        else:
            try:
                # Try to convert to float if numeric
                val = float(obj) if pd.notna(obj) else None
                # Note: Negative values are allowed for CAGR/growth (handled in dict processing)
                return val
            except (ValueError, TypeError):
                return str(obj) if obj is not None else None
    
    export_data = convert_to_native(export_data)
    
    # Ensure revenue KPIs are non-negative (but allow negative CAGR/growth and None for N/A)
    if 'kpis' in export_data:
        for key, value in export_data['kpis'].items():
            if value is None:
                # Keep None for N/A cases (CAGR, growth)
                continue
            if isinstance(value, (int, float)) and value < 0:
                if 'cagr' not in key.lower() and 'growth' not in key.lower():
                    export_data['kpis'][key] = 0.0
    
    try:
        # Final validation before export
        print("\n=== Final KPI Validation Before Export ===")
        _validate_kpi_totals(precomputed, metrics)
        
        print("Exporting to data.json...")
        # Convert to native types before JSON serialization
        export_data_native = convert_to_native(export_data)
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(export_data_native, f, indent=2, ensure_ascii=False)
        
        # Validate file was created and is readable
        import os
        if not os.path.exists('data.json'):
            raise IOError("data.json was not created")
        
        file_size = os.path.getsize('data.json')
        if file_size == 0:
            raise IOError("data.json is empty")
        
        print("Data exported successfully to data.json")
        print(f"   Total records: {len(master_df):,}")
        print(f"   Years: {export_data['filters']['years']}")
        print(f"   States: {len(export_data['filters']['states'])}")
        print(f"   Cities: {len(export_data['filters']['cities'])}")
        print(f"   File size: {file_size / 1024 / 1024:.2f} MB")
    except IOError as e:
        print(f"Error writing data.json: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error during export: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    export_all_data()
