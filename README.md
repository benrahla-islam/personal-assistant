# Personal Assistant v1

A LangChain-powered personal assistant with Telegram integration and web scraping capabilities.

## Features

- **LangChain Agent**: Intelligent assistant powered by LangChain framework
- **Telegram Bot**: Interactive bot interface for user communication
- **Telegram Scraper**: Advanced channel scraping with Telethon
- **Tool Registry**: Extensible tool system for adding new capabilities

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "personal assistant v1"
```

2. Install dependencies with uv:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Usage

### Running the Agent

Test the LangChain agent:
```bash
uv run test_agent.py
```

### Running the Telegram Bot

Start the Telegram bot:
```bash
uv run main.py
```

### Using the Telegram Scraper

Run the interactive scraper example:
```bash
uv run telegram_scraper/example_usage.py
```

## Project Structure

```
├── agent/                  # LangChain agent implementation
│   ├── main.py            # Main agent logic
│   ├── tool_registry.py   # Tool management
│   └── tools/             # Available tools
├── telegram_bot/          # Telegram bot implementation
├── telegram_scraper/      # Telegram channel scraping
├── main.py               # Main entry point
├── test_agent.py         # Agent testing script
└── pyproject.toml        # Project dependencies
```

## Development

### Adding New Tools

1. Create a new tool in `agent/tools/`
2. Register the tool in `agent/tool_registry.py`
3. Test with `uv run test_agent.py`

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black .
uv run isort .
```

## Environment Variables

Required environment variables:
- `OPENAI_API_KEY`: OpenAI API key for LangChain
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_API_ID`: Telegram API ID for scraping
- `TELEGRAM_API_HASH`: Telegram API hash for scraping

## License

MIT License
