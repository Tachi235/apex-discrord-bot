import discord
from discord.ext import tasks, commands
import requests
from flask import Flask
from threading import Thread
import os

# 1. 웹 서버 설정 (Koyeb 유지용)
app = Flask('')

@app.route('/')
def home():
    return "✅ ApexBot is Running!"

def run():
    # Koyeb은 기본적으로 8080 포트를 사용하거나 환경 변수로 포트를 지정합니다.
    port = int(os.environ.get("PORT", 8081))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. 봇 기본 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 사용자 정보 (기존 키와 토큰 그대로 유지)
APEX_API_KEY = "6f5742b0107d506d63727c0e4ce0d06e"
DISCORD_TOKEN = "MTQ4NTI4ODA0NzM1MTE3MzIyMQ.GFhaN0.lUVkpxbL7nBkk6Qvy1pfTZjC99PxxoevrMWhAI"

# 맵 이름 한글 변환
KOR_MAPS = {
    "World's Edge": "세상의 끝", "Olympus": "올림푸스", "Kings Canyon": "킹스 캐년",
    "Storm Point": "스톰 포인트", "Broken Moon": "브로큰 문", "District": "디스트릭트"
}

def to_kor(name):
    return KOR_MAPS.get(name, name)

# 3. 상태창 업데이트 (12시간마다 1번 실행하여 할당량 보호)
@tasks.loop(hours=12)
async def update_presence():
    try:
        url = f"https://api.mozambiquehe.re/maprotation?auth={APEX_API_KEY}"
        res = requests.get(url).json()
        rank = res.get('ranked') or res.get('ranked_battle_royale')
        if rank:
            m = to_kor(rank['current']['map'])
            await bot.change_presence(activity=discord.Game(name=f"랭크 맵: {m}"))
    except:
        pass

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 로그인 성공!")
    if not update_presence.is_running():
        update_presence.start()

# 4. !랭크 명령어
@bot.command(name="랭크")
async def rank_info(ctx):
    try:
        url = f"https://api.mozambiquehe.re/maprotation?auth={APEX_API_KEY}"
        data = requests.get(url).json()
        
        # API 에러 체크
        if "Error" in data or "error" in data:
            await ctx.send("⚠️ API 할당량이 초과되었거나 오류가 발생했습니다.")
            return

        rank = data.get('ranked') or data.get('ranked_battle_royale')
        if rank:
            curr = to_kor(rank['current']['map'])
            rem = rank['current']['remainingTimer']
            next_m = to_kor(rank['next']['map'])
            
            embed = discord.Embed(title="🏆 Apex 랭크 맵 정보", color=discord.Color.gold())
            embed.add_field(name="📍 현재 맵", value=f"**{curr}**", inline=False)
            embed.add_field(name="⏰ 남은 시간", value=f"`{rem}`", inline=True)
            embed.add_field(name="➡️ 다음 맵", value=next_m, inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ 랭크 데이터를 찾을 수 없습니다.")
    except:
        await ctx.send("❌ 서버 연결 오류가 발생했습니다.")

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)