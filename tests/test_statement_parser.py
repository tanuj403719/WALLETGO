"""Tests for the bank statement parser."""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "data-service"))

from services.statement_parser import (  # noqa: E402
    StatementParseError,
    _assign_category,
    parse_statement,
)


DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def test_parse_natwest_csv():
    csv = (
        "Date,Description,Debit Amount,Credit Amount\n"
        "01/05/2024,Rent payment,1500.00,\n"
        "05/05/2024,Salary,,4000.00\n"
    )
    result = parse_statement(csv.encode("utf-8"), "statement.csv")

    assert isinstance(result, list)
    assert len(result) == 2

    rent = next(r for r in result if "Rent" in r["description"])
    salary = next(r for r in result if "Salary" in r["description"])

    assert rent["amount"] == -1500.0
    assert salary["amount"] == 4000.0
    assert all(DATE_ISO.match(r["date"]) for r in result)


def test_parse_generic_csv_with_amount_column():
    csv = (
        "Date,Description,Amount\n"
        "2024-05-01,Coffee shop,-4.50\n"
        "2024-05-02,Refund,12.00\n"
        "2024-05-03,Groceries,-55.25\n"
    )
    result = parse_statement(csv.encode("utf-8"), "generic.csv")

    assert len(result) == 3
    amounts = {r["description"]: r["amount"] for r in result}
    assert amounts["Coffee shop"] == -4.50
    assert amounts["Refund"] == 12.00
    assert amounts["Groceries"] == -55.25


def test_unknown_columns_raises_error():
    csv = "Foo,Bar,Baz\n1,2,3\n"
    with pytest.raises(StatementParseError) as excinfo:
        parse_statement(csv.encode("utf-8"), "bad.csv")
    assert excinfo.value.detected_headers == ["Foo", "Bar", "Baz"]


def test_category_assignment():
    assert _assign_category("Netflix monthly charge") == "subscription"
    assert _assign_category("Tesco superstore") == "groceries"
    assert _assign_category("Monthly salary payment") == "income"
    assert _assign_category("Random purchase xyz") == "general"


def test_max_rows_limit():
    lines = ["Date,Description,Amount"]
    for i in range(600):
        lines.append(f"2024-05-01,Tx {i},-1.00")
    csv = "\n".join(lines) + "\n"
    result = parse_statement(csv.encode("utf-8"), "big.csv")
    assert len(result) == 500


def test_parse_currency_formatted_debit_credit_columns():
    csv = (
        "Date,Description,Debit Amount,Credit Amount\n"
        "2024-10-01,Rent,\"$1,400.00\",\n"
        "2024-10-05,Salary,,\"$4,800.00\"\n"
        "2024-10-07,Groceries,\"$91.30\",\n"
    )
    result = parse_statement(csv.encode("utf-8"), "currency_dc.csv")
    amounts = {r["description"]: r["amount"] for r in result}

    assert amounts["Rent"] == -1400.0
    assert amounts["Salary"] == 4800.0
    assert amounts["Groceries"] == -91.3


def test_parse_currency_amount_column_with_dr_cr_and_parentheses():
    csv = (
        "Date,Description,Amount\n"
        "2024-05-01,Coffee,\"($4.50)\"\n"
        "2024-05-02,Refund,\"$12.00\"\n"
        "2024-05-03,Bonus,\"£1,234.56 CR\"\n"
        "2024-05-04,Bill,\"$52.10 DR\"\n"
    )
    result = parse_statement(csv.encode("utf-8"), "currency_amount.csv")
    amounts = {r["description"]: r["amount"] for r in result}

    assert amounts["Coffee"] == -4.5
    assert amounts["Refund"] == 12.0
    assert amounts["Bonus"] == 1234.56
    assert amounts["Bill"] == -52.1
