import discord
from discord.ext import commands
from firebase_admin import db

# --- GUI: 선수 기록 조회를 위한 인터랙티브 뷰 ---
class BaseballStatsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="타자 상세 기록 조회", style=discord.ButtonStyle.primary, emoji="🏏")
    async def batter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ref = db.reference("baseball/batters")
        data = ref.get()

        if not data:
            await interaction.response.send_message("등록된 타자가 없습니다.", ephemeral=True)
            return

        options = [discord.SelectOption(label=name, description=f"{stats.get('games', 0)}경기 | {stats.get('hits', 0)}안타") for name, stats in data.items()]
        view = discord.ui.View()
        view.add_item(DetailedPlayerSelect("batters", options))
        await interaction.response.send_message("조회할 타자를 선택하세요:", view=view, ephemeral=True)

    @discord.ui.button(label="투수 상세 기록 조회", style=discord.ButtonStyle.danger, emoji="⚾")
    async def pitcher_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ref = db.reference("baseball/pitchers")
        data = ref.get()

        if not data:
            await interaction.response.send_message("등록된 투수가 없습니다.", ephemeral=True)
            return

        options = [discord.SelectOption(label=name, description=f"{stats.get('games', 0)}경기 | {stats.get('innings', 0.0)}이닝") for name, stats in data.items()]
        view = discord.ui.View()
        view.add_item(DetailedPlayerSelect("pitchers", options))
        await interaction.response.send_message("조회할 투수를 선택하세요:", view=view, ephemeral=True)


