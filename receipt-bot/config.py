import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env_var(name: str, required: bool = True) -> str:
    """
    Retrieves an environment variable.
    Raises an error if required=True and the variable is not set.
    """
    value = os.getenv(name)
    if not value and required:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value or ""
GROQ_API_KEY = get_env_var("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = get_env_var("TELEGRAM_BOT_TOKEN", required=False)
GOOGLE_SHEETS_CREDENTIALS = get_env_var("GOOGLE_SHEETS_CREDENTIALS", required=False)
SPREADSHEET_ID = get_env_var("SPREADSHEET_ID", required=False)
