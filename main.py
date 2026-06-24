import os
import asyncio
import traceback
import discord
from discord.ext import commands
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

# .env 로드
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")
FIREBASE_URL = os.getenv("FIREBASE_DB_URL")

if not TOKEN:
    raise SystemExit("❌ DISCORD_TOKEN이 설정되지 않았습니다.")

# --- Firebase 초기화 ---
try:
    cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "firebase_creds.json"))
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_URL
    })
    print("🔥 Firebase 실시간 데이터베이스 연결 성공!")
except Exception as e:
    raise SystemExit(f"❌ Firebase 초기화 실패: {e}")

# 봇 생성
INTENTS = discord.Intents.default()
INTENTS.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=INTENTS, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ 야구 기록 봇 로그인 완료: {bot.user} (ID: {bot.user.id})")

@bot.event
async def load_cogs():
    # 야구 전용 코그 로드
    try:
        await bot.load_extension("cogs.baseball")
        print("Loaded cog: cogs.baseball")
    except Exception as e:
        print(f"Failed to load cogs.baseball: {e}")
        traceback.print_exc()

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 봇이 종료되었습니다.")
