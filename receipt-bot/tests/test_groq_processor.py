import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage
from ai.groq_processor import process_image_with_groq

@pytest.mark.asyncio
@patch("langchain_groq.ChatGroq.ainvoke", new_callable=AsyncMock)
async def test_process_image_with_groq_success(mock_ainvoke):
    """Ensure image is encoded properly and tracked JSON is returned."""
    # Mock LLM response with Langchain 0.2 style usage_metadata
    mock_response = AIMessage(
        content='{"total": 150.0}',
        usage_metadata={"input_tokens": 50, "output_tokens": 10, "total_tokens": 60}
    )
    mock_ainvoke.return_value = mock_response
    
    fake_image_bytes = b"fake_picture_data"
    result_str, usage_dict = await process_image_with_groq(fake_image_bytes)
    
    # Check return string and metadata
    assert result_str == '{"total": 150.0}'
    assert usage_dict["total_tokens"] == 60
    
    # Verify execution format
    mock_ainvoke.assert_called_once()
    
    # Ensure Base64 formatting is injected correctly into the array
    call_args = mock_ainvoke.call_args[0][0]
    human_message = call_args[0]
    assert human_message.content[1]["type"] == "image_url"
    assert human_message.content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
