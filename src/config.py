# Ollama Configuration (only LLM used)
import os
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Bot Configuration
BOT_HOST = os.getenv("BOT_HOST", "0.0.0.0")
BOT_PORT = int(os.getenv("BOT_PORT", "8080"))

# Metadata
TEAM_NAME = "Vera"
TEAM_MEMBERS = ["Mayank Maurya"]
MODEL_DESCRIPTION = "Ollama Llama3 (local LLM only)"
APPROACH = "4-Context Framework: Category + Merchant + Trigger + Customer contexts fed to LLM with few-shot examples"
CONTACT_EMAIL = "mayank@example.com"
VERSION = "1.0.0"
