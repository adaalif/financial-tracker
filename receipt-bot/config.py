import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env_var(name: str) -> str:
    """
    Retrieves an environment variable and raises an error if it is not set.
    This ensures the bot fails fast on startup if configuration is invalid.
    """
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value

# Required Configuration
TELEGRAM_BOT_TOKEN = get_env_var("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = get_env_var("GROQ_API_KEY")
GOOGLE_SHEETS_CREDENTIALS = get_env_var("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = get_env_var("SPREADSHEET_ID")
