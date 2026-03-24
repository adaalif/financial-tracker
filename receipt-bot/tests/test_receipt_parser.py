import pytest
from pydantic import ValidationError
from parser.receipt_parser import (
    extract_json_from_markdown,
    parse_and_validate,
    regex_fallback_extraction,
    format_receipt_row_for_sheets,
    ReceiptData,
    ReceiptItem
)

def test_extract_json_from_markdown():
    raw_md = "Here is the json:\n```json\n{\"test\": 1}\n```\nHope it helps."
    assert extract_json_from_markdown(raw_md) == '{"test": 1}'
    
    raw_think = "<think>Calculating total...</think>\n{\"test\": 2}"
    assert extract_json_from_markdown(raw_think) == '{"test": 2}'
    
def test_parse_and_validate_success():
    valid_json = '{"merchant": "Target", "total": 15.5, "items": [{"name": "Apple", "price": 5.0}]}'
    receipt = parse_and_validate(valid_json)
    assert receipt.merchant == "Target"
    assert receipt.total == 15.5
    assert len(receipt.items) == 1
    assert receipt.items[0].name == "Apple"

def test_parse_and_validate_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON format"):
        parse_and_validate('{"merchant": "Store" "missing_quotes')

def test_parse_and_validate_invalid_schema():
    bad_schema = '{"merchant": ["Array", "Not String"]}'
    with pytest.raises(ValidationError):
        parse_and_validate(bad_schema)
    
def test_regex_fallback_extraction():
    raw = "The total paid was 45.50 on 2026-03-24 at Starbucks."
    receipt = regex_fallback_extraction(raw)
    
    assert receipt.total == 45.5
    assert receipt.date == "2026-03-24"

def test_format_receipt_row_for_sheets():
    """Ensure items array formats cleanly to a single structured cell."""
    data = ReceiptData(
        merchant="TestStore", total=150.0, date="2026-03-24",
        items=[
            ReceiptItem(name="Item1", price=50.0),
            ReceiptItem(name="Item2", price=100.0)
        ]
    )
    rows = format_receipt_row_for_sheets(data)
    assert len(rows) == 1
    assert rows[0] == ["TestStore", "2026-03-24", 150.0, "• Item1: 50.0\n• Item2: 100.0", ""]
