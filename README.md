# 📝 Telegram Quiz Extractor Bot

Yeh bot Telegram ke `@QuizBot` ke kisi bhi Quiz se:
- Question
- Options (A, B, C, D)
- Right Answer (✅ mark ke saath)
- Explanation (`Ex:-` ke saath)

extract karke seedha clean `.txt` file generate karke send karta hai.

---

## ⚙️ Railway Variables (Environment Variables)

Railway Dashboard me **Variables** tab me yeh 4 keys daalni hain:

| Variable Name | Value |
|---|---|
| `BOT_TOKEN` | `8618880598:AAEghYmMFTmJM3tkDSVUTr1z_8vHps4WJQQ` |
| `API_ID` | my.telegram.org se mila hua API ID |
| `API_HASH` | my.telegram.org se mila hua API HASH |
| `STRING_SESSION` | Telethon String Session jo account QuizBot solve karega |

---

## 🚀 How to Use Bot:
1. Apne Telegram bot par `/start` karein.
2. Quiz ka link paste karein:
   `https://t.me/QuizBot?quiz=xxxxx`
3. Bot 10-20 seconds me poora quiz solve karke `.txt` file send kar dega!
