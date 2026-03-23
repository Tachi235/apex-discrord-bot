import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread

# 1. Koyeb Health Check용 웹 서버
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
        
        # 오직 'ranked' 데이터만 가져옴
        ranked = res.get('ranked', {})
        current = ranked.get('current', {})
        next_data = ranked.get('next', {})
        
        curr_map = MAP_NAMES.get(current.get('map'), current.get('map'))
        next_map = MAP_NAMES.get(next_data.get('map'), next_data.get('map'))
        remaining = current.get('remainingTimer', '00:00:00')
        
        return curr_map, next_map, remaining
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None, None, None

# 4. 상태창 업데이트 (6시간마다 - 현재 ➜ 다음 맵 표시)
@tasks.loop(hours=6)
async def update_status():
    curr, nxt, _ = get_rank_only_data()
    if curr:
        # 상태창에 랭크 정보만 표시
        status_msg = f"랭크: {curr} ➜ {nxt}"
        await bot.change_presence(activity=discord.Game(name=status_msg))

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 로그인 성공!")
    if not update_status.is_running():
        update_status.start()

# 5. !랭크 명령어 (채팅창 임베드)
@bot.command(name="랭크")
async def rank_cmd(ctx):
    curr, nxt, rem = get_rank_only_data()
    if curr:
        embed = discord.Embed(title="🏆 현재 랭크 로테이션", color=0xff4444)
        embed.add_field(name="📍 현재 랭크 맵", value=f"**{curr}**", inline=True)
        embed.add_field(name="⏭️ 다음 랭크 맵", value=nxt, inline=True)
        embed.add_field(name="⏰ 다음 교체까지", value=f"`{rem}`", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ 랭크 데이터를 불러올 수 없습니다.")

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
