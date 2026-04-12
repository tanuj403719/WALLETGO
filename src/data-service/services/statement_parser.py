"""
Statement parser: extract transactions from CSV and PDF bank statements.
"""

from __future__ import annotations

import io
import logging
import re
from typing import Dict, List

import chardet
import pandas as pd
import pdfplumber

logger = logging.getLogger("walletgo.data.statement_parser")


DATE_VARIANTS = ["date", "transaction date", "posting date", "value date", "posted date"]
AMOUNT_VARIANTS = ["amount", "net amount"]
DEBIT_VARIANTS = ["debit", "debit amount", "withdrawals"]
CREDIT_VARIANTS = ["credit", "credit amount", "deposits"]
DESCRIPTION_VARIANTS = [
    "description",
    "transaction description",
    "narrative",
    "details",
    "memo",
    "reference",
]

DATE_REGEX = r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}-\d{2}-\d{2}'
AMOUNT_REGEX = r'-?\d{1,3}(?:,\d{3})*(?:\.\d{2})'


class StatementParseError(Exception):
    def __init__(self, message: str, detected_headers: list):
        super().__init__(message)
        self.message = message
        self.detected_headers = detected_headers


def _find_column(columns_lower: Dict[str, str], variants: List[str]) -> str | None:
    for variant in variants:
        if variant in columns_lower:
            return columns_lower[variant]
    return None


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    detected_headers = list(df.columns)
    columns_lower = {c.lower(): c for c in df.columns}

    date_col = _find_column(columns_lower, DATE_VARIANTS)
    amount_col = _find_column(columns_lower, AMOUNT_VARIANTS)
    debit_col = _find_column(columns_lower, DEBIT_VARIANTS)
    credit_col = _find_column(columns_lower, CREDIT_VARIANTS)
    description_col = _find_column(columns_lower, DESCRIPTION_VARIANTS)

    if date_col is None:
        raise StatementParseError(
            f"Could not detect a date column. Found headers: {detected_headers}",
            detected_headers,
        )

    rename_map = {date_col: "date"}

    if amount_col is not None:
        rename_map[amount_col] = "amount"
    elif debit_col is not None and credit_col is not None:
        debit_vals = pd.to_numeric(df[debit_col], errors="coerce").fillna(0)
        credit_vals = pd.to_numeric(df[credit_col], errors="coerce").fillna(0)
        df["amount"] = credit_vals - debit_vals
    else:
        raise StatementParseError(
            f"Could not detect amount column(s). Found headers: {detected_headers}",
            detected_headers,
        )

    if description_col is not None:
        rename_map[description_col] = "description"

    df = df.rename(columns=rename_map)

    if "description" not in df.columns:
        df["description"] = ""

    return df


def _assign_category(description: str) -> str:
    desc = (description or "").lower()
    if any(k in desc for k in ["rent", "mortgage"]):
        return "rent"
    if any(k in desc for k in ["salary", "payroll", "wages"]):
        return "income"
    if any(k in desc for k in ["netflix", "spotify", "amazon prime", "subscription"]):
        return "subscription"
    if any(k in desc for k in ["tesco", "sainsbury", "asda", "waitrose", "grocery", "supermarket"]):
        return "groceries"
    if any(k in desc for k in ["uber", "lyft", "transport", "rail", "tube", "bus"]):
        return "transport"
    if any(k in desc for k in ["restaurant", "cafe", "coffee", "dining"]):
        return "dining"
    return "general"


def _clean_dataframe(df: pd.DataFrame) -> List[Dict]:
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])
    df = df.head(500)

    rows: List[Dict] = []
    for _, r in df.iterrows():
        description = str(r.get("description", "") or "").strip()
        rows.append({
            "date": r["date"],
            "amount": float(r["amount"]),
            "description": description,
            "category": _assign_category(description),
        })
    return rows


def _parse_csv(content: bytes) -> List[Dict]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        detected = chardet.detect(content)
        encoding = detected.get("encoding") or "latin-1"
        text = content.decode(encoding, errors="replace")

    df = pd.read_csv(io.StringIO(text))
    df = _normalize_columns(df)
    return _clean_dataframe(df)


def _parse_pdf(content: bytes) -> List[Dict]:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table and len(table) > 1:
                headers = [str(h).strip() if h else "" for h in table[0]]
                df = pd.DataFrame(table[1:], columns=headers)
                try:
                    df = _normalize_columns(df)
                    return _clean_dataframe(df)
                except StatementParseError:
                    continue

        text = "\n".join((page.extract_text() or "") for page in pdf.pages)

    rows: List[Dict] = []
    for line in text.splitlines():
        date_match = re.search(DATE_REGEX, line)
        amount_matches = re.findall(AMOUNT_REGEX, line)
        if not date_match or not amount_matches:
            continue
        raw_amount = amount_matches[-1].replace(",", "")
        try:
            amount = float(raw_amount)
        except ValueError:
            continue
        date_str = date_match.group(0)
        parsed_date = pd.to_datetime(date_str, errors="coerce", dayfirst=False)
        if pd.isna(parsed_date):
            parsed_date = pd.to_datetime(date_str, errors="coerce", dayfirst=True)
        if pd.isna(parsed_date):
            continue
        description = re.sub(DATE_REGEX, "", line)
        description = re.sub(AMOUNT_REGEX, "", description).strip()
        rows.append({
            "date": parsed_date.strftime("%Y-%m-%d"),
            "amount": amount,
            "description": description,
            "category": _assign_category(description),
        })
        if len(rows) >= 500:
            break

    if not rows:
        logger.warning("PDF parse produced no rows")
    return rows


def parse_statement(content: bytes, filename: str) -> List[Dict]:
    """
    Parse a bank statement file (CSV or PDF) into a list of transaction dicts
    with keys: date, amount, description, category.
    """
    if filename.lower().endswith(".pdf"):
        rows = _parse_pdf(content)
    else:
        rows = _parse_csv(content)

    logger.info("Parsing %s, got %d rows", filename, len(rows))
    return rows
