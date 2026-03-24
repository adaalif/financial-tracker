import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers import download_telegram_image, handle_receipt_photo

@pytest.mark.asyncio
async def test_download_telegram_image_no_photo():
    """Ensure it throws a ValueError if no photo exists."""
    update = MagicMock()
    update.message.photo = []
    context = AsyncMock()
    
    with pytest.raises(ValueError, match="No photo found in the message."):
        await download_telegram_image(update, context)

@pytest.mark.asyncio
async def test_download_telegram_image_success():
    """Ensure highest quality photo file_id is retrieved and mocked downloading works."""
    update = MagicMock()
    
    # Create mock photo objects
    low_res = MagicMock()
    high_res = MagicMock()
    high_res.file_id = "test_file_id_high_res"
    update.message.photo = [low_res, high_res]  # Last item is highest res
    
    context = AsyncMock()
    file_obj_mock = AsyncMock()
    file_obj_mock.download_as_bytearray.return_value = bytearray(b"fake_image_bytes")
    context.bot.get_file.return_value = file_obj_mock
    
    # Execute
    result = await download_telegram_image(update, context)
    
    assert result == b"fake_image_bytes"
    context.bot.get_file.assert_called_once_with("test_file_id_high_res")
    file_obj_mock.download_as_bytearray.assert_called_once()

@pytest.mark.asyncio
async def test_handle_receipt_photo_success(monkeypatch):
    """Ensure the handler replies, downloads the photo, and edits the message on success."""
    update = MagicMock()
    update.effective_user.id = 123456
    status_message_mock = AsyncMock()
    update.message.reply_text = AsyncMock(return_value=status_message_mock)
    
    context = AsyncMock()
    
    # Mock out the internal download step
    async def mock_download(*args, **kwargs):
        return b"fake_bytes"
        
    # Mock out the AI processing step
    async def mock_groq(*args, **kwargs):
        # Must pass pydantic validation, so we return valid json!
        return '{"merchant": "test store", "total": 100, "date": "2026-03-24", "items": []}', {"total_tokens": 10}
        
    async def mock_sheets(*args, **kwargs):
        return True
        
    import bot.handlers
    monkeypatch.setattr(bot.handlers, "download_telegram_image", mock_download)
    monkeypatch.setattr(bot.handlers, "process_image_with_groq", mock_groq)
    monkeypatch.setattr(bot.handlers, "append_to_sheets", mock_sheets)
    
    await handle_receipt_photo(update, context)
    
    update.message.reply_text.assert_called_once_with("📸 Receipt received. Analyzing with AI...")
    assert status_message_mock.edit_text.call_count == 3
    
    # Assert final message confirms Sheets output
    assert "fake_bytes" not in status_message_mock.edit_text.call_args[0][0]
    assert "100" in status_message_mock.edit_text.call_args[0][0]
    assert "Saved to Google Sheets" in status_message_mock.edit_text.call_args[0][0]
