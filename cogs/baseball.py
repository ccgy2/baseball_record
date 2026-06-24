import discord
from discord.ext import commands
from firebase_admin import db

# --- GUI: 선수 기록 조회를 위한 인터랙티브 뷰 ---
class BaseballStatsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60) # 60초 동안 입력이 없으면 비활성화

    @discord.ui.button(label="타자 기록 조회", style=discord.ButtonStyle.primary, emoji="🏏")
    async def batter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 타자 목록 가져오기
        ref = db.reference("baseball/batters")
        data = ref.get()

        if not data:
            await interaction.response.send_message("등록된 타자가 없습니다.", ephemeral=True)
            return

        # 드롭다운 메뉴 생성
        options = [discord.SelectOption(label=name, description=f"안타: {stats.get('hits', 0)}개") for name, stats in data.items()]
        view = discord.ui.View()
        view.add_item(PlayerSelect("batters", options))
        
        await interaction.response.send_message("조회할 타자를 선택하세요:", view=view, ephemeral=True)

    @discord.ui.button(label="투수 기록 조회", style=discord.ButtonStyle.danger, emoji="⚾")
    async def pitcher_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 투수 목록 가져오기
        ref = db.reference("baseball/pitchers")
        data = ref.get()

        if not data:
            await interaction.response.send_message("등록된 투수가 없습니다.", ephemeral=True)
            return

        # 드롭다운 메뉴 생성
        options = [discord.SelectOption(label=name, description=f"이닝: {stats.get('innings', 0.0)}이닝") for name, stats in data.items()]
        view = discord.ui.View()
        view.add_item(PlayerSelect("pitchers", options))
        
        await interaction.response.send_message("조회할 투수를 선택하세요:", view=view, ephemeral=True)


