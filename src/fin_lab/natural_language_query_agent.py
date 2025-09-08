from .registry import task
from typing import Optional, List
import pandas as pd
from typing import Dict
from typing import Any



MONTH_MAP = {m.lower():i for i,m in enumerate(["January","February","March","April","May","June",
                                               "July","August","September","October","November","December"], start=1)}

def parse_month(s:str) -> Optional[str]:
    s=s.lower()
    # e.g., "july 2024", "july", "this month", "last month"
    today = dt.date.today()
    if "this month" in s:
        return f"{today.year}-{today.month:02d}"
    if "last month" in s:
        lm = (pd.Timestamp(today) - pd.offsets.MonthBegin()).to_pydatetime().date()
        lm = (pd.Timestamp(lm) - pd.offsets.MonthBegin()).to_pydatetime().date()
        return f"{lm.year}-{lm.month:02d}"
    m = None
    for name, idx in MONTH_MAP.items():
        if name in s:
            m = idx; break
    if m:
        year = None
        m_year = re.search(r"(20\d{2})", s)
        year = int(m_year.group(1)) if m_year else dt.date.today().year
        return f"{year}-{m:02d}"
    return None

def answer_query(df: pd.DataFrame, q: str) -> Dict[str, Any]:
    ql = q.lower()
    df2 = df.copy()
    df2["month"] = pd.to_datetime(df2["date"]).dt.to_period("M").astype(str)

    # "How much did I spend on groceries in July?"
    if "how much" in ql or "total" in ql:
        # find category by fuzzy match
        cat = None
        for c in CATEGORIES:
            if c.lower() in ql: cat = c; break
        if not cat:
            cand, score, _ = rf_process.extractOne(ql, CATEGORIES, scorer=fuzz.partial_ratio)
            cat = cand if score>70 else None
        month = parse_month(ql)
        mask = pd.Series(True, index=df2.index)
        if cat:   mask &= df2["category"].str.lower()==cat.lower()
        if month: mask &= df2["month"]==month
        total = df2.loc[mask, "amount"].sum()
        return {"type":"total", "category":cat, "month":month, "total":float(total)}

    # "Show me my top 5 largest expenses this month."
    if "top" in ql and "expense" in ql:
        k = re.search(r"top\s+(\d+)", ql)
        k = int(k.group(1)) if k else 5
        month = parse_month(ql) or parse_month("this month")
        mask = df2["month"]==month
        # expenses: negative or positive? assume outflow is negative; if mixed, sort by absolute descending of negative rows
        out = df2.loc[mask].copy()
        out["abs_amt"] = out["amount"].abs()
        out = out.sort_values("abs_amt", ascending=False).head(k)
        cols = ["date","merchant","description","amount","category","account"]
        return {"type":"top", "month":month, "rows": out[cols].to_dict(orient="records")}

    # "Compare my rent payments from 2023 vs 2024."
    if "compare" in ql and "vs" in ql:
        years = [int(y) for y in re.findall(r"(20\d{2})", ql)]
        years = years if years else [dt.date.today().year-1, dt.date.today().year]
        cat = None
        for c in CATEGORIES:
            if c.lower() in ql: cat = c; break
        cat = cat or "Rent"
        out = df2[df2["category"].str.lower()==cat.lower()].copy()
        out["year"] = pd.to_datetime(out["date"]).dt.year
        comp = out[out["year"].isin(years)].groupby("year")["amount"].sum().reindex(years).fillna(0)
        return {"type":"compare", "category":cat, "years":years, "totals":comp.to_dict()}

    # Fallback: quick category totals
    by_cat = df2.groupby("category")["amount"].sum().sort_values()
    return {"type":"summary", "by_category": by_cat.to_dict()}
