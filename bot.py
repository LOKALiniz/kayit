import discord
from discord.ext import commands
from discord import app_commands
import os

# ─────────────────────────────────────────────
#  KONFİGÜRASYON
# ─────────────────────────────────────────────
BOT_TOKEN       = os.environ["BOT_TOKEN"]
KAYITLI_ROL_ID  = 1484188685812629576
KAYITSIZ_ROL_ID = 1484188685757972582
ADMIN_KANAL_ID  = 1486072691172704276

RUTBE_ROLLERI: dict[str, int] = {
    "Cadet":         1484188685812629581,
    "Trooper I":     1484188685812629582,
    "Trooper II":    1484188685812629583,
    "Trooper III":   1484188685812629584,
    "Trooper III+I": 1484188685824950332,
    "Corporal":      1484188685824950333,
    "Sergeant I":    1484188685824950339,
    "Sergeant II":   1484188685824950340,
    "Lieutenant I":  1484188685824950341,
    "Lieutenant II": 1484188685850120192,
    "Captain":       1484188685850120193,
}
# ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Geçici hafıza: {hedef_user_id: seçilen_rütbe}
secilen_rutbe: dict[int, str] = {}


# ══════════════════════════════════════════════
#  BAŞVURU FORMU – Modal
# ══════════════════════════════════════════════
class BasvuruFormu(discord.ui.Modal, title="📋 SASP Başvuru Formu"):

    ooc_isim = discord.ui.TextInput(
        label="OOC İsim",
        placeholder="Gerçek karakterin adı (OOC)",
        max_length=32,
    )
    yas = discord.ui.TextInput(
        label="Yaş",
        placeholder="Kaç yaşındasın?",
        max_length=3,
    )
    fivem_saati = discord.ui.TextInput(
        label="FiveM Saati (200+ olmalı)",
        placeholder="Örn: 270",
        max_length=6,
    )
    map_ses = discord.ui.TextInput(
        label="Map Bilgisi / Ses Kalınlığı (?/10)",
        placeholder="Örn: Map: 8/10 | Ses: 7/10",
        max_length=40,
    )
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
        # Önce kullanıcıya hemen yanıt ver
        await interaction.response.send_message(
            "✅ Başvurun alındı! Yetkililerin incelemesini bekle.",
            ephemeral=True,
        )

        embed = discord.Embed(title="🚔 Yeni SASP Başvurusu", color=0x1a6ebd)
        embed.set_author(
            name=str(interaction.user),
            icon_url=interaction.user.display_avatar.url,
        )
        embed.add_field(name="「👮」OOC İsim",      value=self.ooc_isim.value,    inline=True)
        embed.add_field(name="「👮」Yaş",            value=self.yas.value,         inline=True)
        embed.add_field(name="「👮」FiveM Saati",    value=self.fivem_saati.value, inline=True)
        embed.add_field(name="「👮」Map / Ses",      value=self.map_ses.value,     inline=True)
        embed.add_field(name="「📄」IC & Ek Bilgi", value=self.ic_ve_ek.value,    inline=False)
        embed.set_footer(text=f"Başvurucu ID: {interaction.user.id}")

        kanal = bot.get_channel(ADMIN_KANAL_ID)
        if kanal:
            await kanal.send(
                f"📥 Yeni başvuru: {interaction.user.mention}",
                embed=embed,
                view=BasvuruBildirimView(),
            )


