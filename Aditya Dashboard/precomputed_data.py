"""
Precomputed data module for Weelocal Economic Engine Dashboard.
Pre-aggregates all data for fast lookups and minimal reactivity.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class PrecomputedData:
    """Stores all pre-aggregated data for fast lookups."""
    
    def __init__(self, master_df: pd.DataFrame, city_metrics: pd.DataFrame):
        self.master_df = master_df
        self.city_metrics = city_metrics
        
        # Pre-aggregated yearly totals
        self.yearly_totals: Dict[int, float] = {}
        self.yearly_by_category: Dict[Tuple[int, str], float] = {}
        self.yearly_by_state: Dict[Tuple[int, str], float] = {}
        self.yearly_by_city: Dict[Tuple[int, str, str], float] = {}
        
        # Pre-aggregated category totals
        self.category_totals: Dict[str, float] = {}
        self.category_by_year: Dict[Tuple[str, int], float] = {}
        
        # Pre-aggregated state totals
        self.state_totals: Dict[str, float] = {}
        self.state_by_year: Dict[Tuple[str, int], float] = {}
        
        # Pre-aggregated city totals
        self.city_totals: Dict[Tuple[str, str], float] = {}  # (state, city) -> revenue
        self.city_by_year: Dict[Tuple[str, str, int], float] = {}  # (state, city, year) -> revenue
        
        # Precomputed efficiency metrics (with underlying totals)
        self.revenue_per_shop_by_state: Dict[str, float] = {}
        self.revenue_per_provider_by_state: Dict[str, float] = {}
        self.state_revenue_totals: Dict[str, float] = {}  # State -> Total Revenue
        self.state_shop_totals: Dict[str, float] = {}  # State -> Total Shops
        self.state_provider_totals: Dict[str, float] = {}  # State -> Total Providers
        
        # Global totals (all-years aggregates)
        self.total_shops: float = 0.0
        self.total_providers: float = 0.0
        self.ecosystem_size_by_city: Dict[Tuple[str, str], float] = {}
        
        # Precomputed top cities
        self.top_cities_all_time: List[Tuple[str, str, float]] = []  # (state, city, revenue)
        self.top_cities_by_year: Dict[int, List[Tuple[str, str, float]]] = {}
        
        # Precomputed Pareto data
        self.pareto_data: Dict[int, pd.DataFrame] = {}
        
        # Precompute everything
        self._precompute_all()
    
    def _precompute_all(self):
        """Precompute all aggregations."""
        if self.master_df.empty:
            return
        
        # Precompute yearly totals
        self._precompute_yearly_totals()
        
        # Precompute category aggregations
        self._precompute_category_data()
        
        # Precompute state aggregations
        self._precompute_state_data()
        
        # Precompute city aggregations
        self._precompute_city_data()
        
        # Precompute efficiency metrics
        self._precompute_efficiency_metrics()
        
        # Precompute top cities
        self._precompute_top_cities()
        
        # Precompute Pareto data
        self._precompute_pareto()
    
    def _precompute_yearly_totals(self):
        """Precompute total revenue by year."""
        if 'year' not in self.master_df.columns or 'revenue' not in self.master_df.columns:
            return
        
        # Aggregate monthly data to yearly
        yearly_agg = self.master_df.groupby('year')['revenue'].sum()
        self.yearly_totals = yearly_agg.to_dict()
        
        # Optional validation: Ensure yearly_totals is consistent
        # (This is a sanity check - main validation happens in export_data.py)
        if self.yearly_totals:
            total_sum = sum(self.yearly_totals.values())
            # Verify all values are numeric and non-negative
            for year, revenue in self.yearly_totals.items():
                if pd.isna(revenue) or revenue < 0:
                    print(f"[WARNING] Yearly total for {year} is invalid: {revenue}")
        
        # Precompute by category and year
        if 'category' in self.master_df.columns:
            category_year_agg = self.master_df.groupby(['category', 'year'])['revenue'].sum()
            for (category, year), revenue in category_year_agg.items():
                self.yearly_by_category[(year, category)] = float(revenue)
        
        # Precompute by state and year
        if 'state' in self.master_df.columns:
            state_year_agg = self.master_df.groupby(['state', 'year'])['revenue'].sum()
            for (state, year), revenue in state_year_agg.items():
                self.yearly_by_state[(year, state)] = float(revenue)
        
        # Precompute by city and year
        if 'city' in self.master_df.columns and 'state' in self.master_df.columns:
            city_year_agg = self.master_df.groupby(['state', 'city', 'year'])['revenue'].sum()
            for (state, city, year), revenue in city_year_agg.items():
                self.yearly_by_city[(year, state, city)] = float(revenue)
    
    def _precompute_category_data(self):
        """Precompute category aggregations."""
        if 'category' not in self.master_df.columns or 'revenue' not in self.master_df.columns:
            return
        
        # Total by category
        category_agg = self.master_df.groupby('category')['revenue'].sum()
        self.category_totals = category_agg.to_dict()
        
        # By category and year
        if 'year' in self.master_df.columns:
            category_year_agg = self.master_df.groupby(['category', 'year'])['revenue'].sum()
            for (category, year), revenue in category_year_agg.items():
                self.category_by_year[(category, year)] = float(revenue)
    
    def _precompute_state_data(self):
        """Precompute state aggregations."""
        if 'state' not in self.master_df.columns or 'revenue' not in self.master_df.columns:
            return
        
        # Total by state
        state_agg = self.master_df.groupby('state')['revenue'].sum()
        self.state_totals = state_agg.to_dict()
        
        # By state and year
        if 'year' in self.master_df.columns:
            state_year_agg = self.master_df.groupby(['state', 'year'])['revenue'].sum()
            for (state, year), revenue in state_year_agg.items():
                self.state_by_year[(state, year)] = float(revenue)
    
    def _precompute_city_data(self):
        """Precompute city aggregations."""
        if 'city' not in self.master_df.columns or 'state' not in self.master_df.columns:
            return
        
        if 'revenue' not in self.master_df.columns:
            return
        
        # Total by city (state, city)
        city_agg = self.master_df.groupby(['state', 'city'])['revenue'].sum()
        for (state, city), revenue in city_agg.items():
            self.city_totals[(state, city)] = float(revenue)
        
        # By city and year
        if 'year' in self.master_df.columns:
            city_year_agg = self.master_df.groupby(['state', 'city', 'year'])['revenue'].sum()
            for (state, city, year), revenue in city_year_agg.items():
                self.city_by_year[(state, city, year)] = float(revenue)
    
    def _precompute_efficiency_metrics(self):
        """Precompute efficiency metrics by state using vectorized operations."""
        if self.city_metrics.empty or self.master_df.empty:
            return
        
        # Get shop and provider columns - try multiple naming patterns
        shop_cols = [col for col in self.city_metrics.columns 
                    if 'shop' in col.lower()]
        provider_cols = [col for col in self.city_metrics.columns 
                        if 'provider' in col.lower()]
        
        # If no matches, try simpler patterns
        if not shop_cols:
            shop_cols = [col for col in self.city_metrics.columns if 'number_of_shops' in col.lower()]
        if not provider_cols:
            provider_cols = [col for col in self.city_metrics.columns if 'number_of_service_providers' in col.lower() or 'service_provider' in col.lower()]
        
        if not shop_cols or not provider_cols:
            return  # Silently skip if columns not found
        
        shop_col = shop_cols[0]
        provider_col = provider_cols[0]
        
        # Aggregate revenue by state (vectorized)
        if 'state' not in self.master_df.columns or 'revenue' not in self.master_df.columns:
            return
        if 'state' not in self.city_metrics.columns:
            return
            
        try:
            state_revenue = self.master_df.groupby('state')['revenue'].sum()
            
            # Aggregate shops and providers by state (vectorized)
            state_shops = pd.to_numeric(self.city_metrics.groupby('state')[shop_col].sum(), errors='coerce').fillna(0)
            state_providers = pd.to_numeric(self.city_metrics.groupby('state')[provider_col].sum(), errors='coerce').fillna(0)
            
            # Store global totals (all-years aggregates)
            self.total_shops = float(pd.to_numeric(self.city_metrics[shop_col], errors='coerce').sum())
            self.total_providers = float(pd.to_numeric(self.city_metrics[provider_col], errors='coerce').sum())
            
            print(f"[EFFICIENCY] Global totals computed: {self.total_shops:,.0f} shops, {self.total_providers:,.0f} providers (all-years aggregates)")
            
            # Vectorized calculation for efficiency metrics
            for state in state_revenue.index:
                revenue = float(state_revenue[state])
                self.state_revenue_totals[state] = revenue
                
                shops = float(state_shops.get(state, 0))
                providers = float(state_providers.get(state, 0))
                
                self.state_shop_totals[state] = shops
                self.state_provider_totals[state] = providers
                
                # Calculate efficiency metrics (handle division by zero)
                self.revenue_per_shop_by_state[state] = float(revenue / shops) if shops > 0 else None
                self.revenue_per_provider_by_state[state] = float(revenue / providers) if providers > 0 else None
        except Exception as e:
            print(f"Warning: Error computing efficiency metrics: {e}")
            # Continue without efficiency metrics rather than failing
        
        # Precompute ecosystem size by city
        if 'city' in self.city_metrics.columns and 'state' in self.city_metrics.columns:
            city_metrics_subset = self.city_metrics[['state', 'city', shop_col, provider_col]].copy()
            city_metrics_subset[shop_col] = pd.to_numeric(city_metrics_subset[shop_col], errors='coerce').fillna(0)
            city_metrics_subset[provider_col] = pd.to_numeric(city_metrics_subset[provider_col], errors='coerce').fillna(0)
            city_metrics_subset['ecosystem_size'] = city_metrics_subset[shop_col] + city_metrics_subset[provider_col]
            
            for _, row in city_metrics_subset.iterrows():
                self.ecosystem_size_by_city[(row['state'], row['city'])] = float(row['ecosystem_size'])
    
    def _precompute_top_cities(self):
        """Precompute top cities rankings."""
        # All-time top cities
        sorted_cities = sorted(self.city_totals.items(), key=lambda x: x[1], reverse=True)
        self.top_cities_all_time = [(state, city, revenue) for ((state, city), revenue) in sorted_cities]
        
        # Top cities by year
        if 'year' in self.master_df.columns:
            years = sorted(self.master_df['year'].unique())
            for year in years:
                year_cities = [(state, city, revenue) 
                              for ((y, state, city), revenue) in self.yearly_by_city.items() 
                              if y == year]
                year_cities.sort(key=lambda x: x[2], reverse=True)
                self.top_cities_by_year[year] = year_cities
    
    def _precompute_pareto(self):
        """Precompute Pareto chart data by year."""
        if 'year' not in self.master_df.columns:
            return
        
        years = sorted(self.master_df['year'].unique())
        
        for year in years:
            # Get cities for this year
            year_cities = [(state, city, revenue) 
                          for ((y, state, city), revenue) in self.yearly_by_city.items() 
                          if y == year]
            
            if not year_cities:
                continue
            
            # Sort by revenue
            year_cities.sort(key=lambda x: x[2], reverse=True)
            
            # Calculate cumulative
            total_revenue = sum(revenue for _, _, revenue in year_cities)
            cumulative = 0
            pareto_rows = []
            
            for i, (state, city, revenue) in enumerate(year_cities):
                cumulative += revenue
                cumulative_pct = (cumulative / total_revenue * 100) if total_revenue > 0 else 0
                city_pct = ((i + 1) / len(year_cities) * 100) if year_cities else 0
                
                pareto_rows.append({
                    'State': state,
                    'City': city,
                    'Revenue': revenue,
                    'Cumulative_Percentage': cumulative_pct,
                    'City_Percentage': city_pct
                })
            
            self.pareto_data[year] = pd.DataFrame(pareto_rows)
        
        # Also compute for all years combined
        all_cities = sorted(self.city_totals.items(), key=lambda x: x[1], reverse=True)
        total_revenue = sum(revenue for _, revenue in all_cities)
        cumulative = 0
        pareto_rows = []
        
        for i, ((state, city), revenue) in enumerate(all_cities):
            cumulative += revenue
            cumulative_pct = (cumulative / total_revenue * 100) if total_revenue > 0 else 0
            city_pct = ((i + 1) / len(all_cities) * 100) if all_cities else 0
            
            pareto_rows.append({
                'State': state,
                'City': city,
                'Revenue': revenue,
                'Cumulative_Percentage': cumulative_pct,
                'City_Percentage': city_pct
            })
        
        self.pareto_data[None] = pd.DataFrame(pareto_rows)
    
    def get_revenue_trend(self, start_year: int = 2026, end_year: int = 2031) -> pd.DataFrame:
        """Get revenue trend using precomputed data."""
        trend_data = []
        available_years = sorted(self.yearly_totals.keys())
        
        if not available_years:
            return pd.DataFrame(columns=['Year', 'Revenue'])
        
        # Use actual available years (ensure integers)
        actual_start = int(max(start_year, available_years[0]))
        actual_end = int(min(end_year, available_years[-1]))
        
        for year in range(actual_start, actual_end + 1):
            if year in self.yearly_totals:
                trend_data.append({'Year': year, 'Revenue': self.yearly_totals[year]})
        
        return pd.DataFrame(trend_data)
    
    def get_revenue_by_category(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get revenue by category using precomputed data."""
        if year is None:
            # Use total category totals
            data = [{'Category': cat, 'Revenue': rev} for cat, rev in self.category_totals.items()]
        else:
            # Use year-specific data
            data = [{'Category': cat, 'Revenue': rev} 
                   for (cat, y), rev in self.category_by_year.items() 
                   if y == year]
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('Revenue', ascending=False)
        return df
    
    def get_revenue_by_state(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get revenue by state using precomputed data."""
        if year is None:
            data = [{'State': state, 'Revenue': rev} for state, rev in self.state_totals.items()]
        else:
            data = [{'State': state, 'Revenue': rev} 
                   for (state, y), rev in self.state_by_year.items() 
                   if y == year]
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('Revenue', ascending=False)
        return df
    
    def get_revenue_per_shop_by_state(self, year: Optional[int] = None, top_n: Optional[int] = None) -> pd.DataFrame:
        """
        Get revenue per shop by state with underlying totals.
        Returns DataFrame with: State, Revenue_per_Shop, Total_Revenue, Total_Shops
        """
        data = []
        for state in self.revenue_per_shop_by_state.keys():
            rev_per_shop = self.revenue_per_shop_by_state[state]
            total_revenue = self.state_revenue_totals.get(state, 0)
            total_shops = self.state_shop_totals.get(state, 0)
            
            data.append({
                'State': state,
                'Revenue_per_Shop': rev_per_shop if rev_per_shop is not None else None,
                'Total_Revenue': total_revenue,
                'Total_Shops': total_shops
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            # Sort by Revenue_per_Shop descending (None values go to end)
            df = df.sort_values('Revenue_per_Shop', ascending=False, na_position='last')
            if top_n is not None:
                df = df.head(top_n)
        return df
    
    def get_revenue_per_provider_by_state(self, year: Optional[int] = None, top_n: Optional[int] = None) -> pd.DataFrame:
        """
        Get revenue per provider by state with underlying totals.
        Returns DataFrame with: State, Revenue_per_Provider, Total_Revenue, Total_Providers
        """
        data = []
        for state in self.revenue_per_provider_by_state.keys():
            rev_per_provider = self.revenue_per_provider_by_state[state]
            total_revenue = self.state_revenue_totals.get(state, 0)
            total_providers = self.state_provider_totals.get(state, 0)
            
            data.append({
                'State': state,
                'Revenue_per_Provider': rev_per_provider if rev_per_provider is not None else None,
                'Total_Revenue': total_revenue,
                'Total_Providers': total_providers
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            # Sort by Revenue_per_Provider descending (None values go to end)
            df = df.sort_values('Revenue_per_Provider', ascending=False, na_position='last')
            if top_n is not None:
                df = df.head(top_n)
        return df
    
    def get_top_cities(self, top_n: int = 10, year: Optional[int] = None) -> pd.DataFrame:
        """Get top cities using precomputed data."""
        if year is None:
            cities = self.top_cities_all_time[:top_n]
        else:
            cities = self.top_cities_by_year.get(year, [])[:top_n]
        
        data = [{'State': state, 'City': city, 'Revenue': revenue} 
               for state, city, revenue in cities]
        return pd.DataFrame(data)
    
    def get_top_cities_pareto(self, top_n: int = 15, year: Optional[int] = None) -> pd.DataFrame:
        """
        Get top cities with cumulative percentage for Pareto analysis.
        Returns DataFrame with: State, City, Revenue, Cumulative_Revenue, Cumulative_Percentage, Total_Revenue
        
        Args:
            top_n: Number of top cities to return (default 15)
            year: Optional year filter (None = all years)
        
        Returns:
            DataFrame sorted by revenue descending with cumulative percentages
        """
        # Get all cities for the year
        if year is None:
            all_cities = self.top_cities_all_time.copy()
        else:
            all_cities = self.top_cities_by_year.get(year, []).copy()
        
        if not all_cities:
            return pd.DataFrame(columns=['State', 'City', 'Revenue', 'Cumulative_Revenue', 'Cumulative_Percentage', 'Total_Revenue'])
        
        # Sort by revenue descending
        all_cities.sort(key=lambda x: x[2], reverse=True)
        
        # Calculate total revenue (from ALL cities, not just top N)
        total_revenue = sum(revenue for _, _, revenue in all_cities)
        
        if total_revenue == 0:
            return pd.DataFrame(columns=['State', 'City', 'Revenue', 'Cumulative_Revenue', 'Cumulative_Percentage', 'Total_Revenue'])
        
        # Take top N and calculate cumulative
        top_cities = all_cities[:top_n]
        cumulative = 0
        result_data = []
        
        for state, city, revenue in top_cities:
            cumulative += revenue
            cumulative_pct = (cumulative / total_revenue) * 100
            
            result_data.append({
                'State': state,
                'City': city,
                'Revenue': revenue,
                'Cumulative_Revenue': cumulative,
                'Cumulative_Percentage': cumulative_pct,
                'Total_Revenue': total_revenue  # Include total for reference
            })
        
        return pd.DataFrame(result_data)
    
    def get_pareto_data(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get Pareto data using precomputed data."""
        return self.pareto_data.get(year, pd.DataFrame())
    
    def get_ecosystem_size_vs_revenue(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get ecosystem size vs revenue using precomputed data."""
        data = []
        for (state, city), ecosystem_size in self.ecosystem_size_by_city.items():
            revenue = self.city_totals.get((state, city), 0)
            if year is not None:
                revenue = self.city_by_year.get((state, city, year), 0)
            
            if revenue > 0 and ecosystem_size > 0:
                data.append({
                    'State': state,
                    'City': city,
                    'Revenue': revenue,
                    'Ecosystem_Size': ecosystem_size
                })
        
        return pd.DataFrame(data)
    
    def get_global_efficiency(self) -> Dict[str, float]:
        """
        Get global (all-years) efficiency metrics.
        
        Returns:
            Dictionary with 'revenue_per_shop' and 'revenue_per_provider' using all-years totals.
            Note: Shops/providers counts are totals across the whole dataset (not year-specific).
        """
        total_revenue = sum(self.yearly_totals.values())
        
        result = {}
        
        if self.total_shops > 0:
            result['revenue_per_shop'] = float(total_revenue / self.total_shops)
        else:
            result['revenue_per_shop'] = None
        
        if self.total_providers > 0:
            result['revenue_per_provider'] = float(total_revenue / self.total_providers)
        else:
            result['revenue_per_provider'] = None
        
        return result
    
    def get_yearly_aggregated_df(self) -> pd.DataFrame:
        """Get yearly aggregated dataframe for insights generator."""
        data = []
        for year, revenue in self.yearly_totals.items():
            data.append({'year': year, 'yearly_revenue': revenue})
        if not data:
            return pd.DataFrame(columns=['year', 'yearly_revenue'])
        df = pd.DataFrame(data)
        if 'year' in df.columns:
            return df.sort_values('year')
        return df
