"""
Metrics calculation module for Weelocal Economic Engine Dashboard.
Uses precomputed data for fast dictionary lookups - no groupby operations.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from precomputed_data import PrecomputedData


class MetricsCalculator:
    """Calculates all metrics using precomputed data for fast lookups."""
    
    def __init__(self, precomputed_data: PrecomputedData):
        self.precomputed = precomputed_data
        self._cached_cagr: Optional[float] = None
        self._cached_total_shops: Optional[float] = None
        self._cached_total_providers: Optional[float] = None
    
    def get_total_revenue(self, year: Optional[int] = None) -> float:
        """Get total revenue using precomputed data - O(1) lookup."""
        if year is None:
            # Sum all yearly totals
            return float(sum(self.precomputed.yearly_totals.values()))
        else:
            # Direct dictionary lookup
            return float(self.precomputed.yearly_totals.get(year, 0.0))
    
    def get_cagr(self, start_year: Optional[int] = None, end_year: Optional[int] = None, 
                 selected_years: Optional[List[int]] = None) -> Optional[float]:
        """
        Calculate CAGR using Total Revenue by Year.
        
        Formula: (End/Start)^(1/n) - 1 where n = number of year steps
        
        Args:
            start_year: Start year (if None, uses first available year)
            end_year: End year (if None, uses last available year)
            selected_years: List of selected years (if provided, uses first and last from this list)
        
        Returns:
            CAGR as percentage (float) or None if cannot be calculated (N/A cases)
        
        Edge Cases:
            - If start revenue is 0 or null → returns None (N/A)
            - If only one year selected → returns None (N/A)
            - If no years available → returns None (N/A)
        """
        # Get available years from data (sorted chronologically)
        available_years = sorted(self.precomputed.yearly_totals.keys())
        if not available_years:
            print("CAGR: No years available in data")
            return None
        
        # Determine start and end years
        if selected_years is not None and len(selected_years) > 0:
            # Use first and last from selected years
            selected_sorted = sorted([y for y in selected_years if y in available_years])
            if len(selected_sorted) < 2:
                print(f"CAGR: Only {len(selected_sorted)} year(s) selected, need at least 2 for CAGR")
                return None
            actual_start = selected_sorted[0]
            actual_end = selected_sorted[-1]
        else:
            # Use provided start/end or default to all available years
            if start_year is None:
                actual_start = available_years[0]
            else:
                actual_start = max(start_year, available_years[0])
            
            if end_year is None:
                actual_end = available_years[-1]
            else:
                actual_end = min(end_year, available_years[-1])
        
        # Validate we have at least 2 years
        if actual_start >= actual_end:
            print(f"CAGR: Start year ({actual_start}) >= End year ({actual_end}), need at least 2 years")
            return None
        
        # Get revenue values
        first_revenue = self.precomputed.yearly_totals.get(actual_start, 0)
        last_revenue = self.precomputed.yearly_totals.get(actual_end, 0)
        years = actual_end - actual_start
        
        # Edge case: Start revenue is 0 or null
        if first_revenue is None or first_revenue <= 0:
            print(f"CAGR: Start revenue ({actual_start}) is {first_revenue}, cannot calculate (insufficient baseline)")
            return None
        
        # Edge case: Last revenue is 0 or null
        if last_revenue is None or last_revenue <= 0:
            print(f"CAGR: End revenue ({actual_end}) is {last_revenue}, cannot calculate")
            return None
        
        # Calculate CAGR: (End/Start)^(1/n) - 1
        try:
            ratio = last_revenue / first_revenue
            if ratio <= 0:
                print(f"CAGR: Invalid ratio ({ratio}), cannot calculate")
                return None
            
            cagr = (ratio ** (1 / years) - 1) * 100
            cagr = float(cagr)
            
            # Log calculation for verification
            print(f"CAGR Calculation:")
            print(f"  Start Year: {actual_start}, Revenue: ${first_revenue:,.0f}")
            print(f"  End Year: {actual_end}, Revenue: ${last_revenue:,.0f}")
            print(f"  Years: {years}")
            print(f"  Ratio: {ratio:.4f}")
            print(f"  CAGR: {cagr:.2f}%")
            
            return cagr
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            print(f"CAGR: Calculation error: {e}")
            return None
    
    def get_total_shops(self, year: Optional[int] = None) -> float:
        """Get total number of shops - cached."""
        if self._cached_total_shops is not None:
            return self._cached_total_shops
        
        if self.precomputed.city_metrics.empty:
            return 0.0
        
        shop_cols = [col for col in self.precomputed.city_metrics.columns 
                    if 'shop' in col.lower() and any(x in col.lower() for x in ['number', 'count', 'total'])]
        
        if not shop_cols:
            return 0.0
        
        shop_col = shop_cols[0]
        total = pd.to_numeric(self.precomputed.city_metrics[shop_col], errors='coerce').sum()
        self._cached_total_shops = float(total) if pd.notna(total) else 0.0
        return self._cached_total_shops
    
    def get_total_service_providers(self, year: Optional[int] = None) -> float:
        """Get total number of service providers - cached."""
        if self._cached_total_providers is not None:
            return self._cached_total_providers
        
        if self.precomputed.city_metrics.empty:
            return 0.0
        
        provider_cols = [col for col in self.precomputed.city_metrics.columns 
                        if 'provider' in col.lower() and any(x in col.lower() for x in ['number', 'count', 'total'])]
        
        if not provider_cols:
            return 0.0
        
        provider_col = provider_cols[0]
        total = pd.to_numeric(self.precomputed.city_metrics[provider_col], errors='coerce').sum()
        self._cached_total_providers = float(total) if pd.notna(total) else 0.0
        return self._cached_total_providers
    
    def get_revenue_per_shop(self, year: Optional[int] = None) -> float:
        """
        Calculate revenue per shop.
        
        Note: Uses all-years shop totals (shops/providers counts are totals across the whole dataset).
        If year is specified, uses revenue for that year but still divides by all-years shop total.
        This represents "All-years revenue per shop" when year=None, or "Year-specific revenue per shop (using all-years shop count)" when year is specified.
        """
        total_revenue = self.get_total_revenue(year)
        
        # Use global totals from precomputed data (all-years aggregates)
        # Note: city_metrics contains totals across all years, not year-specific counts
        total_shops = self.precomputed.total_shops if hasattr(self.precomputed, 'total_shops') else self.get_total_shops(year)
        
        if total_shops > 0:
            return total_revenue / total_shops
        return 0.0
    
    def get_revenue_per_service_provider(self, year: Optional[int] = None) -> float:
        """
        Calculate revenue per service provider.
        
        Note: Uses all-years provider totals (shops/providers counts are totals across the whole dataset).
        If year is specified, uses revenue for that year but still divides by all-years provider total.
        This represents "All-years revenue per provider" when year=None, or "Year-specific revenue per provider (using all-years provider count)" when year is specified.
        """
        total_revenue = self.get_total_revenue(year)
        
        # Use global totals from precomputed data (all-years aggregates)
        # Note: city_metrics contains totals across all years, not year-specific counts
        total_providers = self.precomputed.total_providers if hasattr(self.precomputed, 'total_providers') else self.get_total_service_providers(year)
        
        if total_providers > 0:
            return total_revenue / total_providers
        return 0.0
    
    def get_revenue_trend(self, start_year: int = 2026, end_year: int = 2031) -> pd.DataFrame:
        """Get revenue trend using precomputed data - O(n) where n = years."""
        return self.precomputed.get_revenue_trend(start_year, end_year)
    
    def get_revenue_by_category(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get revenue by category using precomputed data - O(1) lookup."""
        return self.precomputed.get_revenue_by_category(year)
    
    def get_revenue_by_state(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get revenue by state using precomputed data - O(1) lookup."""
        return self.precomputed.get_revenue_by_state(year)
    
    def get_revenue_per_shop_by_state(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get revenue per shop by state using precomputed data - O(1) lookup."""
        return self.precomputed.get_revenue_per_shop_by_state(year)
    
    def get_revenue_per_provider_by_state(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get revenue per provider by state using precomputed data - O(1) lookup."""
        return self.precomputed.get_revenue_per_provider_by_state(year)
    
    def get_ecosystem_size_vs_revenue(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get ecosystem size vs revenue using precomputed data - O(n) where n = cities."""
        return self.precomputed.get_ecosystem_size_vs_revenue(year)
    
    def get_top_cities_by_revenue(self, top_n: int = 10, year: Optional[int] = None) -> pd.DataFrame:
        """Get top cities using precomputed data - O(1) lookup."""
        return self.precomputed.get_top_cities(top_n, year)
    
    def get_pareto_data(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get Pareto data using precomputed data - O(1) lookup."""
        return self.precomputed.get_pareto_data(year)
