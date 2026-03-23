import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread

# 1. Koyeb Health Check용 웹 서버 (8000번 포트)
app = Flask('')
@app.route('/')
def home(): return "✅ Apex Rank Bot is Online!"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. 봇 설정
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

# 3. 랭크 데이터 전용 추출 함수
def get_rank_only_data():
    try:
        url = f"https://api.mozambiquehe.re/maprotation?version=2&auth={APEX_API_KEY}"
        res = requests.get(url).json()
        ranked = res.get('ranked', {})
        current = ranked.get('current', {})
        next_data = ranked.get('next', {})
        
        c_map = MAP_NAMES.get(current.get('map'), current.get('map'))
        n_map = MAP_NAMES.get(next_data.get('map'), next_data.get('map'))
        remaining = current.get('remainingTimer', '00:00:00')
        
        return c_map, n_map, remaining
    except:
        return None, None, None

# 4. 상태창 업데이트 (현재 ➜ 다음 맵 표시)
@tasks.loop(minutes=30)
async def update_status():
    curr, nxt, _ = get_rank_only_data()
    if curr:
        # 상태창 예시: 랭크: E-디스트릭트 ➜ 세상의 끝
        await bot.change_presence(activity=discord.Game(name=f"랭크: {curr} ➜ {nxt}"))

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 로그인 성공!")
    if not update_status.is_running():
        update_status.start()

# 5. !랭크 명령어 (중복되는 print/send 구문 모두 삭제됨)
@bot.command(name="랭크")
async def rank_cmd(ctx):
    curr, nxt, rem = get_rank_only_data()
    if curr:
        # 이 블록 하나만 실행되므로 메시지가 한 번만 나옵니다.
        embed = discord.Embed(title="🏆 현재 랭크 로테이션", color=0xff4444)
        embed.add_field(name=" 현재 랭크 맵", value=f"**{curr}**", inline=True)
        embed.add_field(name="➡️ 다음 랭크 맵", value=nxt, inline=True)
        embed.add_field(name=" 다음 교체까지", value=f"`{rem}`", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ 데이터를 불러올 수 없습니다.")

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
