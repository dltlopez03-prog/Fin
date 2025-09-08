from .registry import task
import pandas as pd
from pydantic import BaseModel, Field
from typing import List



def rename_category(df: pd.DataFrame, old:str, new:str) -> pd.DataFrame:
    assert new in CATEGORIES
    df = df.copy()
    df.loc[df["category"].str.lower()==old.lower(), "category"] = new
    return df

def merge_categories(df: pd.DataFrame, olds: List[str], new:str) -> pd.DataFrame:
    assert new in CATEGORIES
    df = df.copy()
    mask = df["category"].str.lower().isin([x.lower() for x in olds])
    df.loc[mask, "category"] = new
    return df



# Examples:
# ask("How much did I spend on groceries in July 2024?")
# ask("Show me my top 5 largest expenses this month.")
# ask("Compare my rent payments from 2023 vs 2024.")


# Add a rule (regex) so future runs auto-apply
# Example: add_rule("trader joe", "merchant", "Groceries", priority=10)
# Pick a tx to correct
# tx_to_fix = result.df.sample(1)["tx_id"].iloc[0]
# correct_category(tx_to_fix, "Groceries")
# After adding corrections, re-run the graph or call:
# result.df = apply_corrections_and_retrain(result.df)#from Multi-agent import PFState
#from pf_graph import PFGraph
