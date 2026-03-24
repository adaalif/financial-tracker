# Receipt Processor Bot

A Telegram bot that reads receipt images, extracts the data using AI, and saves it directly to a Google Sheet.

## Features

- Telegram integration: Send a photo of a receipt to the bot via chat.
- AI extraction: Uses the Groq Vision API to read the receipt and extract the merchant, date, total, items, and category.
- Google Sheets sync: Automatically appends the extracted data as a new row in your spreadsheet.
- Fallback system: If the AI fails to format the data correctly, the bot uses a text extraction backup method.
- Containerized: Ready to run in production using Docker Compose.

## Setup Instructions

### 1. Requirements

- A Telegram Bot Token (from BotFather on Telegram)
- A Groq API Key
- A Google Cloud Service Account (for writing to Google Sheets)

### 2. Environment Variables

Copy the `.env.example` file to a new file named `.env` and fill in your specific keys:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_token
GROQ_API_KEY=your_groq_key
GOOGLE_SHEETS_CREDENTIALS=credentials.json
SPREADSHEET_ID=your_google_sheet_id_here
```

### 3. Google Sheets Setup

1. Place your Google Service Account key file in the main folder and make sure it is named `credentials.json`.
2. Open your Google Sheet in a web browser.
3. Click "Share" and share the document with the `client_email` address found inside your `credentials.json` file. Give it Editor access.
4. Ensure the first tab of your Google Sheet has exactly five columns, in this order:
   Merchant | Date | Total | Items | Category

## Running the Bot

### Using Docker (Recommended)

To run the bot in the background using Docker Compose, run this command in your terminal:

```bash
docker-compose up -d --build
```

### Running Locally

This project uses `uv` for dependency management.

1. Install uv installed on your system.
2. Run the bot directly:

```bash
uv run main.py
```

## Running Tests

To run the unit tests and verify the code is working:

```bash
uv run pytest
```
