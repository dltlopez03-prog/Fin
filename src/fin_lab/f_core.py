from .registry import task

print('Running Functions.....')



import os, re, json, sqlite3, uuid, warnings, duckdb, datetime as dt
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import dateparser
from rapidfuzz import fuzz, process as rf_process
import hashlib
import pdfplumber
from PIL import Image
import pytesseract
from docx import Document
import dateparser   
import uuid
import re
from rapidfuzz import fuzz 
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
import os

@dataclass
class Transaction:
    tx_id: str
    date: dt.date
    amount: float
    description: str
    merchant: str
    account: str
    category: str = "Misc"
    currency: str = "USD"
    source_file: str = ""
    raw: Dict[str, Any] = None

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS category_rules(
        id INTEGER PRIMARY KEY,
        pattern TEXT NOT NULL,          -- regex or literal
        field   TEXT NOT NULL,          -- 'merchant' | 'description'
        category TEXT NOT NULL,
        priority INTEGER DEFAULT 100    -- lower = earlier
    );""")
    conn.execute("""CREATE TABLE IF NOT EXISTS corrections(
        id INTEGER PRIMARY KEY,
        tx_hash TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );""")
    conn.commit()
    return conn

def add_rule(pattern:str, field:str, category:str, priority:int=100):
    assert field in ("merchant","description")
    assert category in CATEGORIES
    with _connect() as c:
        c.execute("INSERT INTO category_rules(pattern,field,category,priority) VALUES(?,?,?,?)",
                  (pattern, field, category, priority))
        c.commit()

print('>>>>>Success')
