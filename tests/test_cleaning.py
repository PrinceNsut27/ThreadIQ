"""Unit tests for data cleaning and quarantining."""

import pandas as pd
import pytest

from src.threadiq.data.cleaning import (
    CleaningAudit,
    clean_customers,
    clean_order_items,
    clean_orders,
)


def test_clean_customers_standardization():
    """Test string trimming, zero padding of zip codes, title casing."""
    df = pd.DataFrame({
        "customer_id": [" c1  ", "c2"],
        "customer_unique_id": ["u1", "u2"],
        "customer_zip_code_prefix": [123, 98765],
        "customer_city": ["sao paulo", "RIO DE JANEIRO"],
        "customer_state": ["sp", "rj"],
    })
    clean_df = clean_customers(df)
    assert clean_df.iloc[0]["customer_id"] == "c1"
    assert clean_df.iloc[0]["customer_zip_code_prefix"] == "00123"
    assert clean_df.iloc[0]["customer_city"] == "Sao Paulo"
    assert clean_df.iloc[0]["customer_state"] == "SP"
    assert clean_df.iloc[1]["customer_city"] == "Rio De Janeiro"


def test_clean_orders_quarantine_invalid_timestamps():
    """Test that orders delivered before purchase are quarantined and not silently deleted."""
    audit = CleaningAudit()
    df = pd.DataFrame({
        "order_id": ["valid_ord", "invalid_ord"],
        "customer_id": ["c1", "c2"],
        "order_status": ["delivered", "delivered"],
        "order_purchase_timestamp": ["2018-05-10 10:00:00", "2018-05-10 10:00:00"],
        "order_delivered_customer_date": ["2018-05-15 12:00:00", "2018-05-01 10:00:00"],
    })
    clean_df, quarantined_df = clean_orders(df, audit=audit)

    assert len(clean_df) == 1
    assert clean_df.iloc[0]["order_id"] == "valid_ord"
    assert len(quarantined_df) == 1
    assert quarantined_df.iloc[0]["order_id"] == "invalid_ord"
    assert len(audit.quarantined_records) == 1
    assert "precedes purchase" in audit.quarantined_records[0]["reason"]


def test_clean_order_items_quarantine_negative_prices():
    """Test that items with negative price are quarantined and recorded in audit log."""
    audit = CleaningAudit()
    df = pd.DataFrame({
        "order_id": ["o1", "o2"],
        "order_item_id": [1, 1],
        "product_id": ["p1", "p2"],
        "seller_id": ["s1", "s2"],
        "price": [49.99, -15.00],
        "freight_value": [10.0, 5.0],
    })
    clean_df, quarantined_df = clean_order_items(df, audit=audit)

    assert len(clean_df) == 1
    assert clean_df.iloc[0]["order_id"] == "o1"
    assert len(quarantined_df) == 1
    assert quarantined_df.iloc[0]["order_id"] == "o2"
    assert len(audit.quarantined_records) == 1
    assert "Invalid price" in audit.quarantined_records[0]["reason"]
