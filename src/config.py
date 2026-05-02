import os
from pathlib import Path

# Load .env file
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip())

# LLM Configuration (Groq - cloud, fast, free)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Bot Configuration
BOT_HOST = os.getenv("BOT_HOST", "0.0.0.0")
BOT_PORT = int(os.getenv("BOT_PORT", "8080"))

# Metadata
TEAM_NAME = "Vera"
TEAM_MEMBERS = ["Mayank Maurya"]
MODEL_DESCRIPTION = "Groq Llama3-8B (cloud LLM, <2s response)"
APPROACH = "4-Context Framework: Category + Merchant + Trigger + Customer contexts fed to LLM with few-shot examples"
CONTACT_EMAIL = "hpmayankmaurya@gmail.com"
VERSION = "1.1.0"
