import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Constantes
MAX_RETRIES = 3
POLLING_INTERVAL = 5
POLLING_MAX_ATTEMPTS = 120
