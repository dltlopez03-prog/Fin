from .registry import task, get
import pandas as pd

@task("aggregate_monthly")
def aggregate_monthly(df: pd.DataFrame, categorize_fn=None) -> pd.DataFrame:
    """Aggregate by month & category, optionally using a categorizer."""
    # No direct import — call another function via registry or DI:
    categorize_fn = categorize_fn or get("categorize")
    df = categorize_fn(df)
    if "date" not in df:
        raise ValueError("Expected 'date' column (normalize first).")
    out = (
        df.assign(month=pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp())
          .groupby(["month", "category"])["amount"].sum()
          .reset_index()
    )
    return out


def summarize(df: pd.DataFrame):
    df = df.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    by_cat = df.groupby("category", dropna=False)["amount"].sum().sort_values(ascending=True)
    by_month_cat = df.groupby(["month","category"])["amount"].sum().reset_index()
    return by_cat, by_month_cat

def drill_down(df: pd.DataFrame, category:str):
    return df[df["category"].str.lower()==category.lower()].sort_values("date")

def export_summary(df: pd.DataFrame, path:str=None):
    path = path or os.path.join(RUN_DIR, "expense_summary.csv")
    df.to_csv(path, index=False)
    return path
