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

def format_to_korean_relative_time(date_str):
    try:
        utc_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        kst_dt = utc_dt + timedelta(hours=9)
        now_kst = datetime.utcnow() + timedelta(hours=9)
        
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

# 3. 명령어 (줄바꿈 로직 수정)
@bot.command(name="랭크")
async def rank_cmd(ctx):
    data = get_rank_full_data()
    if data:
        embed = discord.Embed(title="배틀로얄 | 랭크 로테이션", color=0x9b59b6)
        
        # [상단] 현재 정보 (2개만 배치하여 줄바꿈 유도)
        embed.add_field(name="현재 맵", value=f"```\n{data['c_map']}\n```", inline=True)
        embed.add_field(name="남은 시간", value=f"```\n{data['rem']}\n```", inline=True)
        
        # [중요] 강제 줄바꿈용 필드 (이미지 전용 공간 확보)
        embed.add_field(name="\u200b", value="\u200b", inline=False) 
        
        # [중앙] 이미지
        if data['img']:
            embed.set_image(url=data['img'])
        
        # [하단] 다음 정보 (이미지 아래에 확실하게 배치)
        embed.add_field(name="다음 맵", value=f"```\n{data['n_map']}\n```", inline=True)
        embed.add_field(name="시작 시간", value=f"```\n{data['next_start']}\n```", inline=True)
        
        embed.set_footer(text="Apex Legends Rank Rotation Updates")
        await ctx.send(embed=embed)

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
