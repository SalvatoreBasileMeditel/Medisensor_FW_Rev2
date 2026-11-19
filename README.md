# Medisensor WM1 rev 2 — firmware OTA

Canali (DEC-015):
- `esp32/stable/` — unità in campo. **Solo build di produzione firmate.**
- `esp32/test/`   — schede di sviluppo e prove. Mai usato dalle unità in campo.

Pubblicazione (sempre con lo strumento, mai a mano):

    python tools/make_manifest.py test   ..\ESP32\build\wireless_manager.bin
    python tools/make_manifest.py stable <immagine di produzione firmata>
    git add -A && git commit -m "esp32 <canale> <versione>" && git push

Regole:
- La versione si alza in `PROJECT_VER` (CMakeLists.txt del firmware), mai qui.
- Il firmware rifiuta versioni non successive, progetti diversi, SHA-256 errati.
- `raw.githubusercontent.com` può servire il manifest vecchio per qualche minuto dopo il push.