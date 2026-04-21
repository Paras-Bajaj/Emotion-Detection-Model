
import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

load_dotenv()

TOKEN_MAX_AGE_SECONDS = 2 * 60 * 60


def get_secret_key():
    return os.getenv("SECRET_KEY", "change-me-in-backend-env")