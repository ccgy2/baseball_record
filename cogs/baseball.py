import discord
from discord.ext import commands
from firebase_admin import db

class Baseball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 타자 기능 ---

    @commands.command(name="타자등록")
    async def register_batter(self, ctx, name: str):
        """새로운 타자를 Firebase에 등록합니다."""
        ref = db.reference(f"baseball/batters/{name}")
        
        if ref.get() is not None:
            await ctx.send(f"⚠️ `{name}` 타자는 이미 등록되어 있습니다.")
            return

        ref.set({
            "hits": 0,
            "homeruns": 0,
            "rbi": 0
        })
        await ctx.send(f"⚾ 타자 `{name}` 선수가 성공적으로 등록되었습니다.")

    @commands.command(name="타자기록")
    async def update_batter(self, ctx, name: str, hits: int, homeruns: int, rbi: int):
        """타자의 기록을 누적 추가합니다. (예: !타자기록 홍길동 2 1 3)"""
        ref = db.reference(f"baseball/batters/{name}")
        data = ref.get()

        if data is None:
            await ctx.send(f"❌ `{name}` 선수가 없습니다. 먼저 `!타자등록 {name}`을 해주세요.")
            return

        new_hits = data.get("hits", 0) + hits
        new_homeruns = data.get("homeruns", 0) + homeruns
        new_rbi = data.get("rbi", 0) + rbi

        ref.update({
            "hits": new_hits,
            "homeruns": new_homeruns,
            "rbi": new_rbi
        })
        await ctx.send(f"📈 `{name}` 선수 기록 업데이트! (안타 +{hits}, 홈런 +{homeruns}, 타점 +{rbi})")

    @commands.command(name="타자조회")
    async def view_batter(self, ctx, name: str):
        """타자의 누적 기록을 불러와 임베드로 출력합니다."""
        ref = db.reference(f"baseball/batters/{name}")
        data = ref.get()

        if not data:
            await ctx.send(f"❌ `{name}` 선수의 기록을 찾을 수 없습니다.")
            return

        embed = discord.Embed(title=f"⚾ {name} 선수 누적 기록", color=discord.Color.blue())
        embed.add_field(name="안타", value=f"{data.get('hits', 0)}개", inline=True)
        embed.add_field(name="홈런", value=f"{data.get('homeruns', 0)}개", inline=True)
        embed.add_field(name="타점", value=f"{data.get('rbi', 0)}점", inline=True)
        await ctx.send(embed=embed)


    # --- 투수 기능 ---

    @commands.command(name="투수등록")
    async def register_pitcher(self, ctx, name: str):
        """새로운 투수를 Firebase에 등록합니다."""
        ref = db.reference(f"baseball/pitchers/{name}")
        
        if ref.get() is not None:
            await ctx.send(f"⚠️ `{name}` 투수는 이미 등록되어 있습니다.")
            return

        ref.set({
            "innings": 0.0,
            "strikeouts": 0,
            "er": 0
        })
        await ctx.send(f"⚾ 투수 `{name}` 선수가 성공적으로 등록되었습니다.")

    @commands.command(name="투수기록")
    async def update_pitcher(self, ctx, name: str, innings: float, strikeouts: int, er: int):
        """투수의 기록을 누적 추가합니다. (예: !투수기록 김철수 5.1 6 2)"""
        ref = db.reference(f"baseball/pitchers/{name}")
        data = ref.get()

        if data is None:
            await ctx.send(f"❌ `{name}` 선수가 없습니다. 먼저 `!투수등록 {name}`을 해주세요.")
            return

        new_innings = round(data.get("innings", 0.0) + innings, 1)
        new_strikeouts = data.get("strikeouts", 0) + strikeouts
        new_er = data.get("er", 0) + er

        ref.update({
            "innings": new_innings,
            "strikeouts": new_strikeouts,
            "er": new_er
        })
        await ctx.send(f"📈 `{name}` 선수 기록 업데이트! (이닝 +{innings}, 탈삼진 +{strikeouts}, 자책점 +{er})")

    @commands.command(name="투수조회")
    async def view_pitcher(self, ctx, name: str):
        """투수의 누적 기록을 불러와 임베드로 출력합니다."""
        ref = db.reference(f"baseball/pitchers/{name}")
        data = ref.get()

        if not data:
            await ctx.send(f"❌ `{name}` 선수의 기록을 찾을 수 없습니다.")
            return

        embed = discord.Embed(title=f"⚾ {name} 선수 누적 기록", color=discord.Color.red())
        embed.add_field(name="이닝", value=f"{data.get('innings', 0.0)}이닝", inline=True)
        embed.add_field(name="탈삼진", value=f"{data.get('strikeouts', 0)}개", inline=True)
        embed.add_field(name="자책점", value=f"{data.get('er', 0)}점", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Baseball(bot))
