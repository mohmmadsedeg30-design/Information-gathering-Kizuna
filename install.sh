#!/bin/bash
# KIZUNA X v5.0 — Smart Installer
echo "╔══════════════════════════════════╗"
echo "║   KIZUNA X v5.0 — Installer     ║"
echo "╚══════════════════════════════════╝"

# detect environment
if command -v pkg &>/dev/null; then
    echo "[*] Termux detected"
    pkg install python git -y 2>/dev/null
    PIP="pip"
    FLAGS="--break-system-packages"
elif command -v apk &>/dev/null; then
    echo "[*] Alpine detected"
    apk add python3 py3-pip git 2>/dev/null
    PIP="pip3"
    FLAGS="--break-system-packages"
else
    echo "[*] Linux/Mac"
    PIP="pip3"
    FLAGS=""
fi

echo "[*] Installing core libraries (light, fast)..."
$PIP install requests phonenumbers dnspython email-validator \
             python-whois python-dotenv rich pyfiglet \
             "qrcode[pil]" colorama Pillow $FLAGS -q

echo ""
echo "[✅] Core done! Run: python kizuna_x.py"
echo ""
echo "[i] Optional (heavy):"
echo "    Video tools:  pip install opencv-python-headless $FLAGS"
echo "    Speed test:   pip install speedtest-cli $FLAGS"
