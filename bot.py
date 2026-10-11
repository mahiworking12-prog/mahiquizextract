import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPoll
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables (Railway me set honge)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8618880598:AAEghYmMFTmJM3tkDSVUTr1z_8vHps4WJQQ")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
STRING_SESSION = os.getenv("STRING_SESSION", "")

OPTION_LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Namaste! Main Quiz Extractor Bot hoon.**\n\n"
        "Aap mujhe kisi bhi Quiz ka share link bhej sakte hain:\n"
        "👉 Jaise: `https://t.me/QuizBot?quiz=xxxxx`\n\n"
        "Main saare Questions, Options, Correct Answer (✅) aur Explanation (Ex:-) "
        "extract karke aapko `.txt` file bana kar dunga!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def extract_quiz(quiz_param: str, status_msg) -> str:
    """
    Userbot session use karke @QuizBot se quiz extract karta hai.
    """
    if not API_ID or not API_HASH or not STRING_SESSION:
        raise ValueError("API_ID, API_HASH ya STRING_SESSION configured nahi hai! Kripya Railway me Environment Variables check karein.")

    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        raise ValueError("STRING_SESSION expire ya invalid ho gaya hai! Dubara session generate karein.")

    extracted_data = []
    
    try:
        # QuizBot ko start param bhejte hain
        quiz_bot = await client.get_entity("QuizBot")
        
        await client.send_message(quiz_bot, f"/start {quiz_param}")
        await asyncio.sleep(2)

        # Message check karte hain aur quiz start karte hain
        # QuizBot usually sends inline button or instructions
        # Check last message from QuizBot
        messages = await client.get_messages(quiz_bot, limit=3)
        quiz_title = "Quiz"
        for m in messages:
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        if "I'm ready" in btn.text or "Start" in btn.text or "start" in btn.text.lower():
                            await btn.click()
                            break

        await asyncio.sleep(2)

        # Ab questions aana shuru honge loop me
        q_count = 0
        last_poll_id = None
        consecutive_empty = 0

        while True:
            await asyncio.sleep(1.5)
            msgs = await client.get_messages(quiz_bot, limit=5)
            
            poll_found = False
            for msg in msgs:
                if msg.media and isinstance(msg.media, MessageMediaPoll):
                    poll = msg.media.poll
                    results = msg.media.results
                    
                    if poll.id == last_poll_id:
                        continue

                    # Naya question mila
                    poll_found = True
                    last_poll_id = poll.id
                    q_count += 1
                    consecutive_empty = 0

                    # Answer reveal karne ke liye first option vote karte hain
                    correct_option_index = None
                    try:
                        # Vote option 0
                        await client.send_vote(quiz_bot, msg.id, [b"0"])
                        await asyncio.sleep(1.2)
                        
                        # Updated poll results fetch karte hain
                        upd_msg = await client.get_messages(quiz_bot, ids=msg.id)
                        if upd_msg and upd_msg.media and upd_msg.media.results:
                            res = upd_msg.media.results
                            if res.results:
                                for idx, r in enumerate(res.results):
                                    if getattr(r, 'correct', False):
                                        correct_option_index = idx
                                        break
                    except Exception as e:
                        logger.warning(f"Voting error: {e}")

                    # Question text
                    q_text = poll.question

                    # Format Options
                    options_formatted = []
                    for idx, opt in enumerate(poll.answers):
                        letter = OPTION_LETTERS[idx] if idx < len(OPTION_LETTERS) else f"({idx+1})"
                        opt_text = opt.text
                        if correct_option_index is not None and idx == correct_option_index:
                            options_formatted.append(f"{letter}) {opt_text} ✅")
                        else:
                            options_formatted.append(f"{letter}) {opt_text}")

                    # Explanation text
                    explanation_text = ""
                    if hasattr(msg.media.results, 'solution') and msg.media.results.solution:
                        explanation_text = msg.media.results.solution

                    # Build Question block
                    block = f"Q.{q_count}. {q_text}\n"
                    block += "\n".join(options_formatted)
                    if explanation_text:
                        block += f"\nEx:- {explanation_text}"
                    
                    extracted_data.append(block)

                    # Update status to user periodically
                    if q_count % 5 == 0:
                        try:
                            await status_msg.edit_text(f"⏳ Extracting questions... ({q_count} questions processed)")
                        except Exception:
                            pass
                    break

            if not poll_found:
                consecutive_empty += 1
                # Check agar Quiz complete ho gaya ya result screen aa gayi
                for msg in msgs:
                    if msg.text and ("Quiz is finished" in msg.text or "You answered" in msg.text or "Result" in msg.text):
                        consecutive_empty = 10
                        break

            if consecutive_empty >= 5:
                # 7-8 seconds se koi naya question nahi aaya, quiz end maante hain
                break

    finally:
        await client.disconnect()

    # Final Text file content
    separator = "\n\n"
    final_output = separator.join(extracted_data)
    return final_output, q_count

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Quiz link extract karte hain
    quiz_param = None
    if "t.me/QuizBot?quiz=" in text:
        quiz_param = text.split("quiz=")[-1].split("&")[0].split()[0]
    elif text.startswith("http"):
        await update.message.reply_text("❌ Kripya valid QuizBot link bhejein.\nExample: `https://t.me/QuizBot?quiz=xxxxx`", parse_mode="Markdown")
        return
    else:
        await update.message.reply_text("Kripya mujhe QuizBot ka link bhejein, jaise:\n`https://t.me/QuizBot?quiz=mOkjGq1L`", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("🔄 Quiz extraction shuru ho raha hai... Kripya thoda intezaar karein.")

    try:
        content, count = await extract_quiz(quiz_param, status_msg)
        
        if count == 0:
            await status_msg.edit_text("❌ Quiz se questions extract nahi ho sake. Check karein ki link sahi hai ya nahi.")
            return

        # Save to temporary txt file
        file_path = f"quiz_{quiz_param}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        await status_msg.edit_text(f"✅ Success! Kul {count} questions extract ho gaye hain. File bheji ja rahi hai...")

        # Send file to user
        with open(file_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"quiz_questions.txt",
                caption=f"📝 **Quiz Extracted Successfully!**\nTotal Questions: {count}"
            )

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logger.error(f"Error extracting quiz: {e}", exc_info=True)
        await status_msg.edit_text(f"⚠️ Error occurred:\n`{str(e)}`", parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🤖 Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
