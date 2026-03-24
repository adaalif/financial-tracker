import time
from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import get_logger, track_performance
from ai.groq_processor import process_image_with_groq
from parser.receipt_parser import parse_and_validate, regex_fallback_extraction, format_receipt_row_for_sheets
from pydantic import ValidationError
from sheets.sheets_client import append_to_sheets

logger = get_logger(__name__)

COOLDOWN_SECONDS = 10
user_last_request = {}

@track_performance
async def download_telegram_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bytes:
    """Extracts the highest-resolution photo from the message and downloads it to memory."""
    if not update.message or not update.message.photo:
        raise ValueError("No photo found in the message.")

    # Telegram includes multiple resolutions. The last one is the highest.
    photo_file = update.message.photo[-1]
    
    # Get the actual file object pointer from Telegram's servers
    file_obj = await context.bot.get_file(photo_file.file_id)
    
    # Download as byte array internally
    byte_array = await file_obj.download_as_bytearray()
    logger.info("Image downloaded successfully", file_size_bytes=len(byte_array))
    
    return bytes(byte_array)

@track_performance
async def handle_receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main Telegram handler for incoming photos."""
    user_id = update.effective_user.id
    current_time = time.time()
    
    # Global Rate limit check (2 minutes per user)
    if user_id in user_last_request:
        elapsed = current_time - user_last_request[user_id]
        if elapsed < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - elapsed)
            logger.warning("Rate limit actively blocking request", user_id=user_id, remaining=remaining)
            await update.message.reply_text(f"⏳ Please wait {remaining} seconds before analyzing another receipt to prevent IP bans.")
            return
            
    user_last_request[user_id] = current_time

    # 1. Provide immediate feedback to the user
    status_message = await update.message.reply_text("📸 Receipt received. Analyzing with AI...")
    
    try:
        # 2. Download the image bytes securely into memory
        image_bytes = await download_telegram_image(update, context)
        
        # 3. Process LLM analysis with a validation retry loop (Max 3 attempts)
        await status_message.edit_text("🧠 Analyzing image with Groq Vision AI...")
        
        receipt_data = None
        raw_json_str = "" 
        
        for attempt in range(3):
            raw_json_str, usage_metadata = await process_image_with_groq(image_bytes)
            
            # Debugging step: Dump raw output to a local text file
            debug_content = f"=== USAGE METADATA ===\n{usage_metadata}\n\n=== RAW JSON ===\n{raw_json_str}"
            with open("groq_debug_output.txt", "w", encoding="utf-8") as f:
                f.write(debug_content)
            logger.info("Dumped Groq output to groq_debug_output.txt")
            
            try:
                receipt_data = parse_and_validate(raw_json_str)
                break # Successfully parsed valid JSON matching Pydantic Schema!
            except (ValueError, ValidationError) as e:
                logger.warning(f"Validation failed on attempt {attempt+1}", error=str(e))
                if attempt == 2:
                    logger.error("All 3 LLM attempts failed. Falling back to Regex.")
                    receipt_data = regex_fallback_extraction(raw_json_str)
                    break
        
        # 4. Transform data layout for Google Sheets
        rows_data = format_receipt_row_for_sheets(receipt_data)
        
        # 5. Append data to Google Sheets
        await status_message.edit_text("📊 Saving structured receipt block to Google Sheets...")
        await append_to_sheets(rows_data)
        
        # Temp completion feedback
        merchant_name = receipt_data.merchant or "Unknown"
        total_amt = receipt_data.total or 0.0
        date_str = receipt_data.date or "Unknown"
        await status_message.edit_text(f"✅ Saved to Google Sheets!\n\nMerchant: {merchant_name}\nTotal: {total_amt}\nDate: {date_str}\nItems Saved: {len(rows_data)} rows")
        
    except ValueError as ve:
        logger.warning("Invalid input received", error=str(ve))
        await status_message.edit_text("❌ Please send a valid receipt image (not a document/file).")
    except Exception as e:
        logger.error("Error processing receipt", error=str(e), exc_info=True)
        await status_message.edit_text("❌ An unexpected error occurred while processing your receipt.")
