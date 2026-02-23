"""
Robust data preparation for service_providers sheet.
Converts wide format (year blocks with Jan-Dec columns) to long format.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class ServiceProvidersLoader:
    """
    Robust loader for service_providers sheet with year block detection.
    Converts wide format to long format with proper year/month mapping.
    """
    
    # Expected year blocks
    EXPECTED_YEAR_BLOCKS = [
        (2026, 2027),  # 2026-2027
        (2027, 2028),  # 2027-2028
        (2028, 2029),  # 2028-2029
        (2029, 2030),  # 2029-2030
        (2030, 2031),  # 2030-2031
    ]
    
    # Month names in order
    MONTH_NAMES = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    # Month name to number mapping
    MONTH_TO_NUM = {month: i+1 for i, month in enumerate(MONTH_NAMES)}
    
    def __init__(self, filepath: str = 'Book2.xlsx', sheet_name: str = 'service_providers'):
        self.filepath = filepath
        self.sheet_name = sheet_name
        self.long_df: Optional[pd.DataFrame] = None
    
    def load_and_transform(self) -> pd.DataFrame:
        """
        Main entry point: Load Excel and transform to long format.
        Returns: DataFrame with columns: State, City, Service_Provider, Year, Month, Monthly_Value, Revenue
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        import os
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"File not found: {self.filepath}")
        
        try:
            # Step 1: Read Excel file
            df_years, df_headers, df_data = self._read_excel_layers()
            
            # Store df_headers for later validation
            self.df_headers = df_headers
            
            # Validate we have data
            if df_data.empty:
                raise ValueError(f"File {self.filepath} has no data rows")
            
            # Step 2: Detect year blocks
            year_blocks = self._detect_year_blocks(df_years, df_headers)
            
            if not year_blocks:
                raise ValueError(f"No year blocks detected in {self.filepath}")
            
            # Step 3: Process each year block
            all_long_dfs = []
            for start_year, end_year, block_info in year_blocks:
                try:
                    long_df = self._process_year_block(df_data, start_year, end_year, block_info)
                    if not long_df.empty:
                        all_long_dfs.append(long_df)
                except Exception as e:
                    print(f"Warning: Error processing year block {start_year}-{end_year}: {e}")
                    continue
            
            # Step 4: Combine all year blocks
            if all_long_dfs:
                self.long_df = pd.concat(all_long_dfs, ignore_index=True)
            else:
                self.long_df = pd.DataFrame()
                raise ValueError(f"No valid data processed from {self.filepath}")
            
            # Step 5: Post-process and validate
            self.long_df = self._post_process(self.long_df)
            
            # Step 6: Post-validation for revenue extraction
            self._validate_revenue_extraction(self.long_df, self.df_headers)
            
            # Step 7: Final validation
            self._validate_data(self.long_df)
            
            return self.long_df
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            raise ValueError(f"Error processing {self.filepath}: {str(e)}")
    
    def _read_excel_layers(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Read the three layers of the Excel file."""
        # Row 1: Years
        df_years = pd.read_excel(self.filepath, sheet_name=self.sheet_name, header=None, nrows=1)
        # Row 2: Headers
        df_headers = pd.read_excel(self.filepath, sheet_name=self.sheet_name, header=None, skiprows=1, nrows=1)
        # Row 3+: Data
        df_data = pd.read_excel(self.filepath, sheet_name=self.sheet_name, header=None, skiprows=2)
        
        return df_years, df_headers, df_data
    
    def _detect_year_blocks(self, df_years: pd.DataFrame, df_headers: pd.DataFrame) -> List[Tuple[int, int, Dict]]:
        """
        Detect year blocks in the Excel file.
        Returns: List of (start_year, end_year, block_info) tuples
        """
        year_blocks = []
        years_row = df_years.iloc[0].values
        headers_row = df_headers.iloc[0].values
        
        current_block = None
        block_start_col = None
        
        for col_idx in range(len(years_row)):
            year_val = years_row[col_idx] if col_idx < len(years_row) else None
            header_val = headers_row[col_idx] if col_idx < len(headers_row) else None
            
            year_str = str(year_val) if pd.notna(year_val) else ""
            header_str = str(header_val) if pd.notna(header_val) else ""
            
            # Check if this is a year block header (e.g., "2026-2027")
            block_detected = False
            for start_year, end_year in self.EXPECTED_YEAR_BLOCKS:
                block_pattern = f"{start_year}-{end_year}"
                if block_pattern in year_str:
                    # Start a new block
                    if current_block is not None:
                        # Save previous block
                        year_blocks.append(current_block)
                    
                    current_block = {
                        'start_year': start_year,
                        'end_year': end_year,
                        'start_col': col_idx,
                        'month_cols': [],
                        'revenue_col': None,
                        'metadata_cols': {}
                    }
                    block_start_col = col_idx
                    block_detected = True
                    break
            
            # If we're in a block, track columns
            if current_block is not None and not block_detected:
                header_lower = header_str.lower()
                
                # Check for month columns
                if header_lower in ['jan', 'january', 'feb', 'february', 'mar', 'march',
                                   'apr', 'april', 'may', 'jun', 'june', 'jul', 'july',
                                   'aug', 'august', 'sep', 'september', 'oct', 'october',
                                   'nov', 'november', 'dec', 'december']:
                    current_block['month_cols'].append((col_idx, header_str))
                
                # Check for revenue column (within this block) - improved detection
                elif self._is_revenue_header(header_lower):
                    if current_block['revenue_col'] is None:
                        current_block['revenue_col'] = col_idx
                
                # Check for metadata columns (State, City, Service_Provider) - only in first block
                elif header_lower in ['state', 'city', 'service_provider', 'service provider']:
                    # Only capture metadata from the first block (they're shared across all blocks)
                    if not year_blocks and header_lower not in current_block['metadata_cols']:
                        current_block['metadata_cols'][header_lower] = col_idx
                
                # Check if we've moved to a new block (year value changes to a new year block)
                elif year_str and any(f"{y}-{y+1}" in year_str for y in range(2026, 2031)):
                    # This is the start of a new block, save current one
                    if len(current_block['month_cols']) > 0:  # Only save if we have data
                        # Copy metadata to all blocks (they're shared)
                        for existing_block in year_blocks:
                            existing_block['metadata_cols'] = current_block['metadata_cols'].copy()
                        year_blocks.append(current_block)
                    current_block = None
                    block_start_col = None
        
        # Save the last block
        if current_block is not None and len(current_block['month_cols']) > 0:
            # Copy metadata to all blocks (they're shared)
            for existing_block in year_blocks:
                existing_block['metadata_cols'] = current_block['metadata_cols'].copy()
            year_blocks.append(current_block)
        
        # Ensure all blocks have metadata (copy from first block if available)
        if year_blocks:
            first_block_metadata = year_blocks[0]['metadata_cols']
            for block in year_blocks[1:]:
                if not block['metadata_cols']:
                    block['metadata_cols'] = first_block_metadata.copy()
        
        # Improve revenue column detection: scan around blocks if not found
        for block in year_blocks:
            if block['revenue_col'] is None:
                # Revenue not found inside block, scan ±5 columns around the block
                block_start = block['start_col']
                block_end = block_start + len(block['month_cols']) if block['month_cols'] else block_start + 12
                scan_start = max(0, block_start - 5)
                scan_end = min(len(headers_row), block_end + 5)
                
                # Find closest revenue-like header
                revenue_candidates = []
                for col_idx in range(scan_start, scan_end):
                    if col_idx < len(headers_row):
                        header_val = headers_row[col_idx] if col_idx < len(headers_row) else None
                        header_str = str(header_val) if pd.notna(header_val) else ""
                        header_lower = header_str.lower()
                        
                        if self._is_revenue_header(header_lower):
                            # Calculate distance from block center
                            block_center = (block_start + block_end) / 2
                            distance = abs(col_idx - block_center)
                            revenue_candidates.append((col_idx, distance, header_str))
                
                # Pick the closest revenue header
                if revenue_candidates:
                    revenue_candidates.sort(key=lambda x: x[1])  # Sort by distance
                    closest_revenue_col, distance, header_name = revenue_candidates[0]
                    block['revenue_col'] = closest_revenue_col
                    print(f"[REVENUE] Found revenue column '{header_name}' at column {closest_revenue_col} (distance: {distance:.1f} from block {block['start_year']}-{block['end_year']})")
        
        return [(block['start_year'], block['end_year'], block) for block in year_blocks]
    
    def _is_revenue_header(self, header_lower: str) -> bool:
        """
        Check if a header string indicates a revenue column.
        Matches: revenue, rev, annual revenue, yearly revenue (case-insensitive).
        """
        revenue_patterns = ['revenue', 'rev', 'annual revenue', 'yearly revenue']
        return any(pattern in header_lower for pattern in revenue_patterns)
    
    def _process_year_block(self, df_data: pd.DataFrame, start_year: int, end_year: int, 
                           block_info: Dict) -> pd.DataFrame:
        """
        Process a single year block: unpivot months and map revenue.
        """
        # Get metadata columns (State, City, Service_Provider)
        metadata_cols = {}
        for key, col_idx in block_info['metadata_cols'].items():
            if col_idx < len(df_data.columns):
                metadata_cols[key] = col_idx
        
        # Get month columns
        month_cols = [(col_idx, month_name) for col_idx, month_name in block_info['month_cols'] 
                     if col_idx < len(df_data.columns)]
        
        if not month_cols:
            return pd.DataFrame()
        
        # Get revenue column and validate it
        revenue_col = block_info['revenue_col']
        
        # Validate revenue column: check if it contains numeric values in first 50 rows
        if revenue_col is not None and revenue_col < len(df_data.columns):
            sample_rows = min(50, len(df_data))
            numeric_count = 0
            for row_idx in range(sample_rows):
                val = df_data.iloc[row_idx, revenue_col]
                if pd.notna(val):
                    numeric_val = pd.to_numeric(val, errors='coerce')
                    if pd.notna(numeric_val):
                        numeric_count += 1
            
            # If less than 10% of sample rows have numeric values, consider it invalid
            if numeric_count < (sample_rows * 0.1):
                print(f"[WARNING] Revenue column {revenue_col} for block {start_year}-{end_year} appears invalid: only {numeric_count}/{sample_rows} rows have numeric values")
                print(f"[WARNING] Setting revenue_col=None for this block")
                revenue_col = None
            else:
                print(f"[REVENUE] Validated revenue column {revenue_col} for block {start_year}-{end_year}: {numeric_count}/{sample_rows} rows have numeric values")
        elif revenue_col is not None:
            print(f"[WARNING] Revenue column {revenue_col} is out of bounds (max columns: {len(df_data.columns)}) for block {start_year}-{end_year}")
            revenue_col = None
        
        # Extract metadata for each row
        result_rows = []
        
        for row_idx in range(len(df_data)):
            # Get metadata values
            row_metadata = {}
            for key, col_idx in metadata_cols.items():
                if col_idx < len(df_data.columns):
                    val = df_data.iloc[row_idx, col_idx]
                    # Standardize key names
                    if key == 'service provider':
                        key = 'service_provider'
                    row_metadata[key] = val if pd.notna(val) else None
            
            # Get revenue value for this row (if revenue column exists)
            revenue_value = None
            if revenue_col is not None and revenue_col < len(df_data.columns):
                revenue_value = df_data.iloc[row_idx, revenue_col]
                if pd.notna(revenue_value):
                    revenue_value = pd.to_numeric(revenue_value, errors='coerce')
                else:
                    revenue_value = None
            
            # Process each month column
            for col_idx, month_name in month_cols:
                monthly_value = df_data.iloc[row_idx, col_idx]
                
                # Convert month name to standard format
                month_standard = self._normalize_month(month_name)
                month_num = self.MONTH_TO_NUM.get(month_standard, 1)
                
                # Determine which year this month belongs to
                # For year block 2026-2027: Jan-Jun -> 2026, Jul-Dec -> 2027
                # For year block 2027-2028: Jan-Jun -> 2027, Jul-Dec -> 2028
                # etc.
                if month_num <= 6:  # Jan-Jun -> start_year
                    year = start_year
                else:  # Jul-Dec -> end_year
                    year = end_year
                
                # Create row
                row = {
                    'State': row_metadata.get('state'),
                    'City': row_metadata.get('city'),
                    'Service_Provider': row_metadata.get('service_provider'),
                    'Year': year,
                    'Month': month_standard,
                    'Month_Num': month_num,
                    'Monthly_Value': pd.to_numeric(monthly_value, errors='coerce') if pd.notna(monthly_value) else None,
                    'Revenue': revenue_value
                }
                
                result_rows.append(row)
        
        return pd.DataFrame(result_rows)
    
    def _normalize_month(self, month_str: str) -> str:
        """Normalize month string to standard month name."""
        month_str = str(month_str).lower().strip()
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
    
    def _post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        """Post-process the long dataframe: ensure proper types and ordering."""
        if df.empty:
            return df
        
        # Ensure Year is integer (sortable)
        if 'Year' in df.columns:
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
        
        # Ensure Month_Num is integer
        if 'Month_Num' in df.columns:
            df['Month_Num'] = pd.to_numeric(df['Month_Num'], errors='coerce').astype('Int64')
        
        # Ensure Monthly_Value is numeric
        if 'Monthly_Value' in df.columns:
            df['Monthly_Value'] = pd.to_numeric(df['Monthly_Value'], errors='coerce')
        
        # Ensure Revenue is numeric
        if 'Revenue' in df.columns:
            df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
        
        # Sort by Year, then Month_Num
        if 'Year' in df.columns and 'Month_Num' in df.columns:
            df = df.sort_values(['Year', 'Month_Num'], ascending=[True, True]).reset_index(drop=True)
        
        # Select and reorder columns
        expected_cols = ['State', 'City', 'Service_Provider', 'Year', 'Month', 'Month_Num', 'Monthly_Value', 'Revenue']
        available_cols = [col for col in expected_cols if col in df.columns]
        df = df[available_cols].copy()
        
        return df
    
    def _validate_revenue_extraction(self, df: pd.DataFrame, df_headers: pd.DataFrame) -> None:
        """
        Post-validation: Check if revenue extraction failed.
        If total Revenue sum is 0 but Monthly_Value has non-null values, print WARNING.
        """
        if df.empty:
            return
        
        # Check if Revenue sum is 0 but Monthly_Value has non-null values
        if 'Revenue' in df.columns and 'Monthly_Value' in df.columns:
            total_revenue = df['Revenue'].sum()
            monthly_value_sum = df['Monthly_Value'].sum()
            monthly_value_count = df['Monthly_Value'].notna().sum()
            
            if total_revenue == 0 and monthly_value_count > 0 and monthly_value_sum > 0:
                print(f"\n[WARNING] ========================================")
                print(f"[WARNING] Revenue extraction may have failed!")
                print(f"[WARNING] Total Revenue sum: ${total_revenue:,.2f}")
                print(f"[WARNING] Monthly_Value sum: ${monthly_value_sum:,.2f} (from {monthly_value_count:,} non-null rows)")
                print(f"[WARNING] ========================================")
                
                # Show sample row metadata
                print(f"\n[WARNING] Sample rows with non-null Monthly_Value but zero/null Revenue:")
                sample_rows = df[df['Monthly_Value'].notna() & (df['Revenue'].isna() | (df['Revenue'] == 0))].head(10)
                if not sample_rows.empty:
                    for idx, row in sample_rows.iterrows():
                        print(f"  Row {idx}: State={row.get('State', 'N/A')}, City={row.get('City', 'N/A')}, "
                              f"Year={row.get('Year', 'N/A')}, Month={row.get('Month', 'N/A')}, "
                              f"Monthly_Value={row.get('Monthly_Value', 'N/A')}, Revenue={row.get('Revenue', 'N/A')}")
                
                # Show surrounding header values from original Excel
                if df_headers is not None and not df_headers.empty:
                    headers_row = df_headers.iloc[0].values
                    print(f"\n[WARNING] Surrounding header values from original Excel (first 50 columns):")
                    header_sample = []
                    for col_idx in range(min(50, len(headers_row))):
                        header_val = headers_row[col_idx] if col_idx < len(headers_row) else None
                        header_str = str(header_val) if pd.notna(header_val) else ""
                        if header_str.strip():
                            header_sample.append(f"Col{col_idx}: '{header_str}'")
                    if header_sample:
                        print(f"  {', '.join(header_sample[:20])}")  # Show first 20
                        if len(header_sample) > 20:
                            print(f"  ... and {len(header_sample) - 20} more headers")
                
                print(f"[WARNING] ========================================\n")
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate the transformed data."""
        if df.empty:
            print("WARNING: Transformed dataframe is empty!")
            return
        
        # Assert 5 years exist
        if 'Year' in df.columns:
            unique_years = sorted(df['Year'].dropna().unique())
            print(f"\n=== VALIDATION RESULTS ===")
            print(f"Unique years found: {unique_years}")
            print(f"Number of years: {len(unique_years)}")
            
            if len(unique_years) < 5:
                print(f"WARNING: Expected at least 5 years, found {len(unique_years)}")
            else:
                print(f"OK: All {len(unique_years)} years present")
            
            # Print total Revenue per Year
            print(f"\n=== REVENUE BY YEAR ===")
            if 'Revenue' in df.columns:
                revenue_by_year = df.groupby('Year')['Revenue'].agg(['sum', 'count']).reset_index()
                revenue_by_year.columns = ['Year', 'Total_Revenue', 'Row_Count']
                for _, row in revenue_by_year.iterrows():
                    print(f"Year {int(row['Year'])}: ${row['Total_Revenue']:,.0f} (from {int(row['Row_Count']):,} rows)")
            else:
                print("WARNING: Revenue column not found")
            
            # Print row counts
            print(f"\n=== ROW COUNTS ===")
            print(f"Total rows: {len(df):,}")
            if 'Year' in df.columns:
                year_counts = df['Year'].value_counts().sort_index()
                for year, count in year_counts.items():
                    print(f"Year {int(year)}: {count:,} rows")
        
        print(f"\n=== COLUMN SUMMARY ===")
        print(f"Columns: {list(df.columns)}")
        print(f"Shape: {df.shape}")
        print("=" * 50)


if __name__ == "__main__":
    # Test the loader
    loader = ServiceProvidersLoader()
    long_df = loader.load_and_transform()
    
    if not long_df.empty:
        print(f"\nSuccessfully transformed service_providers data")
        print(f"Sample rows:")
        print(long_df.head(10).to_string())
    else:
        print("Failed to transform data")
