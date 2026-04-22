import base64
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from tenacity import retry, wait_exponential, stop_after_attempt

from config import GROQ_API_KEY
from utils.logger import get_logger, track_performance, log_token_usage

logger = get_logger(__name__)

# Initialize the Groq Vision model
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.0, # Deterministic outputs are best for strict JSON formatting
)

PROMPT_TEXT = """You are a financial receipt analysis assistant.
Analyze the receipt image and extract structured expense data.

Return STRICT JSON only:
{
  "merchant": "string",
  "date": "YYYY-MM-DD",
  "total": 0.0,
  "currency": "IDR",
  "tax": 0.0,
  "items": [{"name": "item", "price": 0.0, "category": "groceries/transport/food/entertainment/general"}]
}

Rules:
- No explanations or extra text
- Do NOT guess unclear values (use empty string "" or 0)
- Normalize numbers (no currency symbols)
- CRITICAL FOR CURRENCY: Remove ALL dots (.) and commas (,) from numbers entirely! Indonesian and European formatting uses punctuation for thousands. For example, `25.000` MUST be `25000`. `45,000` MUST be `45000`. `45,000.00` MUST be `45000`. Never include dots or commas in your numerical JSON outputs.
- Default currency to IDR unless explicitly stated otherwise
- Prefer final payable total
- Keep item names short
- Infer a specific category (food, groceries, electronics, bills, etc) explicitly for EACH sub-item
- Ensure valid JSON at all times
"""

@track_performance
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def process_image_with_groq(image_bytes: bytes) -> tuple[str, dict]:
    """
    Sends the image bytes to Groq Vision API and returns the raw JSON string.
    Retries up to 3 times on typical API faults.
    """
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    # Construct the multimodal message
    message = HumanMessage(
        content=[
            {"type": "text", "text": PROMPT_TEXT},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
            },
        ]
    )
    
    logger.info("Sending receipt image to Groq Vision API...")
    
    # Run API generation
    response = await llm.ainvoke([message])
    
    # Try to grab token usage logic (handles both LangChain 0.1 and 0.2 object structures)
    usage = None
    if getattr(response, "usage_metadata", None):
        usage = response.usage_metadata
    elif "token_usage" in response.response_metadata:
        usage = response.response_metadata["token_usage"]
        
    if usage:
        log_token_usage("groq_vision_call", usage)
    
    logger.info("Groq API successfully returned data.")
    return str(response.content), usage or {}
