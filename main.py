import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# 1. Koyeb 서버 유지용
app = Flask('')
@app.route('/')
def home(): return "✅ Apex Rank Bot Online!"

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
    "World's Edge": "세상의 끝", "Storm Point": "스톰 포인트",
    "Broken Moon": "브로큰 문", "Kings Canyon": "킹스 캐년",
    "Olympus": "올림푸스", "District": "디스트릭트", "E-District": "E-디스트릭트"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 한국 시간으로 변환 및 "오늘/내일" 판별 함수
def format_to_korean_relative_time(date_str):
    try:
        # API 시간(UTC)을 파이썬 시간 객체로 변환
        utc_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        # 한국 시간으로 변환 (UTC + 9시간)
        kst_dt = utc_dt + timedelta(hours=9)
        
        # 현재 한국 시간 기준 오늘/내일 판단
        now_kst = datetime.now() + timedelta(hours=9) # 서버 환경에 따라 조정
        day_str = "오늘" if kst_dt.date() == now_kst.date() else "내일"
        
        ampm = "오전" if kst_dt.hour < 12 else "오후"
        hour = kst_dt.hour if kst_dt.hour <= 12 else kst_dt.hour - 12
        if hour == 0: hour = 12
        
        return f"{day_str} {ampm} {hour}:00"
    except:
        return "시간 확인 불가"

def get_rank_full_data():
    try:
        url = f"https://api.mozambiquehe.re/maprotation?version=2&auth={APEX_API_KEY}"
        res = requests.get(url).json()
        ranked = res.get('ranked', {})
        current = ranked.get('current', {})
        next_data = ranked.get('next', {})
        
        return {
            "c_map": MAP_NAMES.get(current.get('map'), current.get('map')),
            "n_map": MAP_NAMES.get(next_data.get('map'), next_data.get('map')),
            "rem": current.get('remainingTimer', '00:00:00'),
            "img": current.get('asset'),
            "next_start": format_to_korean_relative_time(next_data.get('readableDate_start', ''))
        }
    except:
        return None

# 3. 상태창 및 명령어
@tasks.loop(minutes=30)
async def update_status():
    data = get_rank_full_data()
    if data:
        activity = discord.Game(name=f"랭크: {data['c_map']} ➜ {data['n_map']}")
        await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_ready():
    if not update_status.is_running():
        update_status.start()

@bot.command(name="랭크")
async def rank_cmd(ctx):
    data = get_rank_full_data()
    if data:
        embed = discord.Embed(title="배틀로얄 | 랭크 로테이션", color=0x9b59b6)
        
        # 1층: 현재 정보
        embed.add_field(name="현재 맵", value=f"```\n{data['c_map']}\n```", inline=True)
        embed.add_field(name="남은 시간", value=f"```\n{data['rem']}\n```", inline=True)
        
        # 이미지
        if data['img']:
            embed.set_image(url=data['img'])
        
        # 2층: 다음 정보 (한 줄에 나란히 배치)
        embed.add_field(name="다음 맵", value=f"```\n{data['n_map']}\n```", inline=True)
        embed.add_field(name="시작 시간", value=f"```\n{data['next_start']}\n```", inline=True)
        
        embed.set_footer(text="Apex Legends Rank Rotation Updates")
        await ctx.send(embed=embed)

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
