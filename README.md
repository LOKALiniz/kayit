# 🚔 SASP Kayıt Botu – Kurulum Rehberi

## 1. Gereksinimler
```
pip install -r requirements.txt
```

## 2. bot.py içinde doldurman gerekenler

| Değişken | Açıklama | Mevcut Değer |
|---|---|---|
| `BOT_TOKEN` | Discord bot tokenin | `"BOT_TOKEN_BURAYA"` |
| `KAYITLI_ROL_ID` | Kayıt olunca verilecek rol | `1484188685812629576` ✅ |
| `KAYITSIZ_ROL_ID` | Başvurucu rolü | `1484188685757972582` ✅ |
| `ADMIN_KANAL_ID` | Başvuruların düşeceği kanal ID'si | `0` ← DEĞİŞTİR |
| `RUTBE_ROLLERI` | Her rütbenin rol ID'si | Hepsi `0` ← DEĞİŞTİR |

## 3. Bot izinleri (Discord Developer Portal)
- `bot` scope
- `applications.commands` scope
- İzinler: `Manage Roles`, `Send Messages`, `Read Messages`, `Read Message History`

## 4. Kullanım Akışı

### Başvuru Paneli Kur
```
/basurugonder
```
→ Kanalda "📝 Başvur" butonlu mesaj yayınlanır.

### Kayıtsız üye başvurur
1. "📝 Başvur" butonuna basar
2. Form açılır, doldurur
3. Başvuru **ADMIN_KANAL_ID**'ye düşer

### Yetkili kayıt işlemi yapar
```
/saspkayıt @kullanıcı
```
1. Rütbe dropdown'dan seçilir (Cadet, Trooper I, vb.)
2. **✅ Kabul Et** → Rütbe rolü + Kayıtlı rolü verilir, Kayıtsız rolü alınır, kullanıcıya DM gider
3. **❌ Red Et** → Kullanıcıya DM ile "başvurun red edildi" mesajı gider

## 5. DM Mesajları

**Kabul:**
> 🚔 SASP Başvurun Kabul Edildi!
> Rütben: **Cadet**
> Sunucuya hoş geldin!

**Red:**
> 🚔 SASP Başvurun Red Edildi ❌
> Üzgünüz, daha sonra tekrar başvurabilirsin.
