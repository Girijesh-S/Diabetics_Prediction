"""Compile .po to .mo using Babel (no gettext needed on Windows). Run: python compile_translations.py"""
import os
from pathlib import Path

try:
    from babel.messages.mofile import write_mo
    from babel.messages.pofile import read_po
except ImportError:
    print("Install Babel: pip install Babel")
    raise

base = Path(__file__).parent
locale_dir = base / "locale"
for lang in ["hi", "ta"]:
    po_path = locale_dir / lang / "LC_MESSAGES" / "django.po"
    mo_path = locale_dir / lang / "LC_MESSAGES" / "django.mo"
    if po_path.exists():
        with open(po_path, "rb") as f:
            catalog = read_po(f, locale=lang)
        with open(mo_path, "wb") as f:
            write_mo(f, catalog)
        print(f"Compiled {po_path} -> {mo_path}")
    else:
        print(f"Skip {lang}: {po_path} not found")
print("Done.")