# ══════════════════════════════════════════════
#  BAŞVURU BİLDİRİM VIEW (kalıcı, sadece bilgi)
# ══════════════════════════════════════════════
class BasvuruBildirimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📋 /saspkayit komutuyla işle",
        style=discord.ButtonStyle.secondary,
        disabled=True,
        custom_id="sasp_bilgi_buton",
    )
    async def bilgi(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


# ══════════════════════════════════════════════
#  RÜTBE SEÇİMİ – hedef ID custom_id'ye gömülü
# ══════════════════════════════════════════════
class RutbeSecici(discord.ui.Select):
    def __init__(self, hedef_id: int):
        self.hedef_id = hedef_id
        options = [
            discord.SelectOption(label=r, value=r)
            for r in RUTBE_ROLLERI
        ]
        super().__init__(
            placeholder="Rütbe seç…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"rutbe_{hedef_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        secilen_rutbe[self.hedef_id] = self.values[0]
        await interaction.response.send_message(
            f"✅ Rütbe **{self.values[0]}** seçildi. Şimdi Kabul Et veya Red Et butonuna bas.",
            ephemeral=True,
        )


# ══════════════════════════════════════════════
#  KAYIT VIEW – hedef ID custom_id'ye gömülü
#  Restart sonrası member guild'den çekiliyor
# ══════════════════════════════════════════════
class KayitView(discord.ui.View):
    def __init__(self, hedef_id: int):
        super().__init__(timeout=None)
        self.hedef_id = hedef_id
        self.add_item(RutbeSecici(hedef_id))

    async def get_hedef(self, guild: discord.Guild) -> discord.Member | None:
        hedef = guild.get_member(self.hedef_id)
        if hedef is None:
            try:
                hedef = await guild.fetch_member(self.hedef_id)
            except Exception:
                hedef = None
        return hedef

    @discord.ui.button(
        label="✅ Kabul Et",
        style=discord.ButtonStyle.success,
        custom_id="sasp_kabul",
    )
    async def kabul(self, interaction: discord.Interaction, button: discord.ui.Button):
        rutbe_adi = secilen_rutbe.get(self.hedef_id)
        if not rutbe_adi:
            await interaction.response.send_message(
                "⚠️ Önce yukarıdaki menüden bir rütbe seç!",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        hedef = await self.get_hedef(interaction.guild)
        if hedef is None:
            await interaction.edit_original_response(
                content="❌ Kullanıcı sunucuda bulunamadı.", view=None
            )
            return

        guild = interaction.guild
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

        await interaction.edit_original_response(content=sonuc, view=None)
        secilen_rutbe.pop(self.hedef_id, None)

    @discord.ui.button(
        label="❌ Red Et",
        style=discord.ButtonStyle.danger,
        custom_id="sasp_red",
    )
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        hedef = await self.get_hedef(interaction.guild)
        if hedef is None:
            await interaction.edit_original_response(
                content="❌ Kullanıcı sunucuda bulunamadı.", view=None
            )
            return

        try:
            dm_embed = discord.Embed(
                title="🚔 SASP Başvurun Red Edildi",
                description=(
                    f"Merhaba **{hedef.display_name}**,\n\n"
                    "Üzgünüz, SASP başvurun **red** edilmiştir. ❌\n\n"
                    "Daha sonra tekrar başvurabilirsin.\n"
                    "Başarılar!"
                ),
                color=0xe74c3c,
            )
            await hedef.send(embed=dm_embed)
            dm_bilgi = "✅ Kullanıcıya DM ile bildirildi."
        except discord.Forbidden:
            dm_bilgi = "⚠️ DM gönderemedim (kullanıcı DM kapalı)."

        await interaction.edit_original_response(
            content=f"❌ **{hedef.mention}** başvurusu red edildi. {dm_bilgi}",
            view=None,
        )
        secilen_rutbe.pop(self.hedef_id, None)


# ══════════════════════════════════════════════
#  BAŞVURU BUTONU VIEW (kalıcı)
# ══════════════════════════════════════════════
class BasvuruButonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📝 Başvur",
        style=discord.ButtonStyle.primary,
        custom_id="sasp_basvur_buton",
    )
    async def basvur(self, interaction: discord.Interaction, button: discord.ui.Button):
        kayitsiz_rol = interaction.guild.get_role(KAYITSIZ_ROL_ID)
        if kayitsiz_rol and kayitsiz_rol not in interaction.user.roles:
            await interaction.response.send_message(
                "⚠️ Bu butonu kullanmak için **Kayıtsız** rolüne sahip olman gerekiyor.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(BasvuruFormu())


# ══════════════════════════════════════════════
#  SLASH KOMUTLARI
# ══════════════════════════════════════════════
@bot.tree.command(name="saspkayit", description="SASP üyesini kayıt et (yetkili komutu)")
@app_commands.describe(uye="Kayıt edilecek kişi")
async def sasp_kayit(interaction: discord.Interaction, uye: discord.Member):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "🚫 Bu komutu kullanma yetkin yok.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"🚔 SASP Kayıt – {uye.display_name}",
        description=(
            f"Kullanıcı: {uye.mention} (`{uye.id}`)\n"
            "Aşağıdan **rütbe seç**, ardından Kabul Et veya Red Et butonuna bas."
        ),
        color=0x1a6ebd,
    )
    embed.set_thumbnail(url=uye.display_avatar.url)

    await interaction.response.send_message(
        embed=embed,
        view=KayitView(uye.id),   # ← artık member değil sadece ID
        ephemeral=False,
    )


@bot.tree.command(name="basurugonder", description="Başvuru butonunu kanalda yayınla")
async def basvuru_gonder(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("🚫 Sadece adminler kullanabilir.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🚔 San Andreas State Police – Başvuru",
        description=(
            "SASP'a katılmak istiyorsan aşağıdaki **📝 Başvur** butonuna tıklayarak formu doldur.\n\n"
            "**Gereksinimler:**\n"
            "• 200+ FiveM saati\n"
            "• Sunucu ve oluşum kurallarını kabul etmek\n"
            "• CK kabulü"
        ),
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
    bot.add_view(BasvuruBildirimView())

    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash komutu sync edildi.")
    except Exception as e:
        print(f"Sync hatası: {e}")

    print(f"🤖 Bot hazır → {bot.user} ({bot.user.id})")


bot.run(BOT_TOKEN)
