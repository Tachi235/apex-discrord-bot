import discord
from discord.ext import commands, tasks
import requests
import os

# 1. 설정
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

# 2. 랭크 맵 정보 함수 (주소에 version=2 추가)
def get_ranked_map():
    try:
        # 주소 끝에 &version=2를 반드시 붙여야 합니다.
        url = f"https://api.mozambiquehe.re/maprotation?version=2&auth={APEX_API_KEY}"
        res = requests.get(url).json()
        
        # version=2를 쓰면 데이터 구조가 ranked -> current -> map 순서가 됩니다.
        ranked_info = res.get('ranked', {}).get('current', {})
        
        eng_map = ranked_info.get('map', '정보 없음')
        kor_map = MAP_NAMES.get(eng_map, eng_map)
        
        remaining = ranked_info.get('remainingTimer', '??:??')
        return kor_map, remaining
    except Exception as e:
        print(f"API Error: {e}")
        return None, None

# 3. 상태창 루프 (6시간마다)
@tasks.loop(hours=6)
async def update_presence():
    kor_map, _ = get_ranked_map()
    if kor_map and kor_map != '정보 없음':
        await bot.change_presence(activity=discord.Game(name=f"랭크 맵: {kor_map}"))
    else:
        await bot.change_presence(activity=discord.Game(name="맵 정보 확인 불가"))

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 로그인 성공!")
    if not update_presence.is_running():
        update_presence.start()

@bot.command(name="랭크")
async def rank_info(ctx):
    kor_map, remaining = get_ranked_map()
    if kor_map and kor_map != '정보 없음':
        await ctx.send(f"🏆 **현재 랭크 맵**: {kor_map}\n⏰ **다음 로테이션까지**: {remaining}")
    else:
        await ctx.send("❌ 랭크 정보를 불러올 수 없습니다. API 주소를 확인하세요.")

bot.run(DISCORD_TOKEN)
