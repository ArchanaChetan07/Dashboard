"""
Data loading module for Weelocal Economic Engine Dashboard.
Handles Excel file loading and data transformation.
"""

import pandas as pd
import numpy as np
from typing import Optional
import warnings
warnings.filterwarnings('ignore')


def sanitize_master_df(df: pd.DataFrame) -> tuple:
    """
    Remove header rows that leaked into data and invalid rows.
    
    Rules:
    1. Remove rows where state == "state" or city == "city" (case-insensitive, trimmed)
    2. Remove rows where year is null or not numeric
    
    Args:
        df: Master dataframe to sanitize
        
    Returns:
        Tuple of (sanitized_dataframe, metrics_dict) where metrics_dict contains:
        - rows_before: int
        - rows_after: int
        - rows_dropped_header_state_city: int
        - rows_dropped_bad_year: int
    """
    if df.empty:
        return df, {
            'rows_before': 0,
            'rows_after': 0,
            'rows_dropped_header_state_city': 0,
            'rows_dropped_bad_year': 0
        }
    
    original_count = len(df)
    df_clean = df.copy()
    
    # Rule 1: Remove header rows (state == "state" or city == "city")
    header_rows_removed = 0
    if 'state' in df_clean.columns:
        # Case-insensitive check for "state" header
        state_header_mask = df_clean['state'].astype(str).str.strip().str.lower() == 'state'
        header_rows_removed += state_header_mask.sum()
        df_clean = df_clean[~state_header_mask].copy()
    
    if 'city' in df_clean.columns:
        # Case-insensitive check for "city" header
        city_header_mask = df_clean['city'].astype(str).str.strip().str.lower() == 'city'
        header_rows_removed += city_header_mask.sum()
        df_clean = df_clean[~city_header_mask].copy()
    
    if header_rows_removed > 0:
        print(f"[SANITIZE] Removed {header_rows_removed:,} header rows (state=='state' or city=='city')")
    
    # Rule 2: Remove rows where year is null or not numeric
    invalid_year_rows = 0
    if 'year' in df_clean.columns:
        # Convert year to numeric, coercing errors to NaN
        df_clean['year'] = pd.to_numeric(df_clean['year'], errors='coerce')
        # Count rows with invalid years (NaN or not in valid range)
        invalid_year_mask = df_clean['year'].isna()
        invalid_year_rows = invalid_year_mask.sum()
        if invalid_year_rows > 0:
            df_clean = df_clean[~invalid_year_mask].copy()
            print(f"[SANITIZE] Removed {invalid_year_rows:,} rows with null or non-numeric year")
    
    total_removed = original_count - len(df_clean)
    if total_removed > 0:
        print(f"[SANITIZE] Total removed: {total_removed:,} rows ({total_removed/original_count*100:.2f}%)")
        print(f"[SANITIZE] Remaining rows: {len(df_clean):,}")
    else:
        print(f"[SANITIZE] No invalid rows found. All {original_count:,} rows are valid.")
    
    metrics = {
        'rows_before': int(original_count),
        'rows_after': int(len(df_clean)),
        'rows_dropped_header_state_city': int(header_rows_removed),
        'rows_dropped_bad_year': int(invalid_year_rows)
    }
    
    return df_clean, metrics


