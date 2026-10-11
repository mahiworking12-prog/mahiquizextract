import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

print("==================================================")
print("🔑 TELETHON STRING SESSION GENERATOR")
print("==================================================")

api_id = input("Apna API_ID enter karein: ").strip()
api_hash = input("Apna API_HASH enter karein: ").strip()

async def main():
    async with TelegramClient(StringSession(), int(api_id), api_hash) as client:
        print("\n✅ Session successfully create ho gaya hai!")
        print("\n👇 Yeh rahi aapki STRING_SESSION (ise copy karke Railway me daalein):\n")
        print(client.session.save())
        print("\n⚠️ Is session string ko kisi ke saath share mat kijiye ga.")

if __name__ == "__main__":
    asyncio.run(main())
