import discord
from discord.ext import commands
from discord import app_commands
import os

# ──────────────────────────────────────────────
#  KANAL / ROL ID'LERİ
# ──────────────────────────────────────────────
BASVURU_KANAL_ID       = 1484188687440019644  # butonun gönderileceği kanal
BASVURU_GELEN_KANAL_ID = 1486072691172704276  # formların düşeceği kanal
MULAKAT_ONAY_ROLE_ID   = 1484188685757972580  # mülakat onay rolü
MULAKAT_RED_ROLE_ID    = 1484188685757972581  # mülakat red rolü

# ──────────────────────────────────────────────
#  BOT KURULUMU
# ──────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ──────────────────────────────────────────────
#  MODAL (FORM)
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
        placeholder="Örn: John Doe | 28 | Evet, 6 ay polis rolü yaptım",
        required=True,
        max_length=200,
    )
    ek_bilgiler = discord.ui.TextInput(
        label="「👮」 Aktiflik | Neden biz? | CK & Kural Kabulü",
        placeholder="Aktifliğim: Her gün 4-5 saat\nNeden katılmak istiyorum: ...\nNeden alınmalıyım: ...\nCK & Kural kabulü: Evet / Evet",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="🚔 POLİS DEPARTMANI BAŞVURUSU",
            color=0xF0A500,
        )
        embed.set_author(
            name=f"{interaction.user} — Yeni Başvuru",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.add_field(
            name="━━━━━━ 〔 OOC BİLGİLER 〕 ━━━━━━",
            value="\u200b",
            inline=False,
        )
        embed.add_field(name="「👮」 OOC İsim", value=f"```{self.ooc_isim.value}```", inline=True)
        embed.add_field(name="「👮」 OOC Yaş", value=f"```{self.ooc_yas.value}```", inline=True)
        embed.add_field(
            name="「👮」 FiveM Saati | Map | Ses",
            value=f"```{self.fivem_bilgiler.value}```",
            inline=False,
        )
        embed.add_field(
            name="━━━━━━ 〔 IC BİLGİLER 〕 ━━━━━━",
            value="\u200b",
            inline=False,
        )
        embed.add_field(
            name="「👮」 IC İsim | IC Yaş | Legal Geçmiş",
            value=f"```{self.ic_bilgiler.value}```",
            inline=False,
        )
        embed.add_field(
            name="━━━━━━ 〔 EK BİLGİLER 〕 ━━━━━━",
            value="\u200b",
            inline=False,
        )
        embed.add_field(
            name="「👮」 Aktiflik | Motivasyon | CK & Kural",
            value=f"```{self.ek_bilgiler.value}```",
            inline=False,
        )
        embed.set_footer(
            text=f"Kullanıcı ID: {interaction.user.id}",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = discord.utils.utcnow()

        view = YetkiliView(user_id=interaction.user.id)

        kanal = bot.get_channel(BASVURU_GELEN_KANAL_ID)
        await kanal.send(embeds=[embed], view=view)

        await interaction.followup.send(
            "✅ Başvurunuz başarıyla iletildi! Yetkililerin incelemesini bekleyiniz.",
            ephemeral=True,
        )


# ──────────────────────────────────────────────
#  BAŞVURU BUTONU (başvuru kanalındaki buton)
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
        await interaction.response.send_modal(BasvuruModal())


# ──────────────────────────────────────────────
#  YETKİLİ BUTONLARI (form düştükten sonra)
# ──────────────────────────────────────────────
class YetkiliView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    def _yetkili_mi(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.manage_roles

    async def _guncelle_embed(self, interaction: discord.Interaction, renk: int, baslik: str):
        embed = interaction.message.embeds[0]
        embed.color = renk
        embed.title = baslik
        await interaction.message.edit(embed=embed, view=None)

    @discord.ui.button(label="✅  Onayla", style=discord.ButtonStyle.success, custom_id="onay")
    async def onay(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._yetkili_mi(interaction):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)

        await interaction.response.defer()

        hedef = interaction.guild.get_member(self.user_id)
        if hedef:
            dm_embed = discord.Embed(
                title="✅ Başvurunuz Onaylandı!",
                description=(
                    "**Polis Departmanı** başvurunuz **kabul edildi!**\n\n"
                    "> Mülakat onay permini aldıktan sonra mülakat kanalına geçebilirsin.\n"
                    "> Başarılar dileriz! 🚔"
                ),
                color=0x2ECC71,
            )
            dm_embed.set_footer(text=f"Yetkili: {interaction.user}")
            dm_embed.timestamp = discord.utils.utcnow()
            try:
                await hedef.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        await self._guncelle_embed(interaction, 0x2ECC71, "🚔 POLİS DEPARTMANI BAŞVURUSU — ✅ ONAYLANDI")
        await interaction.followup.send(f"✅ Başvuru onaylandı, kullanıcıya DM gönderildi.", ephemeral=True)

    @discord.ui.button(label="❌  Reddet", style=discord.ButtonStyle.danger, custom_id="red")
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._yetkili_mi(interaction):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)

        await interaction.response.defer()

        hedef = interaction.guild.get_member(self.user_id)
        if hedef:
            dm_embed = discord.Embed(
                title="❌ Başvurunuz Reddedildi",
                description=(
                    "**Polis Departmanı** başvurunuz **reddedildi.**\n\n"
                    "> Daha sonra tekrar başvurabilirsin.\n"
                    "> İyi günler dileriz."
                ),
                color=0xE74C3C,
            )
            dm_embed.set_footer(text=f"Yetkili: {interaction.user}")
            dm_embed.timestamp = discord.utils.utcnow()
            try:
                await hedef.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        await self._guncelle_embed(interaction, 0xE74C3C, "🚔 POLİS DEPARTMANI BAŞVURUSU — ❌ REDDEDİLDİ")
        await interaction.followup.send(f"❌ Başvuru reddedildi, kullanıcıya DM gönderildi.", ephemeral=True)

    @discord.ui.button(label="🎤  Mülakat Onayı Ver", style=discord.ButtonStyle.primary, custom_id="mulakat")
    async def mulakat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._yetkili_mi(interaction):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)

        await interaction.response.defer()

        hedef = interaction.guild.get_member(self.user_id)
        if not hedef:
            return await interaction.followup.send("❌ Kullanıcı sunucuda bulunamadı.", ephemeral=True)

        rol = interaction.guild.get_role(MULAKAT_ONAY_ROLE_ID)
        if rol:
            try:
                await hedef.add_roles(rol)
            except discord.Forbidden:
                return await interaction.followup.send("❌ Rol verilemedi, bot yetkilerini kontrol et.", ephemeral=True)

        dm_embed = discord.Embed(
            title="🎤 Mülakat Onayı Verildi!",
            description=(
                "**Mülakat Onay** permin verildi!\n\n"
                "> Artık mülakat kanalına girerek mülakatını tamamlayabilirsin.\n"
                "> Bol şans! 🚔"
            ),
            color=0x3498DB,
        )
        dm_embed.set_footer(text=f"Yetkili: {interaction.user}")
        dm_embed.timestamp = discord.utils.utcnow()
        try:
            await hedef.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        await self._guncelle_embed(interaction, 0x3498DB, "🚔 POLİS DEPARTMANI BAŞVURUSU — 🎤 MÜLAKAT ONAY VERİLDİ")
        await interaction.followup.send(f"🎤 Mülakat onayı verildi, kullanıcıya DM gönderildi.", ephemeral=True)


# ──────────────────────────────────────────────
#  SLASH COMMAND: /basvurugonder
# ──────────────────────────────────────────────
@tree.command(name="basvurugonder", description="Başvuru butonunu belirtilen kanala gönderir. (Sadece Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def basvurugonder(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="🚔 POLİS DEPARTMANI BAŞVURU SİSTEMİ",
        description=(
            "```\n"
            "BAŞVURUNUZ TEKER TEKER İNCELENECEKTİR\n"
            "```\n\n"
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
        await interaction.response.send_message("❌ Bu komutu kullanmak için **Admin** yetkisine ihtiyacın var.", ephemeral=True)


# ──────────────────────────────────────────────
#  BOT HAZIR
# ──────────────────────────────────────────────
@bot.event
async def on_ready():
    # Persistent view'ları kaydet (bot restart'ta butonlar çalışmaya devam eder)
    bot.add_view(BasvuruView())
    # Slash command'ları sync et
    await tree.sync()
    print(f"✅ Bot hazır: {bot.user} | Slash komutlar sync edildi.")


bot.run(os.environ["BOT_TOKEN"])
