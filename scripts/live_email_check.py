"""
Live Email Scanner & Dual-Device Voice Briefing Executor.
Scans Gmail unread emails, speaks briefing aloud on laptop speakers,
and sends push alerts & voice briefings to mobile phone (ntfy / Telegram).
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from agents.email_agent import agent
from services.voice_service import voice_service
from services.push_service import push_service
from services.telegram_service import telegram_service
from utils.logger import logger


def run_live_dual_device_check():
    print("\n=======================================================")
    print("🚀 RUNNING LIVE GMAIL SCAN & DUAL-DEVICE VOICE BRIEFING")
    print("=======================================================\n")

    # 1. Scan Gmail inbox for unread emails
    print("📧 Step 1: Scanning Gmail inbox for unread emails...")
    scan_res = agent.process_new_emails()
    print(f"   -> Scan Result: {scan_res.get('processed_count', 0)} new emails processed.\n")

    # 2. Run morning briefing routine
    print("🌅 Step 2: Generating Morning Email Briefing script...")
    briefing_res = agent.run_morning_routine()
    briefing_text = briefing_res.get("briefing_text", "")

    print("\n-------------------------------------------------------")
    print("🗣️ SPOKEN BRIEFING SCRIPT:")
    print(f"\"{briefing_text}\"")
    print("-------------------------------------------------------\n")

    # 3. Send Mobile Push Notification to Phone
    print("📱 Step 3: Sending push notification to your phone (ntfy.sh/inbox_alerts)...")
    push_success = push_service.send_push_notification(
        title="🌅 Live Email Briefing",
        message=briefing_text,
        priority="high",
        tags="email,loudspeaker"
    )
    if push_success:
        print("   ✅ Delivered to your phone app (ntfy)!")
    else:
        print("   ⚠️ Mobile push failed or skipped.")

    # 4. Speak Briefing out loud on Laptop Speakers
    print("\n🔊 Step 4: Reading briefing out loud through LAPTOP SPEAKERS...")
    if briefing_text:
        voice_service.speak_sync(briefing_text)
        print("   ✅ Laptop audio playback finished!")

    print("\n=======================================================")
    print("✅ DUAL-DEVICE EMAIL CHECK COMPLETED SUCCESSFULLY!")
    print("=======================================================\n")


if __name__ == "__main__":
    run_live_dual_device_check()
