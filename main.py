import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime

# 1. Koyeb 서버 유지를 위한 웹 서버 (8000번 포트)
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

# 시간 형식을 오전/오후 0:00 형식으로 변환하는 함수
def format_to_korean_time(date_str):
    try:
        # API 제공 날짜 예시: 2026-03-23 18:00:00
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        ampm = "오전" if dt.hour < 12 else "오후"
        hour = dt.hour if dt.hour <= 12 else dt.hour - 12
        if hour == 0: hour = 12
        return f"{ampm} {hour}:00"
    except:
        return "시간 확인 불가"

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
            "img": current.get('asset'),
            "next_start": format_to_korean_time(next_data.get('readableDate_start', ''))
        }
        return data
    except Exception as e:
        print(f"API Error: {e}")
        return None

# 3. 상태창 업데이트 (30분 주기)
@tasks.loop(minutes=30)
async def update_status():
    data = get_rank_full_data()
    if data:
        activity = discord.Game(name=f"랭크: {data['c_map']} ➜ {data['n_map']}")
        await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 로그인 성공!")
    if not update_status.is_running():
        update_status.start()

# 4. !랭크 명령어 (Nessie 스타일 레이아웃 반영)
@bot.command(name="랭크")
async def rank_cmd(ctx):
    data = get_rank_full_data()
    if data:
        embed = discord.Embed(title="배틀로얄 | 랭크 로테이션", color=0x9b59b6)
        
        # 현재 맵 정보
        embed.add_field(name="현재 맵", value=f"```\n{data['c_map']}\n```", inline=True)
        embed.add_field(name="남은 시간", value=f"```\n{data['rem']}\n```", inline=True)
        
        # 중앙 맵 이미지
        if data['img']:
            embed.set_image(url=data['img'])
        
        # 다음 맵 정보 (현재 맵과 동일한 크기로 정렬)
        embed.add_field(name="다음 맵", value=f"```\n{data['n_map']}\n```", inline=True)
        embed.add_field(name="시작 시간", value=f"```\n{data['next_start']}\n```", inline=True)
        
        embed.set_footer(text="Apex Legends Rank Rotation Updates")
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ 정보를 불러오는 중 오류가 발생했습니다.")

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