# --- GUI: 선수 선택 드롭다운 메뉴 ---
class DetailedPlayerSelect(discord.ui.Select):
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
            g = data.get("games", 0)
            ab = data.get("ab", 0)
            h = data.get("hits", 0)
            h2 = data.get("h2", 0)
            h3 = data.get("h3", 0)
            hr = data.get("homeruns", 0)
            h1 = h - (h2 + h3 + hr)
            
            rbi = data.get("rbi", 0)
            r = data.get("runs", 0)
            sb = data.get("sb", 0)
            bb = data.get("bb", 0)
            ibb = data.get("ibb", 0)
            so = data.get("so", 0)
            sf = data.get("sf", 0)
            sh = data.get("sh", 0)
            gdp = data.get("gdp", 0)
            err = data.get("errors", 0)
            bro = data.get("bro", 0)

            avg = h / ab if ab > 0 else 0.0
            obp_denom = ab + bb + sf
            obp = (h + bb) / obp_denom if obp_denom > 0 else 0.0
            total_bases = h1 + (h2 * 2) + (h3 * 3) + (hr * 4)
            slg = total_bases / ab if ab > 0 else 0.0
            ops = obp + slg

            embed = discord.Embed(title=f"🏏 [{name}] 타자 대기록 리포트", color=discord.Color.blue())
            embed.add_field(name="기본 기록", value=f"`{g}경기` `{ab}타수` `{h}안타`", inline=False)
            embed.add_field(name="안타 세부", value=f"1루타: {h1} | 2루타: {h2} | 3루타: {h3} | 홈런: {hr}", inline=False)
            embed.add_field(name="생산력", value=f"득점: {r} | 타점: {rbi} | 도루: {sb}", inline=True)
            embed.add_field(name="선구안/기타", value=f"볼넷: {bb}(고의:{ibb}) | 삼진: {so}\n희플: {sf} | 희번: {sh}", inline=False)
            embed.add_field(name="기타 지표", value=f"실책: {err} | 병살타: {gdp} | 주루사: {bro}", inline=False)
            embed.add_field(name="📈 비율 스탯", value=f"타율(AVG): `{avg:.3f}`\n출루율(OBP): `{obp:.3f}`\n장타율(SLG): `{slg:.3f}`\n**OPS**: **`{ops:.3f}`**", inline=False)

        else:
            # [투수 데이터 파싱]
            g = data.get("games", 0)
            innings = data.get("innings", 0.0)
            w = data.get("wins", 0)
            l = data.get("losses", 0)
            sv = data.get("saves", 0)
            hld = data.get("holds", 0)
            so = data.get("so", 0)
            h_allowed = data.get("h_allowed", 0)
            hr_allowed = data.get("hr_allowed", 0)
            r = data.get("runs", 0)
            er = data.get("er", 0)
            bb = data.get("bb", 0)        # 사사구
            ibb = data.get("ibb", 0)      # 고의사구
            balk = data.get("balk", 0)
            wp = data.get("wp", 0)        # 폭투

            era = (er * 9) / innings if innings > 0 else 0.0
            whip = (h_allowed + bb) / innings if innings > 0 else 0.0

            embed = discord.Embed(title=f"⚾ [{name}] 투수 대기록 리포트", color=discord.Color.red())
            embed.add_field(name="기본 기록", value=f"`{g}경기` `{innings}이닝` | `{w}승 {l}패 {sv}세이브 {hld}홀드`", inline=False)
            embed.add_field(name="피안타 및 실점", value=f"피안타: {h_allowed} | 피홈런: {hr_allowed}\n총 실점: {r} | 자책점: {er}", inline=False)
            embed.add_field(name="제구 및 기타", value=f"탈삼진: {so} | 사사구: {bb} | 고의사구: {ibb}\n보크: {balk} | 폭투(WP): {wp}", inline=False)
            embed.add_field(name="📈 비율 스탯", value=f"평균자책점(ERA): `{era:.2f}`\n이닝당 출루허용률(WHIP): `{whip:.2f}`", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


class Baseball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="기록실")
    async def open_stats_room(self, ctx):
        """버튼형 GUI 야구 종합 기록실을 엽니다."""
        embed = discord.Embed(
            title="⚾ 야구 베이스볼 스탯 종합 시스템",
            description="아래 버튼을 누르면 비율 스탯(타율/출루율/장타율/OPS 및 ERA/WHIP)이 자동 계산된 인터랙티브 GUI 창이 열립니다.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=BaseballStatsView())

    # --- 타자 섹션 ---

    @commands.command(name="타자등록")
    async def register_batter(self, ctx, name: str):
        ref = db.reference(f"baseball/batters/{name}")
        if ref.get() is not None:
            await ctx.send(f"⚠️ `{name}` 타자는 이미 등록되어 있습니다.")
            return
        ref.set({
            "games": 0, "ab": 0, "hits": 0, "h2": 0, "h3": 0, "homeruns": 0,
            "rbi": 0, "runs": 0, "sb": 0, "bb": 0, "ibb": 0, "so": 0,
            "sf": 0, "sh": 0, "gdp": 0, "errors": 0, "bro": 0
        })
        await ctx.send(f"⚾ 타자 `{name}` 선수가 등록되었습니다.")

    @commands.command(name="타자기록")
    async def update_batter(self, ctx, name: str = None, games: int = None, ab: int = None, hits: int = None, h2: int = None, h3: int = None, hr: int = None, rbi: int = None, runs: int = None, sb: int = None, bb: int = None, ibb: int = None, so: int = None, sf: int = None, sh: int = None, gdp: int = None, err: int = None, bro: int = None):
        # 인자(값)를 하나라도 안 적거나 명령어만 치면 사용법 가이드 출력
        if name is None or bro is None:
            embed = discord.Embed(title="🏏 [도움말] !타자기록 입력 순서 가이드", color=discord.Color.blue())
            embed.description = f"값을 입력할 때는 쉼표 없이 **띄어쓰기**로 구분해 주세요.\n\n`!타자기록 [이름] [경기수] [타수] [안타] [2루타] [3루타] [홈런] [타점] [득점] [도루] [볼넷] [고의사구] [삼진] [희생플라이] [희생번트] [병살타] [실책] [주루사]`"
            embed.add_field(name="💡 입력 예시", value="`!타자기록 홍길동 1 4 2 1 0 1 3 2 1 1 0 1 0 0 0 0 0`", inline=False)
            await ctx.send(embed=embed)
            return

        ref = db.reference(f"baseball/batters/{name}")
        data = ref.get()
        if data is None:
            await ctx.send(f"❌ `{name}` 선수가 없습니다. 먼저 `!타자등록 {name}`을 해주세요.")
            return

        ref.update({
            "games": data.get("games", 0) + games, "ab": data.get("ab", 0) + ab, "hits": data.get("hits", 0) + hits,
            "h2": data.get("h2", 0) + h2, "h3": data.get("h3", 0) + h3, "homeruns": data.get("homeruns", 0) + hr,
            "rbi": data.get("rbi", 0) + rbi, "runs": data.get("runs", 0) + runs, "sb": data.get("sb", 0) + sb,
            "bb": data.get("bb", 0) + bb, "ibb": data.get("ibb", 0) + ibb, "so": data.get("so", 0) + so,
            "sf": data.get("sf", 0) + sf, "sh": data.get("sh", 0) + sh, "gdp": data.get("gdp", 0) + gdp,
            "errors": data.get("errors", 0) + err, "bro": data.get("bro", 0) + bro
        })
        await ctx.send(f"📈 타자 `{name}` 경기 기록 누적 완료!")

    # --- 투수 섹션 ---

    @commands.command(name="투수등록")
    async def register_pitcher(self, ctx, name: str):
        ref = db.reference(f"baseball/pitchers/{name}")
        if ref.get() is not None:
            await ctx.send(f"⚠️ `{name}` 투수는 이미 등록되어 있습니다.")
            return
        ref.set({
            "games": 0, "innings": 0.0, "wins": 0, "losses": 0, "saves": 0, "holds": 0,
            "so": 0, "h_allowed": 0, "hr_allowed": 0, "runs": 0, "er": 0, "bb": 0, "ibb": 0, "balk": 0, "wp": 0
        })
        await ctx.send(f"⚾ 투수 `{name}` 선수가 등록되었습니다.")

    @commands.command(name="투수기록")
    async def update_pitcher(self, ctx, name: str = None, games: int = None, innings: float = None, wins: int = None, losses: int = None, saves: int = None, holds: int = None, so: int = None, h_allowed: int = None, hr_allowed: int = None, runs: int = None, er: int = None, bb: int = None, ibb: int = None, balk: int = None, wp: int = None):
        # 인자(값)를 하나라도 안 적거나 명령어만 치면 사용법 가이드 출력
        if name is None or wp is None:
            embed = discord.Embed(title="⚾ [도움말] !투수기록 입력 순서 가이드", color=discord.Color.red())
            embed.description = f"값을 입력할 때는 쉼표 없이 **띄어쓰기**로 구분해 주세요.\n\n`!투수기록 [이름] [경기수] [이닝] [승] [패] [세이브] [홀드] [탈삼진] [피안타] [피홈런] [실점] [자책점] [사사구] [고의사구] [보크] [폭투]`"
            embed.add_field(name="💡 입력 예시", value="`!투수기록 김철수 1 5.2 1 0 0 0 6 4 1 2 2 1 0 0 0`", inline=False)
            await ctx.send(embed=embed)
            return

        ref = db.reference(f"baseball/pitchers/{name}")
        data = ref.get()
        if data is None:
            await ctx.send(f"❌ `{name}` 선수가 없습니다. 먼저 `!투수등록 {name}`을 해주세요.")
            return

        ref.update({
            "games": data.get("games", 0) + games,
            "innings": round(data.get("innings", 0.0) + innings, 1),
            "wins": data.get("wins", 0) + wins,
            "losses": data.get("losses", 0) + losses,
            "saves": data.get("saves", 0) + saves,
            "holds": data.get("holds", 0) + holds,
            "so": data.get("so", 0) + so,
            "h_allowed": data.get("h_allowed", 0) + h_allowed,
            "hr_allowed": data.get("hr_allowed", 0) + hr_allowed,
            "runs": data.get("runs", 0) + runs,
            "er": data.get("er", 0) + er,
            "bb": data.get("bb", 0) + bb,
            "ibb": data.get("ibb", 0) + ibb,
            "balk": data.get("balk", 0) + balk,
            "wp": data.get("wp", 0) + wp
        })
        await ctx.send(f"📈 투수 `{name}` 경기 기록 누적 완료!")

async def setup(bot):
    await bot.add_cog(Baseball(bot))
