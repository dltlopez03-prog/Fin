from .registry import task
from typing import Optional, List

def ask(question:str, files:Optional[List[str]]=None):
    st = PFState(files=files or [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)],
                 query=question)
    res = graph.invoke(st)
    ans = res.query_answer
    if ans["type"] == "total":
        print(f"Total {ans['category'] or ''} {ans['month'] or ''}: ${ans['total']:.2f}")
    elif ans["type"] == "top":
        print(f"Top expenses for {ans['month']}:")
        pd.DataFrame(ans["rows"])
    elif ans["type"] == "compare":
        print(f"Compare {ans['category']} {ans['years']}: {ans['totals']}")
    else:
        print("Summary by category:")
        print(pd.Series(ans["by_category"]))
    return res

# Examples:
# ask("How much did I spend on groceries in July 2024?")
# ask("Show me my top 5 largest expenses this month.")
# ask("Compare my rent payments from 2023 vs 2024.")

def run_pipeline(files: Optional[List[str]]=None, query: Optional[str]=None):
    files = files or [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)]
    state = PFState(files=files, query=query)
    return graph.invoke(state)

# === Run full pipeline ===

