"""
Insights and projections module for Weelocal Economic Engine Dashboard.
Generates automated insights, forecasts, and valuation metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')


class InsightsGenerator:
    """Generates automated insights and projections."""
    
    def __init__(self, yearly_df: pd.DataFrame, city_metrics: pd.DataFrame):
        self.yearly_df = yearly_df
        self.city_metrics = city_metrics
        self._cached_insights: Optional[Dict] = None
        self._cached_projections: Optional[pd.DataFrame] = None
        self._cached_valuation: Optional[Dict] = None
    
    def get_yoy_growth(self) -> Dict[str, float]:
        """Calculate year-over-year growth percentages."""
        if self.yearly_df.empty or 'year' not in self.yearly_df.columns:
            return {}
        
        # Aggregate revenue by year
        yearly_revenue = self.yearly_df.groupby('year')['yearly_revenue'].sum().sort_index()
        
        if len(yearly_revenue) < 2:
            return {}
        
        growth_dict = {}
        years = sorted(yearly_revenue.index)
        
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            prev_revenue = yearly_revenue[prev_year]
            curr_revenue = yearly_revenue[curr_year]
            
            if prev_revenue > 0:
                growth_pct = ((curr_revenue / prev_revenue) - 1) * 100
                growth_dict[f"{prev_year}-{curr_year}"] = float(growth_pct)
        
        return growth_dict
    
    def get_revenue_acceleration_rate(self) -> float:
        """Calculate revenue acceleration rate (change in growth rate)."""
        if self.yearly_df.empty or 'year' not in self.yearly_df.columns:
            return 0.0
        
        yearly_revenue = self.yearly_df.groupby('year')['yearly_revenue'].sum().sort_index()
        
        if len(yearly_revenue) < 3:
            return 0.0
        
        # Calculate growth rates
        growth_rates = []
        years = sorted(yearly_revenue.index)
        
        for i in range(1, len(years)):
            prev_revenue = yearly_revenue[years[i-1]]
            curr_revenue = yearly_revenue[years[i]]
            
            if prev_revenue > 0:
                growth_rate = ((curr_revenue / prev_revenue) - 1) * 100
                growth_rates.append(growth_rate)
        
        if len(growth_rates) < 2:
            return 0.0
        
        # Acceleration is the change in growth rate
        acceleration = growth_rates[-1] - growth_rates[-2]
        return float(acceleration)
    
    def get_efficiency_improvements(self) -> Dict[str, float]:
        """Calculate efficiency improvements over time."""
        if self.yearly_df.empty or self.city_metrics.empty:
            return {}
        
        # Get shop and provider columns
        shop_cols = [col for col in self.city_metrics.columns 
                    if 'shop' in col.lower() and any(x in col.lower() for x in ['number', 'count', 'total'])]
        provider_cols = [col for col in self.city_metrics.columns 
                        if 'provider' in col.lower() and any(x in col.lower() for x in ['number', 'count', 'total'])]
        
        if not shop_cols or not provider_cols:
            return {}
        
        shop_col = shop_cols[0]
        provider_col = provider_cols[0]
        
        # Calculate revenue per shop and per provider by year
        efficiency_data = []
        
        for year in sorted(self.yearly_df['year'].unique()):
            year_data = self.yearly_df[self.yearly_df['year'] == year]
            year_revenue = year_data['yearly_revenue'].sum()
            
            # Get total shops and providers (assuming they're constant or we aggregate)
            total_shops = pd.to_numeric(self.city_metrics[shop_col], errors='coerce').sum()
            total_providers = pd.to_numeric(self.city_metrics[provider_col], errors='coerce').sum()
            
            if total_shops > 0:
                revenue_per_shop = year_revenue / total_shops
                efficiency_data.append({
                    'year': year,
                    'revenue_per_shop': revenue_per_shop
                })
            
            if total_providers > 0:
                revenue_per_provider = year_revenue / total_providers
                if any(d['year'] == year for d in efficiency_data):
                    idx = next(i for i, d in enumerate(efficiency_data) if d['year'] == year)
                    efficiency_data[idx]['revenue_per_provider'] = revenue_per_provider
                else:
                    efficiency_data.append({
                        'year': year,
                        'revenue_per_provider': revenue_per_provider
                    })
        
        if len(efficiency_data) < 2:
            return {}
        
        efficiency_df = pd.DataFrame(efficiency_data).sort_values('year')
        
        improvements = {}
        
        # Calculate improvement in revenue per shop
        if 'revenue_per_shop' in efficiency_df.columns:
            first_shop = efficiency_df.iloc[0]['revenue_per_shop']
            last_shop = efficiency_df.iloc[-1]['revenue_per_shop']
            if first_shop > 0:
                shop_improvement = ((last_shop / first_shop) - 1) * 100
                improvements['revenue_per_shop'] = float(shop_improvement)
        
        # Calculate improvement in revenue per provider
        if 'revenue_per_provider' in efficiency_df.columns:
            first_provider = efficiency_df.iloc[0]['revenue_per_provider']
            last_provider = efficiency_df.iloc[-1]['revenue_per_provider']
            if first_provider > 0:
                provider_improvement = ((last_provider / first_provider) - 1) * 100
                improvements['revenue_per_provider'] = float(provider_improvement)
        
        return improvements
    
    def get_network_density_trends(self) -> Dict[str, float]:
        """Calculate network density trends (shops + providers per city)."""
        if self.city_metrics.empty:
            return {}
        
        shop_cols = [col for col in self.city_metrics.columns 
                    if 'shop' in col.lower() and any(x in col.lower() for x in ['number', 'count', 'total'])]
        provider_cols = [col for col in self.city_metrics.columns 
                        if 'provider' in col.lower() and any(x in col.lower() for x in ['number', 'count', 'total'])]
        
        if not shop_cols or not provider_cols:
            return {}
        
        shop_col = shop_cols[0]
        provider_col = provider_cols[0]
        
        # Calculate density metrics
        if 'city' in self.city_metrics.columns:
            city_count = self.city_metrics['city'].nunique()
            total_shops = pd.to_numeric(self.city_metrics[shop_col], errors='coerce').sum()
            total_providers = pd.to_numeric(self.city_metrics[provider_col], errors='coerce').sum()
            
            if city_count > 0:
                shops_per_city = total_shops / city_count
                providers_per_city = total_providers / city_count
                total_ecosystem_per_city = shops_per_city + providers_per_city
                
                return {
                    'shops_per_city': float(shops_per_city),
                    'providers_per_city': float(providers_per_city),
                    'ecosystem_per_city': float(total_ecosystem_per_city),
                    'total_cities': int(city_count)
                }
        
        return {}
    
    def get_all_insights(self) -> Dict:
        """Get all insights with caching."""
        if self._cached_insights is not None:
            return self._cached_insights
        
        insights = {
            'yoy_growth': self.get_yoy_growth(),
            'revenue_acceleration': self.get_revenue_acceleration_rate(),
            'efficiency_improvements': self.get_efficiency_improvements(),
            'network_density': self.get_network_density_trends()
        }
        
        self._cached_insights = insights
        return insights
    
    def get_projection(self, forecast_years: List[int] = [2032, 2033, 2034]) -> pd.DataFrame:
        """
        Generate linear regression forecast for future years.
        
        Args:
            forecast_years: List of years to forecast
            
        Returns:
            DataFrame with historical and projected data
        """
        if self._cached_projections is not None:
            return self._cached_projections
        
        if self.yearly_df.empty or 'year' not in self.yearly_df.columns:
            return pd.DataFrame()
        
        try:
            # Aggregate revenue by year
            yearly_revenue = self.yearly_df.groupby('year')['yearly_revenue'].sum().sort_index()
            
            if len(yearly_revenue) < 2:
                return pd.DataFrame()
            
            # Prepare data for regression
            X = np.array(yearly_revenue.index).reshape(-1, 1)
            y = yearly_revenue.values
            
            # Validate data
            if len(X) != len(y) or len(X) == 0:
                return pd.DataFrame()
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate projections
            projection_data = []
            
            # Include historical data
            for year in yearly_revenue.index:
                try:
                    projection_data.append({
                        'Year': int(year),
                        'Revenue': float(yearly_revenue[year]),
                        'Type': 'Historical'
                    })
                except (ValueError, TypeError) as e:
                    print(f"Warning: Error processing historical year {year}: {e}")
                    continue
            
            # Generate forecasts
            for year in forecast_years:
                try:
                    predicted_revenue = model.predict([[year]])[0]
                    # Ensure non-negative predictions
                    predicted_revenue = max(0, float(predicted_revenue))
                    projection_data.append({
                        'Year': int(year),
                        'Revenue': predicted_revenue,
                        'Type': 'Projected'
                    })
                except (ValueError, TypeError) as e:
                    print(f"Warning: Error forecasting year {year}: {e}")
                    continue
            
            if not projection_data:
                return pd.DataFrame()
            
            projections_df = pd.DataFrame(projection_data)
            self._cached_projections = projections_df
            return projections_df
        except Exception as e:
            print(f"Error generating projections: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_valuation(self, revenue_multiples: List[float] = [3.0, 5.0, 8.0]) -> Dict:
        """
        Calculate implied valuation using revenue multiples.
        
        Args:
            revenue_multiples: List of revenue multiples to apply
            
        Returns:
            Dictionary with valuation data
        """
        if self._cached_valuation is not None:
            return self._cached_valuation
        
        if self.yearly_df.empty or 'year' not in self.yearly_df.columns:
            return {}
        
        try:
            # Get latest year revenue
            yearly_revenue = self.yearly_df.groupby('year')['yearly_revenue'].sum().sort_index()
            
            if yearly_revenue.empty:
                return {}
            
            latest_year = yearly_revenue.index.max()
            latest_revenue = yearly_revenue[latest_year]
            
            # Validate revenue
            if pd.isna(latest_revenue) or latest_revenue <= 0:
                return {}
            
            # Calculate valuations
            valuations = {}
            for multiple in revenue_multiples:
                try:
                    if multiple <= 0:
                        continue
                    implied_valuation = latest_revenue * multiple
                    valuations[f"{multiple}x"] = {
                        'multiple': float(multiple),
                        'revenue': float(latest_revenue),
                        'valuation': float(implied_valuation)
                    }
                except (ValueError, TypeError) as e:
                    print(f"Warning: Error calculating valuation for {multiple}x: {e}")
                    continue
            
            # Get projected revenue for 2034 (if available)
            projections = self.get_projection()
            if not projections.empty:
                projected_2034 = projections[projections['Year'] == 2034]
                if not projected_2034.empty:
                    projected_revenue = projected_2034.iloc[0]['Revenue']
                    if pd.notna(projected_revenue) and projected_revenue > 0:
                        projected_valuations = {}
                        for multiple in revenue_multiples:
                            try:
                                if multiple <= 0:
                                    continue
                                implied_valuation = projected_revenue * multiple
                                projected_valuations[f"{multiple}x"] = {
                                    'multiple': float(multiple),
                                    'revenue': float(projected_revenue),
                                    'valuation': float(implied_valuation)
                                }
                            except (ValueError, TypeError) as e:
                                print(f"Warning: Error calculating projected valuation for {multiple}x: {e}")
                                continue
                        if projected_valuations:
                            valuations['projected_2034'] = projected_valuations
            
            result = {
                'latest_year': int(latest_year),
                'latest_revenue': float(latest_revenue),
                'current_valuations': valuations
            }
            
            self._cached_valuation = result
            return result
        except Exception as e:
            print(f"Error calculating valuation: {e}")
            import traceback
            traceback.print_exc()
            return {}
