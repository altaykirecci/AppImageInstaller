# AppImage Installer

AppImage dosyalarını kolayca kurmanızı ve yönetmenizi sağlayan bir Python aracı.

## Özellikler

- AppImage dosyalarını kurma
- Kurulu AppImage'ları kaldırma
- Sandbox modu desteği
- Versiyon yönetimi
- Kurulu uygulamaları listeleme

## Kurulum

```bash
pip install .
```

## Kullanım

```bash
# Uygulama kurma
appimage-installer -i /path/to/app.AppImage

# Sandbox modu ile kurma
appimage-installer -i /path/to/app.AppImage --sandbox

# Kurulu uygulamaları listeleme
appimage-installer -l

# Uygulama kaldırma
appimage-installer -u app_name
```

## Versiyon Geçmişi

Detaylı versiyon geçmişi için [CHANGELOG.md](CHANGELOG.md) dosyasına bakın.

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## Author

Developed by [altaykirecci](https://github.com/altaykirecci)
`opriori (c)(p)2025 (https://www.opriori.com.tr)