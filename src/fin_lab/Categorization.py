from .registry import task
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SEED = 42




def _load_rules():
    with _connect() as c:
        return pd.read_sql_query("SELECT * FROM category_rules ORDER BY priority ASC, id ASC", c)
 # keep this here anyway for the body using pd.Series

def apply_rules(df: "pd.DataFrame") -> "pd.Series":
    cats = pd.Series(index=df.index, dtype="object")
    rules = _load_rules()
    for _, r in rules.iterrows():
        pat = re.compile(r["pattern"], flags=re.I)
        fld = r["field"]
        mask = df[fld].astype(str).apply(lambda x: bool(pat.search(x)))
        cats.loc[mask & cats.isna()] = r["category"]
    return cats


def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib_load(MODEL_PATH)
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=2)),
        ("clf", SGDClassifier(loss="log_loss", max_iter=1000, tol=1e-3))
    ])
    return pipe

def train_or_update_model(df_labeled: pd.DataFrame):
    pipe = load_model()
    X = (df_labeled["merchant"].fillna("") + " " + df_labeled["description"].fillna(""))
    y = df_labeled["category"]
    pipe.fit(X, y)
    dump(pipe, MODEL_PATH)
    return pipe

def predict_categories(df: pd.DataFrame, pipe=None) -> pd.Series:
    pipe = pipe or load_model()
    if not os.path.exists(MODEL_PATH):
        # cold start: simple heuristics
        heur = {
            "grocer|whole foods|trader joe|kroger|safeway|aldi|heb": "Groceries",
            "uber|lyft|shell|chevron|exxon|76 gas|bp": "Transport",
            "netflix|spotify|hulu|prime": "Subscriptions",
            "airbnb|delta|united|american airlines|hotel": "Travel",
            "insur": "Insurance",
            "md|clinic|pharmacy|walgreens|cvs": "Health",
            "amzn|amazon": "Shopping",
            "rent|landlord|apartment": "Rent",
            "utility|water|power|electric|gas|comcast|xfinity|att|verizon": "Utilities",
        }
        out = pd.Series("Misc", index=df.index)
        for pat, cat in heur.items():
            mask = (df["merchant"].str.contains(pat, case=False, regex=True) |
                    df["description"].str.contains(pat, case=False, regex=True))
            out[mask] = cat
        return out
    X = (df["merchant"].fillna("") + " " + df["description"].fillna(""))
    return pd.Series(pipe.predict(X), index=df.index)

def categorize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    rule_cats = apply_rules(df)
    ml_cats   = predict_categories(df)
    df["category"] = rule_cats.fillna(ml_cats).fillna("Misc")
    return df

def correct_category(tx_id:str, new_category:str):
    assert new_category in CATEGORIES, f"Unknown category: {new_category}"
    with _connect() as c:
        c.execute("INSERT OR REPLACE INTO corrections(tx_hash, category) VALUES(?,?)", (tx_id, new_category))
        c.commit()

def apply_corrections_and_retrain(df: pd.DataFrame):
    with _connect() as c:
        corr = pd.read_sql_query("SELECT tx_hash, category FROM corrections", c)
    if corr.empty: return df
    df = df.copy()
    df = df.merge(corr, how="left", left_on="tx_id", right_on="tx_hash")
    df["category"] = df["category_y"].fillna(df["category"]).fillna("Misc")
    df = df.drop(columns=["tx_hash","category_y"])
    # retrain model on corrected rows
    labeled = df[~df["category"].isna()]
    train_or_update_model(labeled)
    return df
