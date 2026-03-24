import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# 1. Koyeb 생존 확인용 웹 서버 (포트 바인딩 해결)
app = Flask('')

@app.route('/')
def home():
    return "✅ Apex Rank Bot is Online and Healthy!"

def run():
    # 코옙은 PORT 환경 변수를 사용하므로 8000번을 기본으로 설정합니다.
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. 봇 설정 및 권한(Intents) 주입
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
APEX_API_KEY = os.environ.get("APEX_API_KEY")

MAP_NAMES = {
    "World's Edge": "세상의 끝", "Storm Point": "스톰 포인트",
    "Broken Moon": "브로큰 문", "Kings Canyon": "킹스 캐년",
    "Olympus": "올림푸스", "District": "디스트릭트", "E-District": "E-디스트릭트"
}

# 인텐트 설정: 개발자 포털에서 켠 권한들을 코드에도 명시해야 합니다.
intents = discord.Intents.default()
intents.message_content = True 
intents.presences = True      # 온라인 상태 표시를 위해 필수
intents.members = True        # 서버 멤버 정보 접근

bot = commands.Bot(command_prefix="!", intents=intents)

def format_to_korean_relative_time(date_str):
    try:
        # 최근 파이썬 버전의 권장 방식에 맞춰 UTC 시간 계산 방식을 보정했습니다.
        utc_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        kst_dt = utc_dt + timedelta(hours=9)
        now_kst = datetime.now(timedelta(hours=9))
        
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
        print(f"API 호출 에러: {e}")
        return None

# 3. 상태창 자동 업데이트 루프 (30분 주기)
@tasks.loop(minutes=30)
async def update_status():
    try:
        data = get_rank_full_data()
        if data:
            status_text = f"랭크: {data['c_map']} ➜ {data['n_map']}"
            # 활동 상태 업데이트 및 온라인 상태 강제 유지
            await bot.change_presence(
                status=discord.Status.online,
                activity=discord.Game(name=status_text)
            )
            print(f"상태창 갱신 완료: {status_text}")
    except Exception as e:
        print(f"상태 갱신 중 에러: {e}")

@bot.event
async def on_ready():
    # 로그인 즉시 온라인 상태로 전환
    await bot.change_presence(status=discord.Status.online)
    print(f"✅ {bot.user.name} 로그인 성공 및 온라인 활성화!")
    
    if not update_status.is_running():
        update_status.start()

# 4. !랭크 명령어 (네시 봇 스타일 레이아웃)
@bot.command(name="랭크")
async def rank_cmd(ctx):
    data = get_rank_full_data()
    if data:
        embed = discord.Embed(title="배틀로얄 | 랭크 로테이션", color=0x9b59b6)
        
        # 상단 정보 (한글화 및 강조)
        embed.add_field(name="현재 맵", value=f"```\n{data['c_map']}\n```", inline=True)
        embed.add_field(name="남은 시간", value=f"```\n{data['rem']}\n```", inline=True)
        
        # 중앙 이미지
        if data['img']:
            embed.set_image(url=data['img'])
        
        # 하단 정보 (네시 봇 스타일 - Footer에 고정)
        embed.set_footer(text=f"다음 맵: {data['n_map']} • {data['next_start']}")
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ 정보를 불러오는 중 에러가 발생했습니다.")

if __name__ == "__main__":
    # 웹 서버 먼저 실행 후 봇 실행
    keep_alive()
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"봇 실행 실패 (토큰 확인 필요): {e}")
