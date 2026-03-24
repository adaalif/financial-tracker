import pytest
from unittest.mock import MagicMock, patch
from sheets.sheets_client import append_to_sheets

@pytest.mark.asyncio
@patch("sheets.sheets_client.get_sheets_service")
async def test_append_to_sheets_success(mock_get_service):
    """Ensure our async thread wrapper resolves API calls correctly into exact array index alignments for Sheets."""
    mock_service = MagicMock()
    mock_sheet = MagicMock()
    mock_values = MagicMock()
    mock_append = MagicMock()
    mock_get = MagicMock()
    mock_get.execute.return_value = {"sheets": [{"properties": {"title": "CustomSheetName"}}]}
    
    # Wire the Google discovery builder mocks internally
    mock_get_service.return_value = mock_service
    mock_service.spreadsheets.return_value = mock_sheet
    mock_sheet.values.return_value = mock_values
    mock_sheet.get.return_value = mock_get
    mock_values.append.return_value = mock_append
    mock_append.execute.return_value = {"updates": {"updatedRows": 1}}
    
    fake_rows = [
        ["Target", "2026-03-24", 5.5, "Apples", "Groceries"],
        ["Target", "2026-03-24", 45.0, "Milk", "Groceries"]
    ]
    
    result = await append_to_sheets(fake_rows)
    
    assert result is True
    
    # Verify 2 rows were loaded with aligned properties
    mock_values.append.assert_called_once()
    kwargs = mock_values.append.call_args[1]
    
    assert kwargs["valueInputOption"] == "USER_ENTERED"
    assert len(kwargs["body"]["values"]) == 2
    assert kwargs["body"]["values"][0][0] == "Target"   # row 0, column A (Merchant)
    assert kwargs["body"]["values"][1][2] == 45.0       # row 1, column C (Total)
    assert kwargs["body"]["values"][0][3] == "Apples"
    assert kwargs["body"]["values"][1][3] == "Milk"
