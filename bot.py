import discord
from discord.ext import commands
from discord import app_commands
import os

BASVURU_KANAL_ID       = 1484188687440019644
BASVURU_GELEN_KANAL_ID = 1486072691172704276
MULAKAT_ONAY_ROLE_ID   = 1484188685757972580

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ── BUTON FONKSİYONLARI (view class yok, on_interaction yakalıyor) ─────────────

def basvuru_buton_view():
    """Başvuru kanalındaki tek buton"""
    view = discord.ui.View(timeout=None)
    btn  = discord.ui.Button(style=discord.ButtonStyle.primary, label="📝  BAŞVURU YAP", custom_id="basvuru_ac")
    view.add_item(btn)
    return view


def yetkili_view(user_id: int):
    """Forma gelen yetkili butonları"""
    view = discord.ui.View(timeout=None)
    uid  = str(user_id)
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅  Onayla",           custom_id=f"onay:{uid}"))
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger,  label="❌  Reddet",            custom_id=f"red:{uid}"))
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="🎤  Mülakat Onayı Ver", custom_id=f"mulakat:{uid}"))
    return view


# ── MODAL ──────────────────────────────────────────────────────────────────────
class BasvuruModal(discord.ui.Modal, title="🚔 Polis Departmanı Başvurusu"):
    ooc_isim = discord.ui.TextInput(label="「👮」 OOC İsminiz", placeholder="Adınız Soyadınız", max_length=50)
    ooc_yas  = discord.ui.TextInput(label="「👮」 OOC Yaşınız", placeholder="Örn: 20", max_length=3)
    fivem    = discord.ui.TextInput(label="「👮」 FiveM Saati | Map Bilgisi | Ses", placeholder="350 saat | Map: 8/10 | Ses: 7/10", max_length=100)
    ic       = discord.ui.TextInput(label="「👮」 IC İsim | IC Yaş | Legal Geçmiş?", placeholder="John Doe | 28 | Evet, 6 ay polis rolü", max_length=200)
    ek       = discord.ui.TextInput(label="「👮」 Aktiflik | Neden biz? | CK & Kural", style=discord.TextStyle.paragraph,
                                    placeholder="Aktifliğim: 4-5 saat\nNeden katılmak istiyorum: ...\nNeden alınmalıyım: ...\nCK & Kural: Evet/Evet", max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(title="🚔 POLİS DEPARTMANI BAŞVURUSU", color=0xF0A500)
        embed.set_author(name=f"{interaction.user} — Yeni Başvuru", icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="━━━━━━ 〔 OOC BİLGİLER 〕 ━━━━━━", value="\u200b", inline=False)
        embed.add_field(name="「👮」 OOC İsim", value=f"```{self.ooc_isim.value}```", inline=True)
        embed.add_field(name="「👮」 OOC Yaş",  value=f"```{self.ooc_yas.value}```",  inline=True)
        embed.add_field(name="「👮」 FiveM Saati | Map | Ses", value=f"```{self.fivem.value}```", inline=False)
        embed.add_field(name="━━━━━━ 〔 IC BİLGİLER 〕 ━━━━━━", value="\u200b", inline=False)
        embed.add_field(name="「👮」 IC İsim | IC Yaş | Legal Geçmiş", value=f"```{self.ic.value}```", inline=False)
        embed.add_field(name="━━━━━━ 〔 EK BİLGİLER 〕 ━━━━━━", value="\u200b", inline=False)
        embed.add_field(name="「👮」 Aktiflik | Motivasyon | CK & Kural", value=f"```{self.ek.value}```", inline=False)
        embed.set_footer(text=f"Kullanıcı ID: {interaction.user.id}", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        kanal = bot.get_channel(BASVURU_GELEN_KANAL_ID)
        await kanal.send(embed=embed, view=yetkili_view(interaction.user.id))
        await interaction.followup.send("✅ Başvurunuz iletildi! Yetkililerin incelemesini bekleyiniz.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"Modal hata: {error}")


# ── TÜM BUTONLARI YAKALA ────────────────────────────────────────────────────────
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get("custom_id", "")

    # Başvuru butonu
    if custom_id == "basvuru_ac":
        await interaction.response.send_modal(BasvuruModal())
        return

    # Yetkili butonları
    if ":" in custom_id and custom_id.split(":")[0] in ("onay", "red", "mulakat"):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)
            return

        await interaction.response.defer()
        action, uid = custom_id.split(":", 1)
        user_id = int(uid)
        hedef   = interaction.guild.get_member(user_id)
        embed   = interaction.message.embeds[0]

        if action == "onay":
            embed.colour = 0x2ECC71
            embed.title  = "🚔 POLİS BAŞVURUSU — ✅ ONAYLANDI"
            if hedef:
                dm = discord.Embed(title="✅ Başvurunuz Onaylandı!", color=0x2ECC71,
                    description="**Polis Departmanı** başvurunuz **kabul edildi!**\n\n> Mülakat onay permini aldıktan sonra mülakat kanalına geçebilirsin.\n> Başarılar! 🚔")
                dm.set_footer(text=f"Yetkili: {interaction.user}")
                dm.timestamp = discord.utils.utcnow()
                try:
                    await hedef.send(embed=dm)
                except discord.Forbidden:
                    pass
            await interaction.message.edit(embed=embed, view=None)
            await interaction.followup.send("✅ Onaylandı, DM gönderildi.", ephemeral=True)

        elif action == "red":
            embed.colour = 0xE74C3C
            embed.title  = "🚔 POLİS BAŞVURUSU — ❌ REDDEDİLDİ"
            if hedef:
                dm = discord.Embed(title="❌ Başvurunuz Reddedildi", color=0xE74C3C,
                    description="**Polis Departmanı** başvurunuz **reddedildi.**\n\n> Daha sonra tekrar başvurabilirsin.\n> İyi günler.")
                dm.set_footer(text=f"Yetkili: {interaction.user}")
                dm.timestamp = discord.utils.utcnow()
                try:
                    await hedef.send(embed=dm)
                except discord.Forbidden:
                    pass
            await interaction.message.edit(embed=embed, view=None)
            await interaction.followup.send("❌ Reddedildi, DM gönderildi.", ephemeral=True)

        elif action == "mulakat":
            if not hedef:
                await interaction.followup.send("❌ Kullanıcı sunucuda bulunamadı.", ephemeral=True)
                return
            rol = interaction.guild.get_role(MULAKAT_ONAY_ROLE_ID)
            if rol:
                try:
                    await hedef.add_roles(rol)
                except discord.Forbidden:
                    await interaction.followup.send("❌ Rol verilemedi, bot yetkilerini kontrol et.", ephemeral=True)
                    return
            embed.colour = 0x3498DB
            embed.title  = "🚔 POLİS BAŞVURUSU — 🎤 MÜLAKAT ONAYI VERİLDİ"
            dm = discord.Embed(title="🎤 Mülakat Onayı Verildi!", color=0x3498DB,
                description="**Mülakat Onay** permin verildi!\n\n> Mülakat kanalına girerek mülakatını tamamlayabilirsin.\n> Bol şans! 🚔")
            dm.set_footer(text=f"Yetkili: {interaction.user}")
            dm.timestamp = discord.utils.utcnow()
            try:
                await hedef.send(embed=dm)
            except discord.Forbidden:
                pass
            await interaction.message.edit(embed=embed, view=None)
            await interaction.followup.send("🎤 Mülakat onayı verildi, DM gönderildi.", ephemeral=True)


# ── SLASH COMMAND ───────────────────────────────────────────────────────────────
@bot.tree.command(name="basvurugonder", description="Başvuru butonunu kanala gönderir. (Sadece Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def basvurugonder(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="🚔 POLİS DEPARTMANI BAŞVURU SİSTEMİ",
        description=(
            "```\nBAŞVURUNUZ TEKER TEKER İNCELENECEKTİR\n```\n\n"
            "> **ZAMAN SIKINTISI OLMAYAN** ve **HARD ROL YAPABİLEN** arkadaşlar başvuru atabilir.\n"
            "> Mülakata girebilmek için başvurunuzun **onaylanması** ve **Mülakat Onay** perminizin olması gerekmektedir.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📋 **BAŞVURU FORMU İÇERİĞİ**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**[ OOC BİLGİLER ]**\n「👮」İsim\n「👮」Yaş\n「👮」FiveM Saati (200+)\n「👮」Map Bilgisi (?/10)\n「👮」Ses Kalınlığı (?/10)\n\n"
            "**[ IC BİLGİLER ]**\n「👮」IC İsim\n「👮」IC Yaş\n「👮」Daha önce legal rol yaptınız mı?\n\n"
            "**[ EK BİLGİLER ]**\n「👮」Aktiflik Süreniz\n「👮」Neden bize katılmak istiyorsunuz?\n"
            "「👮」Sizi neden almalıyız?\n「👮」CK yemeyi kabul ediyor musunuz?\n「👮」Sunucu ve Oluşum Kurallarını kabul ediyor musunuz?"
        ),
        color=0x1A1A2E,
    )
    embed.set_footer(text="Polis Departmanı • Başvuru Sistemi",
                     icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.timestamp = discord.utils.utcnow()

    kanal = bot.get_channel(BASVURU_KANAL_ID)
    await kanal.send(embed=embed, view=basvuru_buton_view())
    await interaction.followup.send("✅ Başvuru mesajı gönderildi!", ephemeral=True)


@basvurugonder.error
async def basvurugonder_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Admin yetkisi gerekiyor.", ephemeral=True)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot hazır: {bot.user}")


bot.run(os.environ["BOT_TOKEN"])
