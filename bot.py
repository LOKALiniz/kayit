import discord
from discord.ext import commands
from discord import app_commands
import os

# ─────────────────────────────────────────────
BOT_TOKEN        = os.environ.get("BOT_TOKEN")
KAYITLI_ROL_ID   = 1484188685812629576
KAYITSIZ_ROL_ID  = 1484188685757972582
ADMIN_KANAL_ID   = 1486072691172704276
KAYIT_KANAL_ID   = 1484188687440019644

RUTBE_ROLLERI: dict[str, int] = {
    "Cadet":           1484188685812629581,
    "Trooper I":       1484188685812629582,
    "Trooper II":      1484188685812629583,
    "Trooper III":     1484188685812629584,
    "Trooper III+I":   1484188685824950332,
    "Corporal":        1484188685824950333,
    "Sergeant I":      1484188685824950339,
    "Sergeant II":     1484188685824950340,
    "Lieutenant I":    1484188685824950341,
    "Lieutenant II":   1484188685850120192,
    "Captain":         1484188685850120193,
}
# ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
secilen_rutbe: dict[int, str] = {}


# ══════════════════════════════════════════════
#  BAŞVURU FORMU
# ══════════════════════════════════════════════
class BasvuruFormu(discord.ui.Modal, title="📋 SASP Başvuru Formu"):

    ooc_isim = discord.ui.TextInput(label="OOC İsim", placeholder="Gerçek ismin (OOC)", max_length=32)
    yas = discord.ui.TextInput(label="Yaş", placeholder="Kaç yaşındasın?", max_length=3)
    fivem_saati = discord.ui.TextInput(label="FiveM Saati (200+)", placeholder="Örn: 270", max_length=6)
    map_ses = discord.ui.TextInput(label="Map Bilgisi / Ses Kalınlığı (?/10)", placeholder="Map: 8/10 | Ses: 7/10", max_length=40)
    ic_ve_ek = discord.ui.TextInput(
        label="IC Bilgiler & Ek Bilgiler",
        style=discord.TextStyle.paragraph,
        placeholder=(
            "IC İsim | IC Yaş | Daha önce legal rol?\n"
            "Aktiflik | Neden katılmak istiyorsun? | Neden alınmalısın?\n"
            "CK kabul | Kural kabul"
        ),
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Başvurun alındı! Yetkililerin incelemesini bekle.", ephemeral=True)

        embed = discord.Embed(title="🚔 Yeni SASP Başvurusu", color=0x1a6ebd)
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="「👮」OOC İsim",      value=self.ooc_isim.value,    inline=True)
        embed.add_field(name="「👮」Yaş",            value=self.yas.value,         inline=True)
        embed.add_field(name="「👮」FiveM Saati",    value=self.fivem_saati.value, inline=True)
        embed.add_field(name="「👮」Map / Ses",      value=self.map_ses.value,     inline=True)
        embed.add_field(name="「📄」IC & Ek Bilgi", value=self.ic_ve_ek.value,    inline=False)
        embed.set_footer(text=f"Başvurucu ID: {interaction.user.id}")

        kanal = bot.get_channel(ADMIN_KANAL_ID)
        if kanal:
            await kanal.send(f"📥 Yeni başvuru: {interaction.user.mention}", embed=embed)


