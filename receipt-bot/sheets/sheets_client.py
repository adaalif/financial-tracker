import os
import asyncio
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID
from utils.logger import get_logger, track_performance

logger = get_logger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """Initializes and returns the Google Sheets API client seamlessly handling Credentials."""
    if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS):
        raise FileNotFoundError(f"Credentials file not found at {GOOGLE_SHEETS_CREDENTIALS}")
        
    creds = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    return service

@track_performance
async def append_to_sheets(rows_data: list[list]) -> bool:
    """Appends an array of rows to the next empty row in the active Google Sheet."""
    logger.info(f"Appending {len(rows_data)} receipt rows to Google Sheets...")
    
    # A sync execution block wrapper strictly dedicated to resolving the google SDK functions inside a native thread pool
    def _sync_append():
        service = get_sheets_service()
        sheet = service.spreadsheets()
        
        # Dynamically fetch the name of the first tab to prevent 'Unable to parse range' crashes on non-English locales or renamed tabs
        sheet_metadata = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
        first_sheet_name = sheet_metadata.get('sheets', [{}])[0].get('properties', {}).get('title', 'Sheet1')
        
        body = {
            'values': rows_data
        }
        
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{first_sheet_name}'!A:G", 
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        
        return result

    try:
        # Run blocking I/O SDK calls asynchronously safely outside the event loop
        result = await asyncio.to_thread(_sync_append)
        logger.info("Successfully added row to Google Sheets", updates=result.get("updates"))
        return True
    except Exception as e:
        logger.error("Failed to append to Google Sheets array", error=str(e), exc_info=True)
        raise
