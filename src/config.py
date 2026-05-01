# OpenAI Configuration
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Ollama Configuration (final fallback)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Bot Configuration
BOT_HOST = os.getenv("BOT_HOST", "0.0.0.0")
BOT_PORT = int(os.getenv("BOT_PORT", "8080"))

# Metadata
TEAM_NAME = "Vera"
TEAM_MEMBERS = ["Mayank Maurya"]
MODEL_DESCRIPTION = "3-tier LLM fallback: Gemini 2.0 Flash -> OpenAI GPT-3.5 Turbo -> Ollama Llama3"
APPROACH = "4-Context Framework: Category + Merchant + Trigger + Customer contexts fed to LLM with few-shot examples"
CONTACT_EMAIL = "mayank@example.com"
VERSION = "1.0.0"
