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

# chat_id -> list of questions
ACTIVE_QUIZZES = {}
POLL_ID_MAP = {}

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 **Quiz Extractor Bot Ready!**\n\n"
        "**Kaise use karein:**\n"
        "1. Ek private group banayein aur mujhe Admin banayein.\n"
        "2. Kisi bhi quiz ko us group me 'Start quiz in group' karke chalayein.\n"
        "3. Quiz khatam hone par group me `/done` likhein.\n"
        "4. Main turant saare questions ki formatted `.txt` file bhej dunga!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def record_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ACTIVE_QUIZZES[chat_id] = []
    await update.message.reply_text(
        "🔴 **Recording Start!**\nAb aap QuizBot ka quiz chalayein. Khatam hone par `/done` bhejein.",
        parse_mode="Markdown"
    )

async def message_with_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab naya question aayega"""
    chat_id = update.effective_chat.id
    if chat_id not in ACTIVE_QUIZZES:
        ACTIVE_QUIZZES[chat_id] = []

    msg = update.effective_message
    if not msg.poll:
        return

    poll = msg.poll
    options = [opt.text for opt in poll.options]

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

async def poll_update_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab poll ka right answer reveal hoga"""
    poll = update.poll
    if not poll:
        return

    poll_id = poll.id
    if poll_id in POLL_ID_MAP:
        chat_id, q_idx = POLL_ID_MAP[poll_id]
        if chat_id in ACTIVE_QUIZZES and q_idx < len(ACTIVE_QUIZZES[chat_id]):
            q_data = ACTIVE_QUIZZES[chat_id][q_idx]
            if poll.correct_option_id is not None:
                q_data["correct_option_id"] = poll.correct_option_id
            if poll.explanation:
                q_data["explanation"] = poll.explanation

async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ACTIVE_QUIZZES or len(ACTIVE_QUIZZES[chat_id]) == 0:
        await update.message.reply_text("⚠️ Abhi tak koi question capture nahi hua! Quiz play karne ke baad `/done` bhejein.")
        return

    questions = ACTIVE_QUIZZES[chat_id]
    total = len(questions)

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

    file_bytes = io.BytesIO(final_text.encode("utf-8"))
    file_bytes.name = "quiz_questions.txt"

    await update.message.reply_document(
        document=file_bytes,
        filename="quiz_questions.txt",
        caption=f"📝 **Quiz Successfully Extracted!**\nTotal Questions: {total}"
    )

    ACTIVE_QUIZZES[chat_id] = []

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("record", record_cmd))
    app.add_handler(CommandHandler("done", done_cmd))
    
    app.add_handler(MessageHandler(filters.POLL, message_with_poll))
    app.add_handler(PollAnswerHandler(poll_update_handler))

    print("🤖 Bot is starting on Railway...")
    app.run_polling()

if __name__ == "__main__":
    main()
