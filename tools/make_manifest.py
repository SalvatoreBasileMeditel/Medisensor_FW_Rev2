#!/usr/bin/env python3
"""Pubblicazione OTA ESP32 — Medisensor WM1 rev 2 (DEC-015).

Uso:
  python tools/make_manifest.py test   <percorso>/wireless_manager.bin
  python tools/make_manifest.py stable <percorso>/wireless_manager.bin   (solo immagini firmate)

Legge progetto e versione dall'header dell'immagine, copia il .bin in esp32/<canale>/
e scrive esp32/<canale>/manifest.json. Poi: git add, commit, push.
"""
import argparse
import hashlib
import json
import re
import shutil
import struct
import sys
from pathlib import Path

OWNER    = "SalvatoreBasileMeditel"
REPO     = "Medisensor_FW_Rev2"
BRANCH   = "main"
PROJECT  = "wireless_manager"          # nome progetto atteso nell'header (DEC-015)

APP_DESC_OFFSET = 0x20                 # header immagine (24 B) + header 1o segmento (8 B)
APP_DESC_MAGIC  = 0xABCD5432
SIG_BLOCK_SIZE  = 4096                 # settore firma Secure Boot v2
SIG_BLOCK_MAGIC = 0xE7

ROOT = Path(__file__).resolve().parent.parent


def die(msg: str) -> None:
    sys.exit(f"ERRORE: {msg}")


def read_app_desc(data: bytes):
    magic, secure_version = struct.unpack_from("<II", data, APP_DESC_OFFSET)
    if magic != APP_DESC_MAGIC:
        die("header applicazione non trovato: non e' un'immagine applicativa ESP-IDF")
    version = data[APP_DESC_OFFSET + 16:APP_DESC_OFFSET + 48].split(b"\0")[0].decode()
    project = data[APP_DESC_OFFSET + 48:APP_DESC_OFFSET + 80].split(b"\0")[0].decode()
    return project, version, secure_version


def version_int(version: str) -> int:
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{1,2})", version)
    if not m:
        die(f"versione '{version}' non SemVer MAJOR.MINOR.PATCH (0-99)")
    major, minor, patch = (int(x) for x in m.groups())
    return major * 10000 + minor * 100 + patch


def is_signed(data: bytes) -> bool:
    return len(data) > SIG_BLOCK_SIZE and data[-SIG_BLOCK_SIZE] == SIG_BLOCK_MAGIC


def main() -> None:
    ap = argparse.ArgumentParser(description="Pubblica un'immagine OTA ESP32 rev 2")
    ap.add_argument("channel", choices=["stable", "test"])
    ap.add_argument("image", type=Path)
    args = ap.parse_args()

    data = args.image.read_bytes()
    project, version, secure_version = read_app_desc(data)
    vint = version_int(version)

    if project != PROJECT:
        die(f"progetto '{project}' diverso da '{PROJECT}'")
    if args.channel == "stable" and not is_signed(data):
        die("il canale stable accetta solo immagini FIRMATE (build di produzione + firma)")

    out_dir = ROOT / "esp32" / args.channel
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{PROJECT}-{version}.bin"
    shutil.copyfile(args.image, out_dir / name)

    manifest = {
        "esp32": {
            "version": version,
            "version_int": vint,
            "url": f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/esp32/{args.channel}/{name}",
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "secure_version": secure_version,
            "signed": is_signed(data),
        }
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {name} -> esp32/{args.channel}/ (versione {version}, "
          f"secure_version {secure_version}, firmata: {manifest['esp32']['signed']})")


if __name__ == "__main__":
    main()