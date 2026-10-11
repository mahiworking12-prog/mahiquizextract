import os
import io
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    PollAnswerHandler,
    MessageHandler,
    filters,
    ContextTypes
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8618880598:AAEghYmMFTmJM3tkDSVUTr1z_8vHps4WJQQ")

OPTION_LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

# In-memory storage: chat_id -> list of questions
# Ek question ka structure:
# {
#   "poll_id": str,
#   "question": str,
#   "options": [{"text": str, "voter_count": int}],
#   "correct_option_id": int,
#   "explanation": str
# }
ACTIVE_QUIZZES = {}
POLL_ID_MAP = {}  # poll_id -> (chat_id, question_index)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 **Namaste! Main Quiz Extractor Bot hoon.**\n\n"
        "Bina kisi API ID/HASH ke use karne ka tareeqa:\n\n"
        "1️⃣ Ek private group banayein aur mujhe us group me add karein (Admin permissions dein).\n"
        "2️⃣ Group me `/record` command bhejein (Recording shuru karne ke liye).\n"
        "3️⃣ @QuizBot ka quiz us group me 'Start quiz in group' karke chalayein.\n"
        "4️⃣ Har question ka answer dein taaki right answer aur explanation reveal ho jaye.\n"
        "5️⃣ Quiz khatam hone par group me `/done` command bhejein.\n\n"
        "📁 Main turant saare questions ki formatted `.txt` file bhej dunga!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def record_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ACTIVE_QUIZZES[chat_id] = []
    await update.message.reply_text(
        "🔴 **Recording ON ho gayi hai!**\n\n"
        "Ab aap @QuizBot ka quiz start kijiye. Har question aur answer automatic note ho jayega.\n"
        "Quiz khatam hone par `/done` bhejein.",
        parse_mode="Markdown"
    )

async def poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab group me koi Poll/Quiz message aata hai ya update hota hai"""
    poll = update.poll
    if not poll:
        return

    poll_id = poll.id
    
    # Check if this poll belongs to any tracked chat
    if poll_id in POLL_ID_MAP:
        chat_id, q_idx = POLL_ID_MAP[poll_id]
        if chat_id in ACTIVE_QUIZZES and q_idx < len(ACTIVE_QUIZZES[chat_id]):
            q_data = ACTIVE_QUIZZES[chat_id][q_idx]
            # Update correct option agar reveal ho gaya
            if poll.correct_option_id is not None:
                q_data["correct_option_id"] = poll.correct_option_id
            if poll.explanation:
                q_data["explanation"] = poll.explanation
            return

async def message_with_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab group me naya poll/quiz post hota hai"""
    chat_id = update.effective_chat.id
    if chat_id not in ACTIVE_QUIZZES:
        return

    msg = update.effective_message
    if not msg.poll:
        return

    poll = msg.poll
    
    options = []
    for opt in poll.options:
        options.append(opt.text)

    q_data = {
        "poll_id": poll.id,
        "question": poll.question,
        "options": options,
        "correct_option_id": poll.correct_option_id,
        "explanation": poll.explanation or ""
    }

    q_index = len(ACTIVE_QUIZZES[chat_id])
    ACTIVE_QUIZZES[chat_id].append(q_data)
    POLL_ID_MAP[poll.id] = (chat_id, q_index)

async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ACTIVE_QUIZZES or len(ACTIVE_QUIZZES[chat_id]) == 0:
        await update.message.reply_text("⚠️ Abhi tak koi question capture nahi hua! Pehle `/record` karein aur quiz play karein.", parse_mode="Markdown")
        return

    questions = ACTIVE_QUIZZES[chat_id]
    total = len(questions)

    # Text format banate hain:
    formatted_blocks = []
    for idx, q in enumerate(questions, start=1):
        lines = []
        lines.append(f"Q.{idx}. {q['question']}")

        correct_id = q.get("correct_option_id")
        for o_idx, opt_text in enumerate(q["options"]):
            letter = OPTION_LETTERS[o_idx] if o_idx < len(OPTION_LETTERS) else f"({o_idx+1})"
            if correct_id is not None and o_idx == correct_id:
                lines.append(f"{letter}) {opt_text} ✅")
            else:
                lines.append(f"{letter}) {opt_text}")

        explanation = q.get("explanation")
        if explanation:
            lines.append(f"Ex:- {explanation}")

        formatted_blocks.append("\n".join(lines))

    final_text = "\n\n".join(formatted_blocks)

    # Memory file stream banate hain
    file_bytes = io.BytesIO(final_text.encode("utf-8"))
    file_bytes.name = f"quiz_questions.txt"

    await update.message.reply_document(
        document=file_bytes,
        filename=f"quiz_questions.txt",
        caption=f"✅ **Quiz Successfully Extracted!**\nTotal Questions: {total}"
    )

    # Reset
    ACTIVE_QUIZZES[chat_id] = []

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("record", record_cmd))
    app.add_handler(CommandHandler("done", done_cmd))
    
    # Message handlers
    app.add_handler(MessageHandler(filters.POLL, message_with_poll))
    app.add_handler(PollAnswerHandler(poll_handler))

    print("🤖 Bot is starting (Simple No-API Mode)...")
    app.run_polling()

if __name__ == "__main__":
    main()
