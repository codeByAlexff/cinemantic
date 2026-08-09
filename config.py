import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DSN = os.getenv("DSN")
MODEL = os.getenv("MODEL")
BATCH = os.getenv("BATCH")
TTL = os.getenv("TTL")