import logging
import os
import re
import asyncio
import nest_asyncio
from flask import Flask, request, jsonify
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPoll

nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Telegram API credentials (replace with your credentials or use environment variables)
API_ID = int(os.environ.get("TELEGRAM_API_ID", "1234567"))  
API_HASH = os.environ.get("TELEGRAM_API_HASH", "your_api_hash_here")
SESSION_NAME = "quiz_extractor_session"

# Initialize Telethon Client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def extract_quiz_by_link(quiz_link):
    """
    Connects to Telegram, sends start command with quiz payload to @QuizBot,
    receives quiz questions, and formats them into a clean text / HTML list.
    """
    await client.start()
    
    # Extract quiz start payload (e.g. from t.me/QuizBot?start=t_xxxx or just t_xxxx)
    match = re.search(r'(t_[A-Za-z0-9_-]+)', quiz_link)
    if not match:
        return {"error": "Invalid Quiz Link format. Expected link containing start payload like t_xxxx"}
    
    start_payload = match.group(1)
    quiz_bot = "@QuizBot"
    
    logger.info(f"Sending /start {start_payload} to {quiz_bot}...")
    
    # Send start command to QuizBot
    sent_msg = await client.send_message(quiz_bot, f"/start {start_payload}")
    
    # Wait briefly for responses from QuizBot
    await asyncio.sleep(2)
    
    questions = []
    
    # Listen to recent messages from QuizBot
    async for message in client.iter_messages(quiz_bot, limit=10):
        if message.media and isinstance(message.media, MessageMediaPoll):
            poll = message.media.poll
            question_text = poll.question
            options = [opt.text for opt in poll.answers]
            
            questions.append({
                "question": question_text,
                "options": options
            })
            
    if not questions:
        return {
            "status": "info",
            "message": "Quiz command triggered. Please click 'Ready' or start the quiz via Telegram if prompted.",
            "quiz_payload": start_payload
        }

    return {
        "status": "success",
        "total_questions": len(questions),
        "questions": questions
    }

@app.route('/extract-quiz', methods=['POST'])
def extract_quiz():
    data = request.json or {}
    quiz_link = data.get("quiz_link", "")
    
    if not quiz_link:
        return jsonify({"error": "quiz_link parameter is required"}), 400
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(extract_quiz_by_link(quiz_link))
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
