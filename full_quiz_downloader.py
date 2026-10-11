import asyncio
import re
import os
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPoll

# ==========================================
# TELEGRAM CREDENTIALS (my.telegram.org se milegi)
# ==========================================
API_ID = 12345678                 # Apna API ID yahan likhein (Numbers without quotes)
API_HASH = "your_api_hash_here"   # Apna API HASH yahan text me write karein

SESSION_NAME = "my_telegram_quiz_session"

async def download_quiz(quiz_link):
    # Match start payload like t_xxxxxxx
    match = re.search(r'(t_[A-Za-z0-9_-]+)', quiz_link)
    if not match:
        print("❌ Invalid Quiz Link! Target payload (t_xxxx) nahi mila.")
        return

    start_payload = match.group(1)
    quiz_bot = "@QuizBot"

    print("📡 Telegram Client Start Ho Raha Hai...")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    print(f"🚀 Sending command: /start {start_payload} to {quiz_bot}...")
    await client.send_message(quiz_bot, f"/start {start_payload}")

    print("⏳ Waiting for QuizBot response & Questions (10-15 seconds)...")
    await asyncio.sleep(5)

    questions_list = []

    # Iterate recent messages from QuizBot to grab questions
    async for message in client.iter_messages(quiz_bot, limit=50):
        if message.media and isinstance(message.media, MessageMediaPoll):
            poll = message.media.poll
            q_title = poll.question
            options = [ans.text for ans in poll.answers]
            
            questions_list.append({
                "question": q_title,
                "options": options
            })

    if not questions_list:
        print("ℹ️ QuizBot ne instant poll send nahi kiya. Tab aap Telegram me /start click karke questions start karein.")
        return

    # Save to TXT File
    output_filename = f"Quiz_{start_payload}.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("====================================\n")
        f.write(f"TELEGRAM QUIZ EXPORT ({len(questions_list)} Questions)\n")
        f.write("====================================\n\n")

        for idx, item in enumerate(reversed(questions_list), 1):
            f.write(f"Q{idx}. {item['question']}\n")
            for opt_idx, opt in enumerate(item['options']):
                option_letter = chr(65 + opt_idx)
                f.write(f"   ({option_letter}) {opt}\n")
            f.write("\n------------------------------------\n\n")

    print(f"✅ CONGRATULATIONS! Aapka poora Quiz `{output_filename}` file me save ho gaya hai!")

if __name__ == "__main__":
    # Test Link Here:
    user_quiz_link = input("Enter Quiz Link or payload (e.g., https://t.me/QuizBot?start=t_xxxx): ")
    asyncio.run(download_quiz(user_quiz_link))
