import os
import json
import asyncio
import traceback
import discord
from discord.ext import commands
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

# 환경 변수 로드
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")
FIREBASE_URL = os.getenv("FIREBASE_DB_URL")
FIREBASE_CREDS_RAW = os.getenv("FIREBASE_CREDS_JSON")

if not TOKEN:
    raise SystemExit("❌ DISCORD_TOKEN이 설정되지 않았습니다.")

# --- Firebase Railway 맞춤형 연결 ---
try:
    # 1. Railway 환경변수에 값이 들어있는지 가장 먼저 확인
    creds_raw = FIREBASE_CREDS_RAW.strip() if FIREBASE_CREDS_RAW else None
    
    if creds_raw:
        print("💡 Railway 환경 변수에서 Firebase 키를 로드합니다.")
        creds_dict = json.loads(creds_raw)
        cred = credentials.Certificate(creds_dict)
    else:
        # 2. 환경변수가 없으면 로컬 테스트용 파일 로드
        print("💡 로컬 파일에서 Firebase 키를 로드합니다.")
        current_dir = os.path.dirname(__file__)
        cred_path = os.path.join(current_dir, "firebase_creds.json")
        cred = credentials.Certificate(cred_path)
    
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_URL
    })
    print("🔥 Firebase Realtime Database 연결 성공 (Railway)!")
except Exception as e:
    raise SystemExit(f"❌ Firebase 연결 실패: {e}")

# --- 디스코드 봇 설정 ---
INTENTS = discord.Intents.default()
INTENTS.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=INTENTS, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ 야구 봇 로그인 완료: {bot.user} (ID: {bot.user.id})")

@bot.event
async def load_cogs():
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
