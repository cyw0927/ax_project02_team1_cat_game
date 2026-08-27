import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Create a server/.env file first.")

SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE")
SANDBOX_TIMEOUT_SECONDS = os.getenv("SANDBOX_TIMEOUT_SECONDS")
SANDBOX_MEMORY = os.getenv("SANDBOX_MEMORY")
SANDBOX_CPUS = os.getenv("SANDBOX_CPUS")
SANDBOX_OUTPUT_BYTES = os.getenv("SANDBOX_OUTPUT_BYTES")
