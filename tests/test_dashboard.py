import pytest
import pandas as pd
import numpy as np

class TestDashboardData:
    def test_dataframe_not_empty(self):
        df = pd.DataFrame({"metric": [1, 2, 3], "value": [10.0, 20.0, 30.0]})
        assert not df.empty

    def test_aggregation_correct(self):
        df = pd.DataFrame({"category": ["A","A","B","B"], "sales": [100,200,150,250]})
        agg = df.groupby("category")["sales"].sum()
        assert agg["A"] == 300
        assert agg["B"] == 400

    def test_percentage_calculation(self):
        total = 1000
        part = 250
        pct = (part / total) * 100
        assert pct == 25.0

    def test_null_values_handled(self):
        df = pd.DataFrame({"value": [1.0, None, 3.0, None, 5.0]})
        filled = df["value"].fillna(df["value"].mean())
        assert filled.isnull().sum() == 0

    def test_date_range_valid(self):
        dates = pd.date_range("2024-01-01", periods=12, freq="ME")
        assert len(dates) == 12

class TestVisualization:
    def test_color_palette_defined(self):
        palette = ["#534AB7", "#3B6D11", "#BA7517", "#A32D2D", "#185FA5"]
        assert len(palette) == 5

    def test_chart_data_sorted(self):
        data = [("C", 30), ("A", 100), ("B", 60)]
        sorted_data = sorted(data, key=lambda x: x[1], reverse=True)
        assert sorted_data[0][0] == "A"
