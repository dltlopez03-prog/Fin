from .registry import task
import pandas as pd
from pydantic import BaseModel, Field



class PFState(BaseModel):
    files: list[str] = Field(default_factory=list)
    df: pd.DataFrame | None = None
    by_cat_json: str | None = None

    model_config = {
        "arbitrary_types_allowed": True
    }


def ingest_node(state: PFState) -> PFState:
    frames=[]
    for p in state.files:
        frames.append(load_any(p))
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["date","description","amount","merchant","account","source_file"])
    return state.copy(update={"df": df})

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Dates
    df["date"] = df["date"].apply(lambda x: dateparser.parse(str(x), settings={"PREFER_DAY_OF_MONTH":"first"}))
    df["date"] = pd.to_datetime(df["date"]).dt.date
    # Amount
    df["amount"] = df["amount"].apply(_to_float)
    # Normalize description/merchant
    df["description"] = df["description"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    df["merchant"] = df["merchant"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

    # Attempt better merchant extraction from common POS strings
    def clean_merchant(desc, merchant):
        # Strip common bank noise
        noise = ["POS PURCHASE", "DEBIT CARD PURCHASE", "CARDMEMBER SERV", "CHECKCARD", "VISA", "MASTERCARD",
                 "AMAZON MKTPLACE", "AMZN Mktp", "PAYMENT - THANK YOU", "ONLINE TRANSFER"]
        m = merchant or desc
        for n in noise:
            m = re.sub(n, "", m, flags=re.I)
        m = re.sub(r"\d{4,}", "", m) # strip long numbers
        return m.strip(" -–—·|")
    df["merchant"] = [clean_merchant(d, m) for d, m in zip(df["description"], df["merchant"])]

    # Currency/account defaults
    if "currency" not in df.columns: df["currency"] = "USD"
    if "account"  not in df.columns: df["account"] = "unknown"

    # Create tx_id deterministically (date+amount+merchant+source_file)
    df["tx_id"] = df.apply(lambda r: uuid.uuid5(uuid.NAMESPACE_URL,
                            f"{r['date']}|{r['amount']}|{r['merchant']}|{r['source_file']}").hex, axis=1)
    # Canonical ordering
    keep = ["tx_id","date","amount","description","merchant","account","currency","source_file"]
    return df[keep]


def normalize_node(state: PFState) -> PFState:
    return state.copy(update={"df": normalize(state.df)})


def categorize_node(state: PFState) -> PFState:
    df = categorize(state.df)
    return state.copy(update={"df": df})

def learn_node(state: PFState) -> PFState:
    df = apply_corrections_and_retrain(state.df)
    return state.copy(update={"df": df})

def analyze_node(state: PFState) -> PFState:
    by_cat, by_month_cat = summarize(state.df)
    return state.copy(update={
        "by_cat_json": json.dumps(by_cat.to_dict()),
        "by_month_cat_json": json.dumps(by_month_cat.to_dict(orient="records")),
    })

def export_node(state: PFState) -> PFState:
    path = export_summary(state.df)
    return state.copy(update={"output_csv": path})

def query_node(state: PFState) -> PFState:
    if not state.query:
        return state
    ans = answer_query(state.df, state.query)
    return state.copy(update={"query_answer": ans})


# Conditional branch: only run query if provided
def should_query(state: PFState):
    return "query" if state.query else END

