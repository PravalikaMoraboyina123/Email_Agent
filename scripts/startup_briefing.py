"""
Startup Script for InboxPilot AI.
Executes automatically whenever the user boots or logs into their computer.
Fetches unread emails and reads out the spoken morning briefing immediately.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from agents.email_agent import agent
from services.voice_service import voice_service
from utils.logger import logger


def run_laptop_startup_routine():
    logger.info("=======================================================")
    logger.info("⚡ LAPTOP BOOT DETECTED: RUNNING INBOXPILOT STARTUP BRIEFING ⚡")
    logger.info("=======================================================")

    # Pause 6 seconds to allow Wi-Fi & sound drivers to initialize on login
    time.sleep(6)

    try:
        # 1. Spoken Welcome Greeting
        voice_service.speak("Welcome back. InboxPilot is active and scanning your emails now.", priority=True)

        # 2. Fetch & process new emails
        logger.info("Scanning inbox for new unread emails on boot...")
        scan_res = agent.process_new_emails()
        processed_count = scan_res.get('processed_count', 0)
        logger.info(f"Boot scan completed: {processed_count} new emails processed.")

        # 3. Run morning briefing routine & generate voice script
        briefing_res = agent.run_morning_routine()
        briefing_text = briefing_res.get("briefing_text", "")

        # 4. Speak the briefing aloud through speakers
        if briefing_text:
            logger.info("🔊 Speaking startup email briefing out loud...")
            voice_service.speak_sync(briefing_text)
        else:
            voice_service.speak_sync("You have no new urgent emails at this time. Have a great day!")

    except Exception as e:
        logger.error(f"Error during startup briefing execution: {e}")
        try:
            voice_service.speak_sync("InboxPilot is running in the background, but could not connect to network yet.")
        except Exception:
            pass


if __name__ == "__main__":
    run_laptop_startup_routine()
