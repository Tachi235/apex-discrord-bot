import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread

# 1. Koyeb 서버 유지용 웹 서버 (8000번 포트)
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

# 맵 이름 한글 번역 사전
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

# 랭크 데이터를 가져오는 함수 (이미지 및 다음 일정 포함)
def get_rank_full_data():
    try:
        url = f"https://api.mozambiquehe.re/maprotation?version=2&auth={APEX_API_KEY}"
        res = requests.get(url).json()
        ranked = res.get('ranked', {})
        current = ranked.get('current', {})
        next_data = ranked.get('next', {})
        
        data = {
            "c_map": MAP_NAMES.get(current.get('map'), current.get('map')),
            "n_map": MAP_NAMES.get(next_data.get('map'), next_data.get('map')),
            "rem": current.get('remainingTimer', '00:00:00'),
            "img": current.get('asset'),  # 맵 이미지 주소
            "next_start": next_data.get('readableDate_start', '시간 미확인') # 다음 시작 시간
        }
        return data
    except Exception as e:
        print(f"데이터 가져오기 오류: {e}")
        return None

# 3. 상태창 업데이트 (30분 주기 - API 절약)
@tasks.loop(minutes=30)
async def update_status():
    data = get_rank_full_data()
    if data:
        # 상태창: 랭크: 현재맵 ➜ 다음맵
        activity = discord.Game(name=f"랭크: {data['c_map']} ➜ {data['n_map']}")
        await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 로그인 성공!")
    if not update_status.is_running():
        update_status.start()

# 4. !랭크 명령어 (Nessie 스타일 한글화 버전)
@bot.command(name="랭크")
async def rank_cmd(ctx):
    data = get_rank_full_data()
    if data:
        # 보라색 강조 (Nessie 스타일)
        embed = discord.Embed(title="배틀로얄 | 랭크 로테이션", color=0x9b59b6)
        
        # 상단 정보: 현재 맵과 남은 시간 (박스 형태)
        embed.add_field(name="현재 맵", value=f"```\n{data['c_map']}\n```", inline=True)
        embed.add_field(name="남은 시간", value=f"```\n{data['rem']}\n```", inline=True)
        
        # 중앙 맵 이미지 설정
        if data['img']:
            embed.set_image(url=data['img'])
        
        # 하단 푸터: 다음 맵 정보
        embed.set_footer(text=f"다음 맵: {data['n_map']} • 시작 시간: {data['next_start']}")
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ 랭크 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