# ══════════════════════════════════════════════
#  on_interaction — tüm buton/select olaylarını yakala
# ══════════════════════════════════════════════
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        await bot.process_application_commands(interaction)
        return

    if interaction.type != discord.InteractionType.component:
        return

    custom_id: str = interaction.data.get("custom_id", "")

    if custom_id == "sasp_basvur_buton":
        kayitli_rol = interaction.guild.get_role(KAYITLI_ROL_ID)
        if kayitli_rol and kayitli_rol in interaction.user.roles:
            await interaction.response.send_message("⚠️ Zaten SASP üyesisin, tekrar başvuramazsın.", ephemeral=True)
            return
        await interaction.response.send_modal(BasvuruFormu())

    elif custom_id.startswith("rutbe_"):
        hedef_id = int(custom_id.split("_", 1)[1])
        secilen_deger = interaction.data["values"][0]
        secilen_rutbe[hedef_id] = secilen_deger
        await interaction.response.send_message(
            f"✅ Rütbe **{secilen_deger}** seçildi. Şimdi Kabul Et veya Red Et butonuna bas.",
            ephemeral=True,
        )

    elif custom_id.startswith("sasp_kabul_"):
        hedef_id = int(custom_id.split("_", 2)[2])
        rutbe_adi = secilen_rutbe.get(hedef_id)

        if not rutbe_adi:
            await interaction.response.send_message("⚠️ Önce yukarıdaki menüden bir rütbe seç!", ephemeral=True)
            return

        await interaction.response.defer()

        guild = interaction.guild
        try:
            hedef = guild.get_member(hedef_id) or await guild.fetch_member(hedef_id)
        except Exception:
            await interaction.edit_original_response(content="❌ Kullanıcı sunucuda bulunamadı.")
            return

        hatalar: list[str] = []

        kayitli_rol = guild.get_role(KAYITLI_ROL_ID)
        if kayitli_rol:
            try:
                await hedef.add_roles(kayitli_rol, reason="SASP Kayıt – Kabul")
            except discord.Forbidden:
                hatalar.append("Kayıtlı rolü veremedim (yetki eksik).")
        else:
            hatalar.append(f"Kayıtlı rol bulunamadı (ID: {KAYITLI_ROL_ID}).")

        rutbe_rol_id = RUTBE_ROLLERI.get(rutbe_adi, 0)
        if rutbe_rol_id:
            rutbe_rol = guild.get_role(rutbe_rol_id)
            if rutbe_rol:
                try:
                    await hedef.add_roles(rutbe_rol, reason=f"SASP Kayıt – {rutbe_adi}")
                except discord.Forbidden:
                    hatalar.append(f"{rutbe_adi} rolünü veremedim.")
            else:
                hatalar.append(f"{rutbe_adi} rolü sunucuda bulunamadı.")
        else:
            hatalar.append(f"`{rutbe_adi}` için rol ID'si ayarlanmamış.")

        kayitsiz_rol = guild.get_role(KAYITSIZ_ROL_ID)
        if kayitsiz_rol and kayitsiz_rol in hedef.roles:
            try:
                await hedef.remove_roles(kayitsiz_rol, reason="SASP Kayıt tamamlandı")
            except discord.Forbidden:
                hatalar.append("Kayıtsız rolünü kaldıramadım.")

        try:
            dm_embed = discord.Embed(
                title="🚔 SASP Başvurun Kabul Edildi!",
                description=(
                    f"Merhaba **{hedef.display_name}**,\n\n"
                    f"SASP başvurun **kabul** edilmiştir. 🎉\n"
                    f"Rütben: **{rutbe_adi}**\n\n"
                    "Sunucuya hoş geldin, görevine başarılar!"
                ),
                color=0x2ecc71,
            )
            await hedef.send(embed=dm_embed)
        except discord.Forbidden:
            hatalar.append("DM gönderemedim (kullanıcı DM kapalı).")

        sonuc = f"✅ **{hedef.mention}** kayıt edildi → Rütbe: **{rutbe_adi}**"
        if hatalar:
            sonuc += "\n\n⚠️ Bazı sorunlar:\n" + "\n".join(f"• {h}" for h in hatalar)

        await interaction.edit_original_response(content=sonuc)
        secilen_rutbe.pop(hedef_id, None)

    elif custom_id.startswith("sasp_red_"):
        hedef_id = int(custom_id.split("_", 2)[2])

        await interaction.response.defer()

        guild = interaction.guild
        try:
            hedef = guild.get_member(hedef_id) or await guild.fetch_member(hedef_id)
        except Exception:
            await interaction.edit_original_response(content="❌ Kullanıcı sunucuda bulunamadı.")
            return

        try:
            dm_embed = discord.Embed(
                title="🚔 SASP Başvurun Red Edildi",
                description=(
                    f"Merhaba **{hedef.display_name}**,\n\n"
                    "Üzgünüz, SASP başvurun **red** edilmiştir. ❌\n\n"
                    "Daha sonra tekrar başvurabilirsin.\nBaşarılar!"
                ),
                color=0xe74c3c,
            )
            await hedef.send(embed=dm_embed)
            dm_bilgi = "✅ Kullanıcıya DM ile bildirildi."
        except discord.Forbidden:
            dm_bilgi = "⚠️ DM gönderemedim (kullanıcı DM kapalı)."

        await interaction.edit_original_response(
            content=f"❌ **{hedef.mention}** başvurusu red edildi. {dm_bilgi}"
        )
        secilen_rutbe.pop(hedef_id, None)


