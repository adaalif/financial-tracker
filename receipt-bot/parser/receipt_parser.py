import re
import json
from typing import List
from pydantic import BaseModel, Field, ValidationError

from utils.logger import get_logger

logger = get_logger(__name__)

class ReceiptItem(BaseModel):
    name: str = Field(default="")
    price: float = Field(default=0.0)

class ReceiptData(BaseModel):
    """Strict JSON schema enforcing the exact structure Groq must respond with."""
    merchant: str = Field(default="")
    date: str = Field(default="")
    total: float = Field(default=0.0)
    currency: str = Field(default="")
    tax: float = Field(default=0.0)
    items: List[ReceiptItem] = Field(default_factory=list)
    category: str = Field(default="")

def extract_json_from_markdown(raw_text: str) -> str:
    """Strips markdown code blocks and reasoning blocks if present."""
    # Sometimes AI outputs <think>...</think> before JSON, or wraps JSON in ```json
    
    # 1. Strip <think> blocks
    raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
    
    # 2. Strip standard markdown code fences
    match = re.search(r"```(?:json)?(.*?)```", raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
        
    return raw_text.strip()

def parse_and_validate(raw_str: str) -> ReceiptData:
    """Attempts to parse the raw string as JSON and validate it against the Pydantic schema."""
    clean_json = extract_json_from_markdown(raw_str)
    
    try:
        data_dict = json.loads(clean_json)
        # Validate dictionary layout through Pydantic
        receipt = ReceiptData(**data_dict)
        return receipt
        
    except json.JSONDecodeError as e:
        logger.warning("JSON decode failed", error=str(e), raw_segment=clean_json[:100])
        raise ValueError("Invalid JSON format") from e
    except ValidationError as e:
        logger.warning("Pydantic validation failed structure check", error=str(e))
        raise

def regex_fallback_extraction(raw_str: str) -> ReceiptData:
    """If all LLM parses fail, attempt basic heuristics and Regex to find the critical fields."""
    logger.info("Executing regex fallback extraction")
    receipt = ReceiptData()
    
    # 1. Try to find Total (e.g. Total: 100.00, AMOUNT $45)
    total_match = re.search(r"(?i)(?:total|amount|sum|paid).*?([\d.,]+)", raw_str)
    if total_match:
        try:
            val = total_match.group(1).replace(",", "")
            receipt.total = float(val)
        except ValueError:
            pass

    # 2. Try to find Date (e.g. 2026-03-24, 03/24/2026)
    date_match = re.search(r"\b(\d{2,4}[-/]\d{2}[-/]\d{2,4})\b", raw_str)
    if date_match:
        receipt.date = date_match.group(1)
        
    return receipt

def format_receipt_row_for_sheets(data: ReceiptData) -> list[list]:
    """Flattens a ReceiptData object into a single row array for Google Sheets.
    The items are beautifully formatted with newlines into a single bulleted cell list."""
    merchant = data.merchant or ""
    date = data.date or ""
    total = data.total if data.total is not None else 0.0
    category = data.category or ""
    
    if data.items:
        structured_items_list = [f"• {item.name}: {item.price}" for item in data.items if item.name]
        items_cell_str = "\n".join(structured_items_list)
    else:
        items_cell_str = ""
        
    return [[merchant, date, total, items_cell_str, category]]
