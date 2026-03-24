import discord
from discord.ext import commands
from discord import app_commands
import os

# ── AYARLAR (ID'LER) ──────────────────────────────────────────────────────────
BASVURU_KANAL_ID       = 1484188687440019644  # Başvuru butonunun duracağı kanal
BASVURU_GELEN_KANAL_ID = 1486072691172704276  # Başvuruların yetkililere düştüğü kanal
MULAKAT_ONAY_ROLE_ID   = 1484188685757972580  # Onaylanan ve Mülakat Onayı alanlara verilecek rol
RED_ROLE_ID            = 1484188685757972581  # Reddedilenlere verilecek rol
YETKILI_ROL_ID         = 1484188685850120193  # Yeni başvuru gelince etiketlenecek yetkili rolü

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ── BUTON GÖRÜNÜMLERİ ──────────────────────────────────────────────────────────

def basvuru_buton_view():
    """Başvuru kanalındaki 'Başvuru Yap' butonu"""
    view = discord.ui.View(timeout=None)
    btn  = discord.ui.Button(style=discord.ButtonStyle.primary, label="📝  BAŞVURU YAP", custom_id="basvuru_ac")
    view.add_item(btn)
    return view

def yetkili_view(user_id: int):
    """Yetkili kanalına düşen yönetim butonları"""
    view = discord.ui.View(timeout=None)
    uid  = str(user_id)
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅  Onayla",           custom_id=f"onay:{uid}"))
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger,  label="❌  Reddet",            custom_id=f"red:{uid}"))
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="🎤  Mülakat Onayı Ver", custom_id=f"mulakat:{uid}"))
    return view

# ── BAŞVURU MODALI ─────────────────────────────────────────────────────────────

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

        # Yetkili kanalına mesaj gönder ve rolü etiketle
        kanal = bot.get_channel(BASVURU_GELEN_KANAL_ID)
        await kanal.send(
            content=f"<@&{YETKILI_ROL_ID}> yeni bir başvuru geldi!", 
            embed=embed, 
            view=yetkili_view(interaction.user.id)
        )
        
        await interaction.followup.send("✅ Başvurunuz iletildi! Yetkililerin incelemesini bekleyiniz.", ephemeral=True)

# ── TÜM ETKİLEŞİMLERİ YAKALAMA (BUTONLAR) ──────────────────────────────────────

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get("custom_id", "")

    # Başvuru formunu açma
    if custom_id == "basvuru_ac":
        await interaction.response.send_modal(BasvuruModal())
        return

    # Yetkili butonları (Onay, Red, Mülakat)
    if ":" in custom_id:
        action, uid = custom_id.split(":", 1)
        if action in ("onay", "red", "mulakat"):
            if not interaction.user.guild_permissions.manage_roles:
                await interaction.response.send_message("❌ Bu işlemi yapmak için yetkin yok.", ephemeral=True)
                return

            await interaction.response.defer()
            user_id = int(uid)
            hedef   = interaction.guild.get_member(user_id)
            embed   = interaction.message.embeds[0]

            if not hedef:
                await interaction.followup.send("❌ Kullanıcı sunucuda bulunamadı.", ephemeral=True)
                return

            # --- ONAY İŞLEMİ ---
            if action == "onay":
                rol = interaction.guild.get_role(MULAKAT_ONAY_ROLE_ID)
                if rol: await hedef.add_roles(rol)
                
                embed.colour = 0x2ECC71
                embed.title  = "🚔 POLİS BAŞVURUSU — ✅ ONAYLANDI"
                dm_text = "Başvurunuz **onaylandı**! Aramıza hoş geldiniz."
                msg_text = f"✅ {hedef.mention} onaylandı ve rolü verildi."

            # --- RED İŞLEMİ ---
            elif action == "red":
                rol = interaction.guild.get_role(RED_ROLE_ID)
                if rol: await hedef.add_roles(rol)
                
                embed.colour = 0xE74C3C
                embed.title  = "🚔 POLİS BAŞVURUSU — ❌ REDDEDİLDİ"
                dm_text = "Başvurunuz maalesef **reddedildi**."
                msg_text = f"❌ {hedef.mention} reddedildi ve red rolü verildi."

            # --- MÜLAKAT ONAYI İŞLEMİ ---
            elif action == "mulakat":
                rol = interaction.guild.get_role(MULAKAT_ONAY_ROLE_ID)
                if rol: await hedef.add_roles(rol)
                
                embed.colour = 0x3498DB
                embed.title  = "🚔 POLİS BAŞVURUSU — 🎤 MÜLAKAT ONAYI VERİLDİ"
                dm_text = "Mülakat perminiz tanımlandı! Mülakat kanalına geçebilirsiniz."
                msg_text = f"🎤 {hedef.mention} mülakat onayı aldı ve rolü verildi."

            # Ortak DM Gönderme ve Mesaj Güncelleme
            try:
                dm = discord.Embed(title=embed.title, description=dm_text, color=embed.color)
                dm.set_footer(text=f"İşlemi Yapan: {interaction.user}")
                await hedef.send(embed=dm)
            except: pass

            await interaction.message.edit(embed=embed, view=None)
            await interaction.followup.send(msg_text, ephemeral=True)

# ── SLASH KOMUTLARI ──────────────────────────────────────────────────────────

@bot.tree.command(name="basvurugonder", description="Başvuru butonunu kanala gönderir.")
@app_commands.checks.has_permissions(administrator=True)
async def basvurugonder(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="🚔 POLİS DEPARTMANI BAŞVURU SİSTEMİ",
        description=(
            "```\nBAŞVURUNUZ TEKER TEKER İNCELENECEKTİR\n```\n"
            "Mülakata girebilmek için başvurunuzun **onaylanması** gerekmektedir.\n\n"
            "Aşağıdaki butona tıklayarak formu doldurabilirsiniz."
        ),
        color=0x1A1A2E,
    )
    embed.set_footer(text="Polis Departmanı • Başvuru Sistemi")
    embed.timestamp = discord.utils.utcnow()

    kanal = bot.get_channel(BASVURU_KANAL_ID)
    await kanal.send(embed=embed, view=basvuru_buton_view())
    await interaction.followup.send("✅ Başvuru mesajı gönderildi!", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot Aktif: {bot.user}")

# Bot Tokenini Buraya Gir
bot.run(os.environ["BOT_TOKEN"])
