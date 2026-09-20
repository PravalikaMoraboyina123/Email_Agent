"""
InboxPilot AI Live Interactive Demonstrator Script.
Runs a live demonstration showing email categorization, priority scoring, audio alerts, and briefings.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from database.session import SessionLocal
from models.domain import EmailRecord, UserPreference, RoutineLog
from agents.email_agent import agent
from services.learning_service import learning_service


def run_demo():
    print("\n=======================================================")
    print("      🤖 INBEXPILOT AI - LIVE SYSTEM DEMONSTRATION      ")
    print("=======================================================\n")

    db = SessionLocal()

    try:
        # 1. Fetch Processed Email Summary
        total = db.query(EmailRecord).count()
        important = db.query(EmailRecord).filter(EmailRecord.is_important == True).count()

        print(f"📊 SUMMARY STATS:")
        print(f"   • Total Emails Analyzed: {total}")
        print(f"   • High Priority / Important: {important}\n")

        # 2. Display Sample Categorized Emails
        print("📧 PROCESSED EMAILS & AI ANALYSIS (SAMPLE):")
        records = db.query(EmailRecord).order_by(EmailRecord.id.desc()).limit(5).all()

        for idx, rec in enumerate(records, 1):
            print(f"\n--- [{idx}] {rec.subject[:50]} ---")
            print(f"  • Sender: {rec.sender}")
            print(f"  • Category: {rec.category}")
            print(f"  • Priority Score: {rec.priority_score}/100 | Opportunity Score: {rec.opportunity_score}/100")
            print(f"  • Summary: {rec.summary}")
            print(f"  • Recommended Action: {rec.recommended_action}")

        # 3. Simulate Morning Routine (6:00 AM Briefing)
        print("\n\n🌅 TESTING MORNING ROUTINE (6:00 AM BRIEFING)...")
        morning_result = agent.run_morning_routine()
        print(f"\n🗣️ SPOKEN MORNING BRIEFING SCRIPT:\n\"{morning_result.get('briefing_text')}\"")

        # 4. Simulate Evening Routine (9:00 PM Review)
        print("\n\n🌙 TESTING EVENING ROUTINE (9:00 PM BRIEFING)...")
        evening_result = agent.run_evening_routine()
        print(f"\n🗣️ SPOKEN EVENING BRIEFING SCRIPT:\n\"{evening_result.get('briefing_text')}\"")

        # Wait for audio playback to finish playing through speakers
        print("\n🔊 Playing audio speech aloud through speakers...")
        from services.voice_service import voice_service
        voice_service.wait_until_done()

        # 5. Demonstrate Adaptive Learning Engine
        print("\n\n🧠 DEMONSTRATING ADAPTIVE LEARNING ENGINE:")
        if records:
            test_email = records[0]
            print(f"   Simulating user clicking 'Applied' on email ID {test_email.id} ('{test_email.subject[:30]}')...")
            learning_service.record_user_interaction(db, test_email.id, "Applied")

            # Check learned preferences
            prefs = db.query(UserPreference).all()
            print(f"   Updated Learned Preferences Weight Modifiers:")
            for p in prefs:
                print(f"   • {p.key_type.title()} [{p.key_value}]: Modifier {p.priority_modifier:+.1f} (Opens: {p.open_count}, Ignores: {p.ignore_count})")

        print("\n=======================================================")
        print("      ✅ DEMONSTRATION COMPLETE - AGENT RUNNING 24/7    ")
        print("=======================================================\n")

    finally:
        db.close()


if __name__ == "__main__":
    run_demo()
