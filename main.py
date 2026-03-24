import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# 1. Koyeb 생존 확인용 웹 서버 (가장 중요!)
app = Flask('')

@app.route('/')
def home():
    return "✅ Apex Rank Bot is Online and Healthy!"

def run():
    # 코옙은 PORT 환경 변수를 통해 포트를 지정합니다.
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
intents.presences = True 
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
    except Exception as e:
        print(f"API Error: {e}")
        return None

# 상태창 루프
@tasks.loop(minutes=30)
async def update_status():
    try:
        data = get_rank_full_data()
        if data:
            status_text = f"랭크: {data['c_map']} ➜ {data['n_map']}"
            await bot.change_presence(activity=discord.Game(name=status_text))
    except Exception as e:
        print(f"Status Update Error: {e}")

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 로그인 성공!")
    if not update_status.is_running():
        update_status.start()

@bot.command(name="랭크")
async def rank_cmd(ctx):
    data = get_rank_full_data()
    if data:
        embed = discord.Embed(title="배틀로얄 | 랭크 로테이션", color=0x9b59b6)
        embed.add_field(name="현재 맵", value=f"```\n{data['c_map']}\n```", inline=True)
        embed.add_field(name="남은 시간", value=f"```\n{data['rem']}\n```", inline=True)
        if data['img']:
            embed.set_image(url=data['img'])
        embed.set_footer(text=f"다음 맵: {data['n_map']} • {data['next_start']}")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ 정보를 가져오는 데 실패했습니다.")

if __name__ == "__main__":
    # 봇 시작 전 웹 서버를 먼저 띄웁니다.
    keep_alive()
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Bot 실행 에러: {e}")
