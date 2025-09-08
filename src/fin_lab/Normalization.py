
from .registry import task
import pandas as pd

@task("normalize")
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names and types."""
    df = df.copy()
    mapping = {
        "Merchant": "merchant",
        "Date": "date",
        "Amount": "amount",
        "TxId": "tx_id",
    }
    df.rename(columns=mapping, inplace=True)
    if "amount" in df:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize a transaction DataFrame:
    - Standardize column names
    - Convert date to datetime
    - Convert amount to numeric
    - Ensure merchant column
    - Generate unique tx_id
    """
    if df is None:
        return df

    df = df.copy()

    # Lowercase + strip column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Convert fields
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    if "description" in df.columns:
        df["description"] = df["description"].astype(str).str.strip()

    if "merchant" not in df.columns and "description" in df.columns:
        df["merchant"] = df["description"]

    # ✅ Generate unique transaction id
    # Use row index + merchant + amount + date hash to avoid duplicates
    def make_id(row):
        raw = f"{row.get('date')}-{row.get('merchant')}-{row.get('amount')}"
        return hashlib.sha1(raw.encode()).hexdigest()[:10]

    df["tx_id"] = df.apply(make_id, axis=1)

    return df
