import os
import logging
import http.server
import threading

import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

OPENSKY_API_URL = "https://opensky-network.org/api/states/all"

IRAQ_BOUNDS = {
    "lamin": 29.0,
    "lamax": 37.5,
    "lomin": 38.5,
    "lomax": 48.5,
}

TARGET_COUNTRIES = {
    "united states",
    "turkey",
    "united kingdom",
    "germany",
    "france",
    "italy",
    "spain",
    "netherlands",
    "belgium",
    "switzerland",
    "sweden",
    "norway",
    "denmark",
    "poland",
    "greece",
    "ireland",
    "austria",
    "portugal",
    "finland",
    "czech republic",
}


# Chats that have enabled notifications
active_chats = set()

# ICAO24 identifiers of aircraft already alerted about
seen_flights = set()


# --------------------------------------------------
# Health Check Server
# --------------------------------------------------

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive")

    def log_message(self, format, *args):
        # Keep health-check requests out of the logs
        return


def run_health_check():
    port = int(os.environ.get("PORT", 10000))

    server = http.server.HTTPServer(
        ("0.0.0.0", port),
        HealthCheckHandler,
    )

    logger.info("Health check server running on port %s", port)

    server.serve_forever()


# --------------------------------------------------
# Telegram Commands
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat is None or update.message is None:
        return

    chat_id = update.effective_chat.id

    active_chats.add(chat_id)

    await update.message.reply_text(
        "👋 *Iraq Flight Tracker Bot Active!*\n\n"
        "I am now scanning Iraq's airspace 24/7.",
        parse_mode="Markdown",
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat is None or update.message is None:
        return

    chat_id = update.effective_chat.id

    active_chats.discard(chat_id)

    await update.message.reply_text(
        "🔇 Notifications paused."
    )


# --------------------------------------------------
# Flight Monitoring
# --------------------------------------------------

async def check_flights_job(context: ContextTypes.DEFAULT_TYPE):

    if not active_chats:
        return

    current_flights = set()

    try:

        async with httpx.AsyncClient(timeout=15) as client:

            response = await client.get(
                OPENSKY_API_URL,
                params=IRAQ_BOUNDS,
            )

            response.raise_for_status()

            data = response.json()

        states = data.get("states")

        if not states:
            logger.info("No aircraft currently detected.")
            return

        for flight in states:

            # OpenSky state vectors contain multiple fields.
            # Make sure the response contains the fields we need.
            if len(flight) < 10:
                continue

            # OpenSky state vector fields:
            # 0 = ICAO24
            # 1 = Callsign
            # 2 = Origin country
            # 7 = Barometric altitude (meters)
            # 9 = Velocity (m/s)

            icao24 = flight[0]

            callsign = (
                flight[1].strip()
                if flight[1]
                else "UNKNOWN"
            )

            origin_country = (
                flight[2].strip()
                if flight[2]
                else "Unknown"
            )

            altitude = flight[7]
            velocity = flight[9]

            if not icao24:
                continue

            if not callsign or callsign == "UNKNOWN":
                continue

            current_flights.add(icao24)

            # Check whether this aircraft belongs to one
            # of the selected target countries.
            if origin_country.lower() not in TARGET_COUNTRIES:
                continue

            # Don't repeatedly alert for the same aircraft
            # while it remains inside the monitored area.
            if icao24 in seen_flights:
                continue

            seen_flights.add(icao24)

            # Convert OpenSky metric units
            # meters -> feet
            # meters/second -> miles/hour

            alt_ft = (
                int(altitude * 3.28084)
                if altitude is not None
                else "Unknown"
            )

            speed_mph = (
                int(velocity * 2.23694)
                if velocity is not None
                else "Unknown"
            )

            # FlightRadar24 tracking URL
            fr24_url = (
                "https://www.flightradar24.com/data/flights/"
                f"{callsign.lower()}"
            )

            alert_msg = (
                "🚨 *Target Aircraft Detected Over Iraq!*\n\n"
                f"✈️ *Callsign:* `{callsign}`\n"
                f"🌍 *Aircraft Country:* {origin_country}\n"
                f"📏 *Altitude:* {alt_ft} ft\n"
                f"🚀 *Speed:* {speed_mph} mph\n\n"
                f"🌐 [Track Live on Flightradar24]({fr24_url})"
            )

            # Send the alert to every active subscriber.
            for chat_id in list(active_chats):

                try:

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=alert_msg,
                        parse_mode="Markdown",
                        disable_web_page_preview=False,
                    )

                except Exception as e:

                    logger.error(
                        "Failed to send alert to chat %s: %s",
                        chat_id,
                        e,
                    )

        # Aircraft that are no longer detected can trigger
        # another alert if they return later.
        seen_flights.intersection_update(current_flights)

    except httpx.HTTPError as e:

        logger.error(
            "OpenSky HTTP error: %s",
            e,
        )

    except Exception as e:

        logger.exception(
            "Unexpected error while checking flights: %s",
            e,
        )


# --------------------------------------------------
# Main Application
# --------------------------------------------------

def main():

    # Start health-check server in the background.
    threading.Thread(
        target=run_health_check,
        daemon=True,
    ).start()

    # Read Telegram token from environment.
    BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")

    if not BOT_TOKEN:

        logger.error(
            "CRITICAL ERROR: 'TELEGRAM_TOKEN' "
            "environment variable not found."
        )

        print(
            "\n❌ Error: Please set the "
            "TELEGRAM_TOKEN environment variable.\n"
        )

        return

    # Create Telegram application.
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Telegram commands.
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("stop", stop)
    )

    # Check aircraft every 120 seconds.
    job_queue = app.job_queue

    job_queue.run_repeating(
        check_flights_job,
        interval=120,
        first=5,
    )

    logger.info("Iraq Flight Tracker Bot started.")

    # Start Telegram polling.
    app.run_polling()


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":
    main()

os.environ.get("TELEGRAM_TOKEN")
