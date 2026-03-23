import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread

# 1. Koyeb 서버 유지용
app = Flask('')
@app.route('/')
def home(): return "✅ Bot is Online!"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. 설정
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
APEX_API_KEY = os.environ.get("APEX_API_KEY")

MAP_NAMES = {
    "World's Edge": "세상의 끝", "Storm Point": "스톰 포인트",
    "Broken Moon": "브로큰 문", "Kings Canyon": "킹스 캐년",
    "Olympus": "올림푸스", "District": "디스트릭트", "E-District": "E-디스트릭트"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# API 데이터를 가져오는 통합 함수
def get_rank_data():
    try:
        url = f"https://api.mozambiquehe.re/maprotation?version=2&auth={APEX_API_KEY}"
        res = requests.get(url).json()
        ranked = res.get('ranked', {})
        current = ranked.get('current', {})
        next_data = ranked.get('next', {})
        
        c_map = MAP_NAMES.get(current.get('map'), current.get('map'))
        n_map = MAP_NAMES.get(next_data.get('map'), next_data.get('map'))
        rem = current.get('remainingTimer', '00:00:00')
        return c_map, n_map, rem
    except Exception as e:
        print(f"API Error: {e}")
        return None, None, None

# 3. 상태창 업데이트 (주기를 30분으로 늘려 API 절약)
@tasks.loop(minutes=30)
async def update_status():
    curr, nxt, _ = get_rank_data()
    if curr:
        # 봇 상태창에 "랭크: 현재맵 ➜ 다음맵" 표시
        activity = discord.Game(name=f"랭크: {curr} ➜ {nxt}")
        await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 로그인 성공!")
    if not update_status.is_running():
        update_status.start()

# 4. !랭크 명령어 (정렬 및 디자인 개선)
@bot.command(name="랭크")
async def rank_cmd(ctx):
    curr, nxt, rem = get_rank_data()
    if curr:
        embed = discord.Embed(title="🏆 현재 랭크 로테이션", color=0xff4444)
        
        # 필드 이름을 비워서( \u200b ) 맵 이름들을 가로로 예쁘게 정렬 시도
        embed.add_field(name="📍 현재 랭크 맵", value=f"**{curr}**", inline=True)
        embed.add_field(name=" \u200b", value=" \u200b ", inline=True) # 중간 공백 칸
        embed.add_field(name="➡️ 다음 랭크 맵", value=f"**{nxt}**", inline=True)
        
        embed.add_field(name="⏰ 다음 교체까지", value=f"`{rem}`", inline=False)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ 데이터를 불러올 수 없습니다.")

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
