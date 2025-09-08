import pandas as pd
import plotly.express as px

def to_dataframe(data):
    if isinstance(data, pd.DataFrame):
        return data
    try:
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

def detect_column_types(df):
    types = {"numerical": [], "categorical": [], "datetime": []}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            types["numerical"].append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            types["datetime"].append(col)
        else:
            types["categorical"].append(col)
    return types

def plot_sales_trend(df, date_col, value_col):
    return px.line(df.groupby(date_col)[value_col].sum().reset_index(),
                   x=date_col, y=value_col, title=f"{value_col} Trend Over Time")

def plot_categorical_breakdown(df, cat_col, value_col):
    agg = df.groupby(cat_col)[value_col].sum().reset_index()
    return px.bar(agg, x=cat_col, y=value_col, title=f"{value_col} by {cat_col}")

def plot_pie_chart(df, cat_col, value_col):
    agg = df.groupby(cat_col)[value_col].sum().reset_index()
    return px.pie(agg, names=cat_col, values=value_col, title=f"{value_col} Share by {cat_col}")

def recommend_visualizations(df, max_charts=3):
    types = detect_column_types(df)
    visuals = []
    if types["datetime"] and types["numerical"]:
        visuals.append(plot_sales_trend(df, types["datetime"][0], types["numerical"][0]))

    if types["categorical"] and types["numerical"]:
        visuals.append(plot_categorical_breakdown(df, types["categorical"][0], types["numerical"][0]))
        visuals.append(plot_pie_chart(df, types["categorical"][0], types["numerical"][0]))

    return visuals[:max_charts]

if __name__ == "__main__":
    import pandas as pd
    df = pd.DataFrame({
        "Date": pd.date_range(start="2023-01-01", periods=10, freq="D"),
        "Sales": [100, 150, 200, 130, 170, 160, 190, 220, 210, 230],
        "Category": ["A", "B", "A", "A", "B", "B", "A", "B", "A", "B"]
    })
    visuals = recommend_visualizations(df)
    for i, fig in enumerate(visuals):
        print(f"Showing Figure {i+1}")
        fig.show()