class DataLoader:
    """Loads and processes Weelocal Excel data files."""
    
    def __init__(self):
        self.file_mapping = {
            'Book1.xlsx': 'shopsrestraunt',
            'Book2.xlsx': 'service_providers',
            'Book4.xlsx': 'helpers',
            'Book5.xlsx': 'number of shops',
            'Book6.xlsx': 'number of service providers'
        }
        self.master_df: Optional[pd.DataFrame] = None
        self.city_metrics: Optional[pd.DataFrame] = None
        
    def load_excel_file(self, filepath: str, sheet_name: str) -> pd.DataFrame:
        """
        Load Excel file with special handling:
        - Row 1 contains years (2026-2031)
        - Row 2 contains actual headers
        - Monthly data follows
        
        Args:
            filepath: Path to Excel file
            sheet_name: Name of sheet to load
            
        Returns:
            DataFrame with processed data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid format
        """
        import os
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Excel file not found: {filepath}")
        
        try:
            # Read first two rows to get years and headers
            df_years = pd.read_excel(filepath, sheet_name=sheet_name, header=None, nrows=1)
            df_headers = pd.read_excel(filepath, sheet_name=sheet_name, header=None, skiprows=1, nrows=1)
            
            # Validate that we have data
            if df_years.empty or df_headers.empty:
                raise ValueError(f"File {filepath} sheet {sheet_name} has empty header rows")
            
            # Read actual data starting from row 3 (index 2)
            df_data = pd.read_excel(filepath, sheet_name=sheet_name, header=None, skiprows=2)
            
            if df_data.empty:
                raise ValueError(f"File {filepath} sheet {sheet_name} has no data rows")
                
        except FileNotFoundError:
            raise
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error reading {filepath} sheet {sheet_name}: {str(e)}")
        
        # Get years from first row
        years = df_years.iloc[0].values
        
        # Get headers from second row
        headers = df_headers.iloc[0].values
        
        # Combine years and headers for column names
        # Year ranges span multiple columns, so we need to propagate the year
        column_names = []
        current_year = None
        
        for i, (year, header) in enumerate(zip(years, headers)):
            year_str = str(year) if pd.notna(year) else ""
            header_str = str(header) if pd.notna(header) else ""
            
            # Check if this column has a year (year range like "2026-2027" or single year)
            if year_str and any(str(y) in year_str for y in range(2026, 2032)):
                # Extract first year from range (e.g., "2026-2027" -> 2026)
                for y in range(2026, 2032):
                    if str(y) in year_str:
                        current_year = y
                        break
            elif pd.notna(year) and isinstance(year, (int, float)) and year >= 2026 and year <= 2031:
                current_year = int(year)
            
            # Build column name
            if current_year and header_str and header_str.lower() not in ['state', 'city', 'area', 'nan']:
                # Month or data column with year
                column_names.append(f"{current_year}_{header_str}")
            elif current_year and not header_str:
                column_names.append(f"Year_{current_year}")
            elif header_str and header_str.lower() not in ['nan', '']:
                # Regular metadata column (State, City, Area, Revenue)
                column_names.append(header_str)
            else:
                column_names.append(f"Col_{i}")
        
        df_data.columns = column_names[:len(df_data.columns)]
        
        return df_data
    
    def standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to lowercase with underscores."""
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        return df
    
    def _parse_month(self, month_str: str) -> str:
        """Parse month string to standard month name."""
        month_str = str(month_str).lower().strip('_')
        month_map = {
            'jan': 'January', 'january': 'January', '1': 'January',
            'feb': 'February', 'february': 'February', '2': 'February',
            'mar': 'March', 'march': 'March', '3': 'March',
            'apr': 'April', 'april': 'April', '4': 'April',
            'may': 'May', '5': 'May',
            'jun': 'June', 'june': 'June', '6': 'June',
            'jul': 'July', 'july': 'July', '7': 'July',
            'aug': 'August', 'august': 'August', '8': 'August',
            'sep': 'September', 'september': 'September', '9': 'September',
            'oct': 'October', 'october': 'October', '10': 'October',
            'nov': 'November', 'november': 'November', '11': 'November',
            'dec': 'December', 'december': 'December', '12': 'December'
        }
        return month_map.get(month_str, 'January')
    
    def convert_to_long_format(self, df: pd.DataFrame, category: str) -> pd.DataFrame:
        """
        Convert monthly wide format (2026-2031) into long format.
        Final schema: State, City, Area (if exists), Category, Year, Month, Monthly_Value, Revenue
        """
        # Identify year columns (columns that contain a year 2026-2031)
        year_columns = []
        for col in df.columns:
            col_str = str(col)
            for year in range(2026, 2032):
                if str(year) in col_str:
                    year_columns.append(col)
                    break
        
        # Identify metadata columns (State, City, Area, Revenue)
        metadata_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
            if col not in year_columns:
                if any(term in col_lower for term in ['state', 'city', 'area', 'revenu']):
                    metadata_cols.append(col)
        
        # If no year columns found, return empty
        if not year_columns:
            return pd.DataFrame()
        
        # Melt the dataframe
        id_vars = [col for col in metadata_cols if col in df.columns]
        value_vars = [col for col in year_columns if col in df.columns]
        
        if not value_vars:
            return pd.DataFrame()
        
        df_long = pd.melt(
            df,
            id_vars=id_vars,
            value_vars=value_vars,
            var_name='year_month',
            value_name='monthly_value'
        )
        
        # Extract year and month using vectorized operations
        df_long['year'] = None
        for year in range(2026, 2032):
            mask = df_long['year_month'].astype(str).str.contains(str(year), na=False)
            df_long.loc[mask, 'year'] = year
        
        # Extract month
        def extract_month(year_month_str):
            year_month_str = str(year_month_str)
            for year in range(2026, 2032):
                if str(year) in year_month_str:
                    parts = year_month_str.split(str(year))
                    if len(parts) > 1:
                        month_part = parts[-1].strip('_').strip()
                        return self._parse_month(month_part)
            return 'January'
        
        df_long['month'] = df_long['year_month'].apply(extract_month)
        df_long = df_long[df_long['year'].notna()].copy()
        df_long['category'] = category
        
        # Rename columns to standard names
        rename_map = {}
        for col in df_long.columns:
            col_lower = str(col).lower()
            if 'state' in col_lower and 'state' not in rename_map.values():
                rename_map[col] = 'state'
            elif 'city' in col_lower and 'city' not in rename_map.values():
                rename_map[col] = 'city'
            elif 'area' in col_lower and 'area' not in rename_map.values():
                rename_map[col] = 'area'
            elif 'revenu' in col_lower and 'revenue' not in rename_map.values():
                rename_map[col] = 'revenue'
        
        df_long = df_long.rename(columns=rename_map)
        
        # If revenue column doesn't exist, use monthly_value as revenue
        if 'revenue' not in df_long.columns and 'monthly_value' in df_long.columns:
            df_long['revenue'] = df_long['monthly_value']
        
        # Select and reorder final columns
        final_cols = ['state', 'city', 'area', 'category', 'year', 'month', 'monthly_value', 'revenue']
        final_cols = [col for col in final_cols if col in df_long.columns]
        
        df_long = df_long[final_cols].copy()
        
        # Ensure data types
        if 'year' in df_long.columns:
            df_long['year'] = df_long['year'].astype(int)
        if 'monthly_value' in df_long.columns:
            df_long['monthly_value'] = pd.to_numeric(df_long['monthly_value'], errors='coerce')
        if 'revenue' in df_long.columns:
            df_long['revenue'] = pd.to_numeric(df_long['revenue'], errors='coerce')
            # Fill any NaN revenue values with monthly_value
            if 'monthly_value' in df_long.columns:
                df_long['revenue'] = df_long['revenue'].fillna(df_long['monthly_value'])
        
        return df_long
    
    def load_all_files(self) -> pd.DataFrame:
        """Load all Excel files and combine into master dataframe with debug logging."""
        """
        Load all Excel files and combine into master dataframe.
        
        Returns:
            Combined DataFrame with all data
            
        Raises:
            ValueError: If no files could be loaded
        """
        all_dfs = []
        errors = []
        
        for filename, sheet_name in self.file_mapping.items():
            try:
                # Use robust loader for service_providers
                if filename == 'Book2.xlsx' and sheet_name == 'service_providers':
                    try:
                        from pathlib import Path
                        from service_providers_loader import ServiceProvidersLoader
                        
                        # Get absolute path
                        abs_path = Path(filename).resolve()
                        print(f"[DEBUG] Loading Book2.xlsx from: {abs_path}")
                        print(f"[DEBUG] File exists: {abs_path.exists()}")
                        
                        loader = ServiceProvidersLoader(str(abs_path), sheet_name)
                        df_long = loader.load_and_transform()
                        
                        print(f"[DEBUG] Book2.xlsx loaded - Shape: {df_long.shape}")
                        print(f"[DEBUG] Book2.xlsx columns (before standardization): {list(df_long.columns)}")
                        
                        if not df_long.empty:
                            # Standardize column names to match master schema (lowercase)
                            column_mapping = {
                                'State': 'state',
                                'City': 'city',
                                'Service_Provider': 'service_provider',  # Keep for reference but not in final schema
                                'Year': 'year',
                                'Month': 'month',
                                'Month_Num': 'month_num',
                                'Monthly_Value': 'monthly_value',
                                'Revenue': 'revenue'
                            }
                            
                            # Rename columns that exist
                            rename_map = {old: new for old, new in column_mapping.items() if old in df_long.columns}
                            df_long = df_long.rename(columns=rename_map)
                            
                            # Add category column to match other files
                            df_long['category'] = 'service_providers'
                            
                            # Select only columns that match master schema
                            master_schema_cols = ['state', 'city', 'year', 'month', 'month_num', 'monthly_value', 'revenue', 'category']
                            available_cols = [col for col in master_schema_cols if col in df_long.columns]
                            df_long = df_long[available_cols].copy()
                            
                            print(f"[DEBUG] Book2.xlsx columns (after standardization): {list(df_long.columns)}")
                            print(f"[DEBUG] Book2.xlsx head(3):\n{df_long.head(3)}")
                            
                            if 'year' in df_long.columns:
                                years = sorted(df_long['year'].dropna().unique())
                                print(f"[DEBUG] Book2.xlsx years: {years}")
                            
                            # Runtime check: Ensure Book2 contributes non-zero revenue
                            if 'revenue' in df_long.columns:
                                total_revenue = df_long['revenue'].sum()
                                revenue_by_year = df_long.groupby('year')['revenue'].sum() if 'year' in df_long.columns else pd.Series()
                                
                                print(f"[DEBUG] Book2.xlsx total revenue: ${total_revenue:,.2f}")
                                if not revenue_by_year.empty:
                                    print(f"[DEBUG] Book2.xlsx revenue by year:\n{revenue_by_year}")
                                
                                # Assertion/runtime check: Book2 must contribute non-zero revenue
                                if total_revenue == 0 or pd.isna(total_revenue):
                                    print(f"\n[WARNING] ========================================")
                                    print(f"[WARNING] Book2.xlsx (service_providers) contributes ZERO revenue!")
                                    print(f"[WARNING] Total revenue: ${total_revenue:,.2f}")
                                    print(f"[WARNING] This may indicate a data loading or mapping issue.")
                                    print(f"[WARNING] ========================================\n")
                                elif total_revenue < 0:
                                    print(f"\n[WARNING] ========================================")
                                    print(f"[WARNING] Book2.xlsx (service_providers) has NEGATIVE revenue!")
                                    print(f"[WARNING] Total revenue: ${total_revenue:,.2f}")
                                    print(f"[WARNING] ========================================\n")
                                else:
                                    print(f"[OK] Book2.xlsx revenue validation passed: ${total_revenue:,.2f}")
                            
                            all_dfs.append(df_long)
                        else:
                            print(f"[WARNING] Book2.xlsx loaded but dataframe is empty!")
                    except ImportError as e:
                        errors.append(f"Failed to import ServiceProvidersLoader: {e}")
                    except Exception as e:
                        errors.append(f"Error loading {filename} with ServiceProvidersLoader: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    # Use standard loader for other files
                    try:
                        from pathlib import Path
                        abs_path = Path(filename).resolve()
                        print(f"[DEBUG] Loading {filename} from: {abs_path}")
                        print(f"[DEBUG] File exists: {abs_path.exists()}")
                        
                        df = self.load_excel_file(str(abs_path), sheet_name)
                        print(f"[DEBUG] {filename} loaded - Shape: {df.shape}")
                        print(f"[DEBUG] {filename} columns: {list(df.columns)}")
                        if not df.empty:
                            print(f"[DEBUG] {filename} head(3):\n{df.head(3)}")
                        
                        df = self.standardize_column_names(df)
                        category = sheet_name.replace(' ', '_')
                        df_long = self.convert_to_long_format(df, category)
                        
                        print(f"[DEBUG] {filename} after convert_to_long_format - Shape: {df_long.shape}")
                        if not df_long.empty:
                            print(f"[DEBUG] {filename} long format columns: {list(df_long.columns)}")
                            if 'year' in df_long.columns:
                                print(f"[DEBUG] {filename} years: {sorted(df_long['year'].unique())}")
                            if 'revenue' in df_long.columns:
                                revenue_by_year = df_long.groupby('year')['revenue'].sum()
                                print(f"[DEBUG] {filename} revenue by year:\n{revenue_by_year}")
                            all_dfs.append(df_long)
                    except (FileNotFoundError, ValueError) as e:
                        errors.append(f"Error loading {filename}: {e}")
                        import traceback
                        traceback.print_exc()
                    except Exception as e:
                        errors.append(f"Unexpected error loading {filename}: {e}")
                        import traceback
                        traceback.print_exc()
            except Exception as e:
                errors.append(f"Critical error processing {filename}: {e}")
        
        # Log errors but continue if we have some data
        if errors:
            print("Warnings during data loading:")
            for error in errors:
                print(f"  - {error}")
        
        if all_dfs:
            try:
                print(f"[DEBUG] Combining {len(all_dfs)} dataframes...")
                self.master_df = pd.concat(all_dfs, ignore_index=True)
                print(f"[DEBUG] Master dataframe shape: {self.master_df.shape}")
                print(f"[DEBUG] Master dataframe columns: {list(self.master_df.columns)}")
                
                # Validate we have required columns
                required_cols = ['state', 'city', 'year', 'revenue']
                missing_cols = [col for col in required_cols if col not in self.master_df.columns]
                if missing_cols:
                    raise ValueError(f"Missing required columns: {missing_cols}")
                
                # Sanitize data: remove header rows and invalid data
                print("\n[SANITIZE] Applying data sanitization...")
                self.master_df, _ = sanitize_master_df(self.master_df)  # Metrics tracked in export_data.py
                
                # Debug: Show years and revenue totals after sanitization
                if 'year' in self.master_df.columns and 'revenue' in self.master_df.columns:
                    revenue_by_year = self.master_df.groupby('year')['revenue'].sum()
                    print(f"[DEBUG] Master dataframe - Years present: {sorted(self.master_df['year'].unique())}")
                    print(f"[DEBUG] Master dataframe - Revenue by year:\n{revenue_by_year}")
                
                return self.master_df
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise ValueError(f"Error combining dataframes: {e}")
        else:
            if errors:
                raise ValueError(f"Failed to load any data files. Errors: {'; '.join(errors)}")
            return pd.DataFrame()
    
    def load_city_metrics(self) -> pd.DataFrame:
        """
        Load and merge Book5 and Book6 for city-level metrics.
        
        Returns:
            Merged DataFrame with city metrics
            
        Raises:
            FileNotFoundError: If required files don't exist
            ValueError: If data format is invalid
        """
        import os
        try:
            # Validate files exist
            if not os.path.exists('Book5.xlsx'):
                raise FileNotFoundError("Book5.xlsx not found")
            if not os.path.exists('Book6.xlsx'):
                raise FileNotFoundError("Book6.xlsx not found")
            
            # Book5 and Book6 have simple structure: headers in row 0, data from row 1
            df_shops = pd.read_excel('Book5.xlsx', sheet_name='number of shops', header=0)
            if df_shops.empty:
                raise ValueError("Book5.xlsx has no data")
            df_shops = self.standardize_column_names(df_shops)
            
            df_providers = pd.read_excel('Book6.xlsx', sheet_name='number of service providers', header=0)
            if df_providers.empty:
                raise ValueError("Book6.xlsx has no data")
            df_providers = self.standardize_column_names(df_providers)
            
            # Rename columns to standard names
            rename_map_shops = {}
            rename_map_providers = {}
            
            for col in df_shops.columns:
                col_lower = str(col).lower()
                if 'state' in col_lower:
                    rename_map_shops[col] = 'state'
                elif 'city' in col_lower:
                    rename_map_shops[col] = 'city'
                elif 'shop' in col_lower:
                    rename_map_shops[col] = 'number_of_shops'
            
            for col in df_providers.columns:
                col_lower = str(col).lower()
                if 'state' in col_lower:
                    rename_map_providers[col] = 'state'
                elif 'city' in col_lower:
                    rename_map_providers[col] = 'city'
                elif 'provider' in col_lower:
                    rename_map_providers[col] = 'number_of_service_providers'
            
            df_shops = df_shops.rename(columns=rename_map_shops)
            df_providers = df_providers.rename(columns=rename_map_providers)
            
            # Merge on city (and state if available)
            merge_cols = []
            for col in ['state', 'city']:
                if col in df_shops.columns and col in df_providers.columns:
                    merge_cols.append(col)
            
            if merge_cols:
                self.city_metrics = pd.merge(
                    df_shops, df_providers,
                    on=merge_cols,
                    how='outer',
                    suffixes=('_shops', '_providers')
                )
            elif 'city' in df_shops.columns and 'city' in df_providers.columns:
                self.city_metrics = pd.merge(
                    df_shops, df_providers,
                    on='city',
                    how='outer',
                    suffixes=('_shops', '_providers')
                )
            else:
                self.city_metrics = pd.DataFrame()
            
            # Validate merge was successful
            if self.city_metrics.empty:
                print("Warning: City metrics merge resulted in empty dataframe")
            
            return self.city_metrics
        except FileNotFoundError as e:
            print(f"Error: {e}")
            self.city_metrics = pd.DataFrame()
            return self.city_metrics
        except ValueError as e:
            print(f"Error: Invalid data format - {e}")
            self.city_metrics = pd.DataFrame()
            return self.city_metrics
        except Exception as e:
            print(f"Unexpected error loading city metrics: {str(e)}")
            import traceback
            traceback.print_exc()
            self.city_metrics = pd.DataFrame()
            return self.city_metrics
    
    def get_master_dataframe(self) -> pd.DataFrame:
        """Return the cleaned master dataframe."""
        if self.master_df is None:
            self.load_all_files()
        return self.master_df.copy() if self.master_df is not None else pd.DataFrame()
    
    def get_city_metrics(self) -> pd.DataFrame:
        """Return city metrics dataframe."""
        if self.city_metrics is None:
            self.load_city_metrics()
        return self.city_metrics.copy() if self.city_metrics is not None else pd.DataFrame()
