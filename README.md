# Extron Virtual Devices

Home Assistant custom integration for Extron IPL PRO S3.

## Özellikler

- Epson projektör aç/kapat ve durum geri bildirimi
- Kramer VS-88H2A video çıkış/giriş seçimi
- Kramer harici ses giriş seçimi
- Analog OUT 1 ses seviyesi: 0–100
- Ses aç / ses kıs butonları
- Ses mute switch'i
- **Kramer Code Send** metin kutusu

## Code Send kullanımı

Cihaz sayfasındaki `Kramer VS-88H2A Code Send` kutusuna tek bir
Kramer Protocol 3000 komutu yazıp **Ayarla** düğmesine basın.
Komut `#` ile başlamalıdır. Örnekler:

```text
#VID? 4
#AV 4>2
#VOLUME? 1
#VOLUME 1,75
#EXT-AUD?
#MODEL?
```

Bu özellik için Extron `main.py` dosyasının `MATRIX_RAW:` komutunu
desteklemesi gerekir.

## Kurulum

`custom_components/extron_virtual_devices` klasörünü Home Assistant
`/config/custom_components/` altına kopyalayın ve Home Assistant'ı
yeniden başlatın.
