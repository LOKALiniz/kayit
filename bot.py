import discord
from discord.ext import commands
from discord import app_commands
import os

# ──────────────────────────────────────────────
#  KANAL / ROL ID'LERİ
# ──────────────────────────────────────────────
BASVURU_KANAL_ID       = 1484188687440019644
BASVURU_GELEN_KANAL_ID = 1486072691172704276
MULAKAT_ONAY_ROLE_ID   = 1484188685757972580
MULAKAT_RED_ROLE_ID    = 1484188685757972581

# ──────────────────────────────────────────────
#  BOT KURULUMU
# ──────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ──────────────────────────────────────────────
#  MODAL
# ──────────────────────────────────────────────
class BasvuruModal(discord.ui.Modal, title="🚔 Polis Departmanı Başvurusu"):

    ooc_isim = discord.ui.TextInput(
        label="「👮」 OOC İsminiz",
        placeholder="Adınız Soyadınız",
        required=True,
        max_length=50,
    )
    ooc_yas = discord.ui.TextInput(
        label="「👮」 OOC Yaşınız",
        placeholder="Örn: 20",
        required=True,
        max_length=3,
    )
    fivem_bilgiler = discord.ui.TextInput(
        label="「👮」 FiveM Saati | Map Bilgisi | Ses Kalınlığı",
        placeholder="Örn: 350 saat | Map: 8/10 | Ses: 7/10",
        required=True,
        max_length=100,
    )
    ic_bilgiler = discord.ui.TextInput(
        label="「👮」 IC İsim | IC Yaş | Legal Rol Geçmişi?",
        placeholder="Örn: John Doe | 28 | Evet, 6 ay polis rolü",
        required=True,
        max_length=200,
    )
    ek_bilgiler = discord.ui.TextInput(
        label="「👮」 Aktiflik | Neden biz? | CK & Kural Kabulü",
        placeholder="Aktifliğim: Her gün 4-5 saat\nNeden katılmak istiyorum: ...\nNeden alınmalıyım: ...\nCK & Kural: Evet / Evet",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(title="🚔 POLİS DEPARTMANI BAŞVURUSU", color=0xF0A500)
        embed.set_author(
            name=f"{interaction.user} — Yeni Başvuru",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.add_field(name="━━━━━━ 〔 OOC BİLGİLER 〕 ━━━━━━", value="\u200b", inline=False)
        embed.add_field(name="「👮」 OOC İsim", value=f"```{self.ooc_isim.value}```", inline=True)
        embed.add_field(name="「👮」 OOC Yaş",  value=f"```{self.ooc_yas.value}```",  inline=True)
        embed.add_field(name="「👮」 FiveM Saati | Map | Ses", value=f"```{self.fivem_bilgiler.value}```", inline=False)
        embed.add_field(name="━━━━━━ 〔 IC BİLGİLER 〕 ━━━━━━", value="\u200b", inline=False)
        embed.add_field(name="「👮」 IC İsim | IC Yaş | Legal Geçmiş", value=f"```{self.ic_bilgiler.value}```", inline=False)
        embed.add_field(name="━━━━━━ 〔 EK BİLGİLER 〕 ━━━━━━", value="\u200b", inline=False)
        embed.add_field(name="「👮」 Aktiflik | Motivasyon | CK & Kural", value=f"```{self.ek_bilgiler.value}```", inline=False)
        embed.set_footer(text=f"Kullanıcı ID: {interaction.user.id}", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        view = YetkiliView(user_id=interaction.user.id)
        kanal = bot.get_channel(BASVURU_GELEN_KANAL_ID)
        await kanal.send(embed=embed, view=view)

        await interaction.followup.send(
            "✅ Başvurunuz iletildi! Yetkililerin incelemesini bekleyiniz.",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"Modal hatası: {error}")
        try:
            await interaction.response.send_message("❌ Bir hata oluştu, tekrar dene.", ephemeral=True)
        except Exception:
            pass


# ──────────────────────────────────────────────
#  BAŞVURU BUTONU — timeout=None → kalıcı
# ──────────────────────────────────────────────
class BasvuruView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📝  BAŞVURU YAP",
        style=discord.ButtonStyle.primary,
        custom_id="basvuru_ac",
    )
    async def basvuru_ac(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(BasvuruModal())
        except Exception as e:
            print(f"Buton hatası: {e}")


# ──────────────────────────────────────────────
#  YETKİLİ BUTONU — user_id custom_id'ye gömülü
#  Format: onay:123456789  →  bot restart'tan sonra da çalışır
# ──────────────────────────────────────────────
class YetkiliButon(discord.ui.Button):
    def __init__(self, action: str, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.action  = action
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)

        await interaction.response.defer()

        hedef = interaction.guild.get_member(self.user_id)

        if self.action == "onay":
            if hedef:
                dm = discord.Embed(
                    title="✅ Başvurunuz Onaylandı!",
                    description=(
                        "**Polis Departmanı** başvurunuz **kabul edildi!**\n\n"
                        "> Mülakat onay permini aldıktan sonra mülakat kanalına geçebilirsin.\n"
                        "> Başarılar dileriz! 🚔"
                    ),
                    color=0x2ECC71,
                )
                dm.set_footer(text=f"Yetkili: {interaction.user}")
                dm.timestamp = discord.utils.utcnow()
                try:
                    await hedef.send(embed=dm)
                except discord.Forbidden:
                    pass
            await self._guncelle(interaction, 0x2ECC71, "🚔 POLİS BAŞVURUSU — ✅ ONAYLANDI")
            await interaction.followup.send("✅ Onaylandı, kullanıcıya DM gönderildi.", ephemeral=True)

        elif self.action == "red":
            if hedef:
                dm = discord.Embed(
                    title="❌ Başvurunuz Reddedildi",
                    description=(
                        "**Polis Departmanı** başvurunuz **reddedildi.**\n\n"
                        "> Daha sonra tekrar başvurabilirsin.\n"
                        "> İyi günler dileriz."
                    ),
                    color=0xE74C3C,
                )
                dm.set_footer(text=f"Yetkili: {interaction.user}")
                dm.timestamp = discord.utils.utcnow()
                try:
                    await hedef.send(embed=dm)
                except discord.Forbidden:
                    pass
            await self._guncelle(interaction, 0xE74C3C, "🚔 POLİS BAŞVURUSU — ❌ REDDEDİLDİ")
            await interaction.followup.send("❌ Reddedildi, kullanıcıya DM gönderildi.", ephemeral=True)

        elif self.action == "mulakat":
            if not hedef:
                return await interaction.followup.send("❌ Kullanıcı sunucuda bulunamadı.", ephemeral=True)
            rol = interaction.guild.get_role(MULAKAT_ONAY_ROLE_ID)
            if rol:
                try:
                    await hedef.add_roles(rol)
                except discord.Forbidden:
                    return await interaction.followup.send("❌ Rol verilemedi, bot yetkilerini kontrol et.", ephemeral=True)
            dm = discord.Embed(
                title="🎤 Mülakat Onayı Verildi!",
                description=(
                    "**Mülakat Onay** permin verildi!\n\n"
                    "> Mülakat kanalına girerek mülakatını tamamlayabilirsin.\n"
                    "> Bol şans! 🚔"
                ),
                color=0x3498DB,
            )
            dm.set_footer(text=f"Yetkili: {interaction.user}")
            dm.timestamp = discord.utils.utcnow()
            try:
                await hedef.send(embed=dm)
            except discord.Forbidden:
                pass
            await self._guncelle(interaction, 0x3498DB, "🚔 POLİS BAŞVURUSU — 🎤 MÜLAKAT ONAYI VERİLDİ")
            await interaction.followup.send("🎤 Mülakat onayı verildi, kullanıcıya DM gönderildi.", ephemeral=True)

    async def _guncelle(self, interaction: discord.Interaction, renk: int, baslik: str):
        embed = interaction.message.embeds[0]
        embed.colour = renk
        embed.title  = baslik
        await interaction.message.edit(embed=embed, view=None)


class YetkiliView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        uid = str(user_id)
        self.add_item(YetkiliButon(action="onay",    user_id=user_id, label="✅  Onayla",           style=discord.ButtonStyle.success, custom_id=f"onay:{uid}"))
        self.add_item(YetkiliButon(action="red",     user_id=user_id, label="❌  Reddet",            style=discord.ButtonStyle.danger,  custom_id=f"red:{uid}"))
        self.add_item(YetkiliButon(action="mulakat", user_id=user_id, label="🎤  Mülakat Onayı Ver", style=discord.ButtonStyle.primary, custom_id=f"mulakat:{uid}"))


# ──────────────────────────────────────────────
#  SLASH COMMAND: /basvurugonder
# ──────────────────────────────────────────────
@tree.command(name="basvurugonder", description="Başvuru butonunu kanala gönderir. (Sadece Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def basvurugonder(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="🚔 POLİS DEPARTMANI BAŞVURU SİSTEMİ",
        description=(
            "```\nBAŞVURUNUZ TEKER TEKER İNCELENECEKTİR\n```\n\n"
            "> **ZAMAN SIKINTISI OLMAYAN** ve **HARD ROL YAPABİLEN** "
            "arkadaşlar başvuru atabilir.\n"
            "> Mülakata girebilmek için başvurunuzun **onaylanması** ve "
            "**Mülakat Onay** perminizin olması gerekmektedir.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📋 **BAŞVURU FORMU İÇERİĞİ**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**[ OOC BİLGİLER ]**\n"
            "「👮」İsim\n「👮」Yaş\n「👮」FiveM Saati (200+)\n"
            "「👮」Map Bilgisi (?/10)\n「👮」Ses Kalınlığı (?/10)\n\n"
            "**[ IC BİLGİLER ]**\n"
            "「👮」IC İsim\n「👮」IC Yaş\n「👮」Daha önce legal rol yaptınız mı?\n\n"
            "**[ EK BİLGİLER ]**\n"
            "「👮」Aktiflik Süreniz\n「👮」Neden bize katılmak istiyorsunuz?\n"
            "「👮」Sizi neden almalıyız?\n「👮」CK yemeyi kabul ediyor musunuz?\n"
            "「👮」Sunucu ve Oluşum Kurallarını kabul ediyor musunuz?"
        ),
        color=0x1A1A2E,
    )
    embed.set_footer(
        text="Polis Departmanı • Başvuru Sistemi",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
    )
    embed.timestamp = discord.utils.utcnow()

    kanal = bot.get_channel(BASVURU_KANAL_ID)
    await kanal.send(embed=embed, view=BasvuruView())
    await interaction.followup.send("✅ Başvuru mesajı gönderildi!", ephemeral=True)


@basvurugonder.error
async def basvurugonder_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Admin yetkisi gerekiyor.", ephemeral=True)


# ──────────────────────────────────────────────
#  BOT HAZIR
# ──────────────────────────────────────────────
@bot.event
async def on_ready():
    bot.add_view(BasvuruView())  # persistent view kaydet
    await tree.sync()
    print(f"✅ Bot hazır: {bot.user}")


bot.run(os.environ["BOT_TOKEN"])
