# unkownsjetbot-public
Telegram bot that monitors aircraft over Iraq using the OpenSky Network API and sends automated alerts through Telegram. Includes configurable airspace monitoring, aircraft filtering, background checks, and live tracking links. Built with Python, HTTPX, and python-telegram-bot.
# Iraq Flight Tracker Bot ✈️

A Telegram bot that monitors aircraft flying over Iraq and sends automated notifications when selected aircraft are detected.

The project uses the OpenSky Network API for live aircraft state data and Telegram's Bot API for notifications.

## Features

- 🛫 Monitors aircraft within defined Iraqi airspace boundaries
- 🔎 Filters aircraft based on configured criteria
- 📱 Sends automated alerts through Telegram
- 🌐 Provides a Flightradar24 tracking link for detected aircraft
- ⏱️ Performs periodic background checks
- ❤️ Includes a lightweight health-check server for deployment environments
- 🔐 Uses environment variables to keep API credentials out of the source code

## Technologies

- Python
- python-telegram-bot
- HTTPX
- OpenSky Network API
- Telegram Bot API
- Flightradar24 links

## How It Works

1. The bot receives a `/start` command from a Telegram user.
2. The user's chat is registered for notifications.
3. The bot periodically queries the OpenSky Network API for aircraft within the configured Iraqi airspace boundaries.
4. Aircraft matching the configured criteria are identified.
5. The bot sends an alert containing available flight information and a tracking link.
6. Users can use `/stop` to pause notifications.

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the Telegram bot token

The Telegram bot token is loaded through an environment variable:

```text
TELEGRAM_TOKEN
```

Do not place the actual token directly inside the source code or commit it to GitHub.

### 3. Run the bot

```bash
python main.py
```

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Telegram Bot API token |
| `PORT` | Port used by the health-check server |

## Security

API credentials are intentionally excluded from this repository.

The public version of this project uses environment variables so that the Telegram bot token does not need to be stored in source code.

If deploying the bot to a hosting service, the token should be added through the platform's secret/environment-variable settings.

## Project Background

I originally developed an earlier version of this flight-tracking bot in 2024.

In 2026, I rebuilt the project from scratch after losing access to the original source code. The current repository represents the rebuilt and improved version of the project.

The rebuild also provided an opportunity to improve the project's structure, security practices, error handling, and API integration.

## Commands

| Command | Purpose |
|---|---|
| `/start` | Start receiving flight alerts |
| `/stop` | Stop receiving flight alerts |

## Disclaimer

This project is an independent software project created for educational and portfolio purposes.

Aircraft information is obtained from the OpenSky Network and may be incomplete, delayed, or unavailable depending on the data source.

## Author

**UnknownVariabl**

GitHub: https://github.com/UnknownVariabl
