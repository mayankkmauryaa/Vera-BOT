# Changelog

## [1.2.0] - 2026-05-03

### Fixed (Critical Bot Evaluation Issues)
- **STOP handling**: Now returns `action='end'` immediately when user says "stop", "no", "not interested" (fixes eval failure)
- **Generic replies**: Replaced "Got it, let me process that for you." with contextual, personalized responses
- **Pattern matching**: Added more intent patterns ("yes", "sure", "ok", "yep", "yeah", etc.)
- **Hostile detection**: Expanded patterns to catch "stop", "no thanks", "don't message", "unsubscribe"

### Added
- **Contextual replies**: Bot now generates specific responses based on message content (booking, X-ray, help, etc.)
- **Merchant personalization**: Replies now include merchant name from context
- **Conversation context**: `ConversationManager` now stores and uses merchant/customer context for better replies
- **`.env.example`**: Template for environment variables (`.env` is gitignored)
- **`.env` support**: API keys now loaded from environment variables, not hardcoded

### Changed
- **Project reorganization**: Moved files from root to `challenge zip extracted/` for better organization
- **Deployment**: Updated to use Render with environment variables for API keys
- **Documentation**: Updated README with current evaluation status, fixes, and setup instructions

### Security
- **Removed hardcoded API key**: Moved `GROQ_API_KEY` from code to `.env` file (gitignored)
- **Git history rewritten**: Removed exposed API key from commit history

---

## [1.1.0] - 2026-05-03

### Added
- Initial submission to magicpin AI Challenge
- 4-Context Framework implementation (Category + Merchant + Trigger + Customer)
- Support for 5 categories: dentists, gyms, pharmacies, restaurants, salons
- Groq LLM integration (llama-3.1-8b-instant)
- Auto-reply detection and handling
- Few-shot examples for better prompt engineering

### Known Issues (from eval score 15/100)
- STOP handling returns `action=send` instead of `action=end`
- Generic fallback reply: "Got it, let me process that for you."
- Low engagement compulsion (1/10)
- Low decision quality (2/10)
- Low specificity (2/10)
