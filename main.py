import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread

# [추가] Koyeb Health Check를 위한 웹 서버 설정
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    # Koyeb이 사용할 포트를 8000으로 설정합니다.
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 봇 설정 부분
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
APEX_API_KEY = os.environ.get("APEX_API_KEY")

MAP_NAMES = {
    "World's Edge": "세상의 끝",
    "Storm Point": "스톰 포인트",
    "Broken Moon": "브로큰 문",
    "Kings Canyon": "킹스 캐년",
    "Olympus": "올림푸스",
    "District": "디스트릭트",
    "E-District": "E-디스트릭트"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_ranked_map():
    try:
        url = f"https://api.mozambiquehe.re/maprotation?version=2&auth={APEX_API_KEY}"
        res = requests.get(url).json()
        ranked_info = res.get('ranked', {}).get('current', {})
        eng_map = ranked_info.get('map', '정보 없음')
        kor_map = MAP_NAMES.get(eng_map, eng_map)
        remaining = ranked_info.get('remainingTimer', '??:??')
        return kor_map, remaining
    except:
        return None, None

@tasks.loop(hours=6)
async def update_presence():
    kor_map, _ = get_ranked_map()
    if kor_map and kor_map != '정보 없음':
        await bot.change_presence(activity=discord.Game(name=f"랭크 맵: {kor_map}"))

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 로그인 성공!")
    if not update_presence.is_running():
        update_presence.start()

@bot.command(name="랭크")
async def rank_info(ctx):
    kor_map, remaining = get_ranked_map()
    if kor_map and kor_map != '정보 없음':
        await ctx.send(f"🏆 **현재 랭크 맵**: {kor_map}\n⏰ **다음 로테이션까지**: {remaining}")
    else:
        await ctx.send("❌ 정보를 불러올 수 없습니다.")

# [수정] 실행 부분에 웹 서버 시작 추가
if __name__ == "__main__":
    keep_alive()  # 웹 서버를 먼저 띄우고
    bot.run(DISCORD_TOKEN) # 봇을 실행합니다.
