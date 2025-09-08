print('Running PDF.....')

from .registry import task

@task("extract_from_pdf")
def extract_from_pdf(pdf_path: str) -> list[str]:
    """Stub: return list of raw lines from a PDF statement (replace with real logic)."""
    # Implement with your extractor of choice later.
    return ["2025-08-01, Coffee Shop, 4.50", "2025-08-02, Grocery Mart, 32.10"]




DATE_PAT = r"(?P<date>\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}\b)"
AMT_PAT  = r"(?P<amount>-?\$?\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"

def _to_float(x):
    if x is None or (isinstance(x, float) and np.isnan(x)): return np.nan
    val = str(x).replace("$","").replace(",","").strip()
    try: return float(val)
    except: return np.nan

def load_csv(path:str, account:str=""):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    # Minimal heuristics
    guess_cols = dict(
        date = next((c for c in df.columns if c in ("date","posted date","transaction date","posting date")), None),
        desc = next((c for c in df.columns if c in ("description","memo","details","payee")), None),
        amt  = next((c for c in df.columns if c in ("amount","amt","debit","credit","value")), None)
    )
    if guess_cols["amt"] is None and {"debit","credit"}.issubset(set(df.columns)):
        df["amount"] = df["credit"].fillna(0) - df["debit"].fillna(0)
        guess_cols["amt"] = "amount"
    df2 = pd.DataFrame({
        "date": df[guess_cols["date"]],
        "description": df[guess_cols["desc"]],
        "amount": df[guess_cols["amt"]],
    })
    df2["merchant"] = df2["description"]
    df2["account"] = account or os.path.basename(path)
    df2["source_file"] = path
    return df2

def load_xlsx(path:str, account:str=""):
    return load_csv(path, account) if path.endswith(".csv") else pd.read_excel(path).pipe(
        lambda x: load_csv(x.to_csv(index=False), account) # fallback via CSV serialization
    )

def parse_pdf_lines(text:str):
    # Fallback generic parser using regex on lines.
    rows=[]
    for line in text.splitlines():
        m_date = re.search(DATE_PAT, line)
        m_amt  = re.search(AMT_PAT, line.replace(",", ""))
        if m_date and m_amt:
            date_s = m_date.group("date")
            amt_s  = m_amt.group("amount")
            # description = line with date/amount removed
            desc = line
            desc = desc.replace(m_date.group("date"), "").replace(m_amt.group("amount"), "").strip(" -\t")
            rows.append({"date":date_s, "description":desc, "amount":amt_s})
    return pd.DataFrame(rows)

def load_pdf(path:str, account:str=""):
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    df = parse_pdf_lines(text)
    if df.empty:
        warnings.warn(f"Generic PDF parse produced 0 rows for {path}.")
    df["merchant"] = df["description"]
    df["account"] = account or os.path.basename(path)
    df["source_file"] = path
    return df

def load_docx(path:str, account:str=""):
    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs)
    df = parse_pdf_lines(text)
    df["merchant"] = df["description"]
    df["account"] = account or os.path.basename(path)
    df["source_file"] = path
    return df

def load_image(path:str, account:str=""):
    img = Image.open(path)
    text = pytesseract.image_to_string(img)
    df = parse_pdf_lines(text)
    df["merchant"] = df["description"]
    df["account"] = account or os.path.basename(path)
    df["source_file"] = path
    return df

def load_any(path:str, account:str=""):
    path_l = path.lower()
    if path_l.endswith(".csv"):  return load_csv(path, account)
    if path_l.endswith(".xlsx") or path_l.endswith(".xls"): return load_xlsx(path, account)
    if path_l.endswith(".pdf"):  return load_pdf(path, account)
    if path_l.endswith(".docx"): return load_docx(path, account)
    if path_l.endswith((".png",".jpg",".jpeg",".tif",".tiff")): return load_image(path, account)
    raise ValueError(f"Unsupported file: {path}")


print('>>>>>Success')