# ══════════════════════════════════════════════
#  BAŞVURU BUTONU VIEW (kalıcı)
# ══════════════════════════════════════════════
class BasvuruButonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Başvur", style=discord.ButtonStyle.primary, custom_id="sasp_basvur_buton")
    async def basvur(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass  # on_interaction tarafından ele alınıyor


# ══════════════════════════════════════════════
#  KAYIT MESAJI BUILDER
# ══════════════════════════════════════════════
def kayit_view(hedef_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)

    select = discord.ui.Select(
        placeholder="Rütbe seç…",
        min_values=1,
        max_values=1,
        options=[discord.SelectOption(label=r, value=r) for r in RUTBE_ROLLERI],
        custom_id=f"rutbe_{hedef_id}",
    )
    view.add_item(select)

    view.add_item(discord.ui.Button(
        label="✅ Kabul Et",
        style=discord.ButtonStyle.success,
        custom_id=f"sasp_kabul_{hedef_id}",
    ))
    view.add_item(discord.ui.Button(
        label="❌ Red Et",
        style=discord.ButtonStyle.danger,
        custom_id=f"sasp_red_{hedef_id}",
    ))

    return view


# ══════════════════════════════════════════════
#  SLASH KOMUTLARI
# ══════════════════════════════════════════════
@bot.tree.command(name="saspkayit", description="SASP üyesini kayıt et (yetkili komutu)")
@app_commands.describe(uye="Kayıt edilecek kişi")
async def sasp_kayit(interaction: discord.Interaction, uye: discord.Member):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("🚫 Bu komutu kullanma yetkin yok.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🚔 SASP Kayıt – {uye.display_name}",
        description=f"Kullanıcı: {uye.mention} (`{uye.id}`)\nAşağıdan **rütbe seç**, ardından Kabul Et veya Red Et butonuna bas.",
        color=0x1a6ebd,
    )
    embed.set_thumbnail(url=uye.display_avatar.url)
    await interaction.response.send_message(embed=embed, view=kayit_view(uye.id))


@bot.tree.command(name="basurugonder", description="Başvuru butonunu kanalda yayınla")
async def basvuru_gonder(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("🚫 Sadece adminler kullanabilir.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🚔 San Andreas State Police – Başvuru",
        description="SASP'a katılmak istiyorsan aşağıdaki **📝 Başvur** butonuna tıklayarak formu doldur.\n\n**Gereksinimler:**\n• 200+ FiveM saati\n• Sunucu ve oluşum kurallarını kabul etmek\n• CK kabulü",
        color=0x1a6ebd,
    )
    await interaction.channel.send(embed=embed, view=BasvuruButonView())
    await interaction.response.send_message("✅ Başvuru mesajı gönderildi.", ephemeral=True)


# ══════════════════════════════════════════════
#  BOT HAZIR
# ══════════════════════════════════════════════
@bot.event
async def on_ready():
    bot.add_view(BasvuruButonView())
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash komutu sync edildi.")
    except Exception as e:
        print(f"Sync hatası: {e}")
    print(f"🤖 Bot hazır → {bot.user} ({bot.user.id})")


bot.run(BOT_TOKEN)