# --- GUI: 선수 선택 드롭다운 메뉴 ---
class PlayerSelect(discord.ui.Select):
    def __init__(self, player_type, options):
        self.player_type = player_type
        super().__init__(placeholder="선수 이름을 선택하세요...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        name = self.values[0]
        ref = db.reference(f"baseball/{self.player_type}/{name}")
        data = ref.get()

        if not data:
            await interaction.response.send_message("기록을 찾을 수 없습니다.", ephemeral=True)
            return

        if self.player_type == "batters":
            # 타자 상세 스탯 계산
            ab = data.get("ab", 0)       # 타수
            hits = data.get("hits", 0)   # 안타
            hr = data.get("homeruns", 0) # 홈런
            rbi = data.get("rbi", 0)     # 타점
            bb = data.get("bb", 0)       # 볼넷
            
            avg = hits / ab if ab > 0 else 0.0
            obp = (hits + bb) / (ab + bb) if (ab + bb) > 0 else 0.0

            embed = discord.Embed(title=f"🏏 타자 [{name}] 선수 누적 리포트", color=discord.Color.blue())
            embed.add_field(name="타수 / 안타", value=f"{ab}타수 {hits}안타", inline=True)
            embed.add_field(name="홈런 / 타점", value=f"{hr}홈런 {rbi}타점", inline=True)
            embed.add_field(name="볼넷 (사사구)", value=f"{bb}개", inline=True)
            embed.add_field(name="타율 (AVG)", value=f"📊 `{avg:.3f}`", inline=True)
            embed.add_field(name="출루율 (OBP)", value=f"🎯 `{obp:.3f}`", inline=True)

        else:
            # 투수 상세 스탯 계산
            innings = data.get("innings", 0.0) # 이닝
            er = data.get("er", 0)             # 자책점
            so = data.get("so", 0)             # 탈삼진
            h_allowed = data.get("h_allowed", 0) # 피안타
            bb_allowed = data.get("bb_allowed", 0) # 피볼넷

            era = (er * 9) / innings if innings > 0 else 0.0
            whip = (h_allowed + bb_allowed) / innings if innings > 0 else 0.0

            embed = discord.Embed(title=f"⚾ 투수 [{name}] 선수 누적 리포트", color=discord.Color.red())
            embed.add_field(name="소화 이닝", value=f"{innings}이닝", inline=True)
            embed.add_field(name="탈삼진 (SO)", value=f"{so}개", inline=True)
            embed.add_field(name="자책점 (ER)", value=f"{er}점", inline=True)
            embed.add_field(name="피안타 / 피볼넷", value=f"{h_allowed}개 / {bb_allowed}개", inline=True)
            embed.add_field(name="평균자책점 (ERA)", value=f"📊 `{era:.2f}`", inline=True)
            embed.add_field(name="이닝당 출루허용률 (WHIP)", value=f"🎯 `{whip:.2f}`", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


# --- 야구 코그 클래스 ---
class Baseball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="기록실")
    async def open_stats_room(self, ctx):
        """버튼형 GUI 야구 기록실을 엽니다."""
        embed = discord.Embed(
            title="⚾ 야구 기록실 내부 시스템",
            description="아래 버튼을 눌러 등록된 타자 및 투수의 상세 누적 기록을 GUI 환경에서 간편하게 확인하세요.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=BaseballStatsView())

    # --- 데이터 입력 명령어들 ---

    @commands.command(name="타자등록")
    async def register_batter(self, ctx, name: str):
        ref = db.reference(f"baseball/batters/{name}")
        if ref.get() is not None:
            await ctx.send(f"⚠️ `{name}` 타자는 이미 등록되어 있습니다.")
            return
        ref.set({"ab": 0, "hits": 0, "homeruns": 0, "rbi": 0, "bb": 0})
        await ctx.send(f"⚾ 타자 `{name}` 선수가 상세 데이터 테이블에 등록되었습니다.")

    @commands.command(name="타자기록")
    async def update_batter(self, ctx, name: str, ab: int, hits: int, hr: int, rbi: int, bb: int):
        """타자의 기록을 입력합니다. (순서: 이름 타수 안타 홈런 타점 볼넷)
        예시: !타자기록 홍길동 4 2 1 3 1
        """
        ref = db.reference(f"baseball/batters/{name}")
        data = ref.get()
        if data is None:
            await ctx.send(f"❌ `{name}` 선수가 없습니다. 먼저 `!타자등록 {name}`을 해주세요.")
            return

        ref.update({
            "ab": data.get("ab", 0) + ab,
            "hits": data.get("hits", 0) + hits,
            "homeruns": data.get("homeruns", 0) + hr,
            "rbi": data.get("rbi", 0) + rbi,
            "bb": data.get("bb", 0) + bb
        })
        await ctx.send(f"📈 `{name}` 타자 기록 누적 완료! (타수+{ab}, 안타+{hits}, 홈런+{hr}, 타점+{rbi}, 볼넷+{bb})")

    @commands.command(name="투수등록")
    async def register_pitcher(self, ctx, name: str):
        ref = db.reference(f"baseball/pitchers/{name}")
        if ref.get() is not None:
            await ctx.send(f"⚠️ `{name}` 투수는 이미 등록되어 있습니다.")
            return
        ref.set({"innings": 0.0, "er": 0, "so": 0, "h_allowed": 0, "bb_allowed": 0})
        await ctx.send(f"⚾ 투수 `{name}` 선수가 상세 데이터 테이블에 등록되었습니다.")

    @commands.command(name="투수기록")
    async def update_pitcher(self, ctx, name: str, innings: float, er: int, so: int, h_allowed: int, bb_allowed: int):
        """투수의 기록을 입력합니다. (순서: 이름 이닝 자책 탈삼진 피안타 피볼넷)
        예시: !투수기록 김철수 6.0 2 7 4 1
        """
        ref = db.reference(f"baseball/pitchers/{name}")
        data = ref.get()
        if data is None:
            await ctx.send(f"❌ `{name}` 선수가 없습니다. 먼저 `!투수등록 {name}`을 해주세요.")
            return

        ref.update({
            "innings": round(data.get("innings", 0.0) + innings, 1),
            "er": data.get("er", 0) + er,
            "so": data.get("so", 0) + so,
            "h_allowed": data.get("h_allowed", 0) + h_allowed,
            "bb_allowed": data.get("bb_allowed", 0) + bb_allowed
        })
        await ctx.send(f"📈 `{name}` 투수 기록 누적 완료! (이닝+{innings}, 자책+{er}, 삼진+{so}, 피안타+{h_allowed}, 피볼넷+{bb_allowed})")

async def setup(bot):
    await bot.add_cog(Baseball(bot))
