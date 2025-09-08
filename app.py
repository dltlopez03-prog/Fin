#%%bash
#cat > app.py << 'PY'
import os, json, pandas as pd, plotly.express as px, streamlit as st




RUN_DIR = "fin_runs"
CSV = os.path.join(RUN_DIR, "expense_summary.csv")

st.set_page_config(page_title="Finance Dashboard", layout="wide")
st.title("Personal Spending Dashboard")

@st.cache_data
def load():
    df = pd.read_csv(CSV, parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df

if not os.path.exists(CSV):
    st.warning("Run the notebook pipeline to generate expense_summary.csv first.")
else:
    df = load()
    cats = sorted(df["category"].unique())
    sel_cats = st.multiselect("Categories", cats, default=cats)
    dfv = df[df["category"].isin(sel_cats)]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Total by Category")
        g = dfv.groupby("category")["amount"].sum().reset_index()
        st.dataframe(g.sort_values("amount"))
        fig = px.bar(g, x="category", y="amount")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Monthly Trend")
        g2 = dfv.groupby(["month"])["amount"].sum().reset_index()
        fig2 = px.line(g2, x="month", y="amount")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Transactions (drill-down)")
    st.dataframe(dfv.sort_values("date", ascending=False))
#PY
