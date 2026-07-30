# Extron Virtual Devices 1.2.0

Bu paket üç Home Assistant select varlığı oluşturur:

- `select.kramer_vs_88h2a_secili_cikis`
- `select.kramer_vs_88h2a_aktif_giris`
- `select.kramer_vs_88h2a_aktif_ses`

## Ses akışı

Home Assistant:

`MATRIX_AUDIO:4`

Extron:

`#EXT-AUD 0,1,1,4\r`

Kramer geri bildirimi:

`~01@EXT-AUD 0,1,1,4`

Extron → Home Assistant:

`MATRIX_AUDIO_STATE:4`

## Kurulum

1. ZIP içindeki `custom_components/extron_virtual_devices` klasörünü Home Assistant'taki `/config/custom_components/` içine kopyalayın.
2. Home Assistant'ı yeniden başlatın.
3. Entegrasyonu kaldırmayın; mevcut kayıt yeni kodla açılmalıdır.
4. Extron Global Scripter projesinde mevcut `main.py` dosyasını paketteki `main.py` ile değiştirin.
5. Extron projesini yeniden yükleyin.
6. HACS kullanıyorsanız sürüm önbelleği nedeniyle entegrasyonu yeniden indirin veya Home Assistant'ı yeniden başlatın.

## Not

`#EXT-AUD?` sorgusunun VS-88H2A firmware sürümündeki kesin biçimi farklıysa, komut gönderiminden sonraki
`~01@EXT-AUD 0,1,1,n` geri bildirimi yine durumu günceller. Sorgu cevabı gelmezse yalnızca başlangıçta ses state'i
boş kalır; ilk ses butonuna basıldığında fiziksel geri bildirimle güncellenir.

## 1.3.0 ek özellikler

Mevcut projeksiyon ve matrix entity'leri değiştirilmeden aşağıdaki yeni entity'ler eklendi:

- Kramer ses seviyesi (0-100)
- Kramer ses aç / ses kıs butonları
- Kramer ses mute anahtarı
- Kramer Code Send metin kutusu

Code Send kutusuna Kramer Protocol 3000 komutu `#` ile başlayacak şekilde yazılır.
Örnek: `#VOLUME? 1`
