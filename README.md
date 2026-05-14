# KIZUNA X — OSINT Framework

```
██╗  ██╗██╗███████╗██╗   ██╗███╗   ██╗ █████╗
██║ ██╔╝██║╚══███╔╝██║   ██║████╗  ██║██╔══██╗
█████╔╝ ██║  ███╔╝ ██║   ██║██╔██╗ ██║███████║
██╔═██╗ ██║ ███╔╝  ██║   ██║██║╚██╗██║██╔══██║
██║  ██╗██║███████╗╚██████╔╝██║ ╚████║██║  ██║
╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
        OSINT FRAMEWORK  ·  v2.0
```

> أداة استطلاع وجمع معلومات مفتوحة المصدر مبنية بـ Python

---

## الوحدات

| # | الوحدة | الوصف |
|---|--------|-------|
| 1 | 📱 Phone OSINT | تحليل أرقام الهاتف — الدولة، الشبكة، النوع، التوقيت |
| 2 | 📧 Email OSINT | التحقق من الإيميل + سجلات MX / SPF / DMARC |
| 3 | 🌐 Domain OSINT | WHOIS + سجلات DNS كاملة |
| 4 | 🔍 IP OSINT | الموقع الجغرافي، ISP، ASN، Proxy Detection |
| 5 | 🔌 Port Scanner | فحص المنافذ المفتوحة (على أنظمتك فقط) |
| 6 | 🔑 Hash Tools | توليد ومقارنة الهاش (MD5, SHA1, SHA256…) |
| 7 | 💻 System Info | معلومات الجهاز والـ IP المحلي والعام |
| 8 | 📡 DNS Deep Scan | استعلام شامل لجميع أنواع سجلات DNS |

---

## التثبيت

### Linux / Mac
```bash
git clone https://github.com/mohmmadsedeg30-design/Information-gathering-Kizuna.git
cd Information-gathering-Kizuna
pip install -r requirements.txt
python3 kizuna_x.py
```

### Termux (Android)
```bash
pkg update && pkg install python git
git clone https://github.com/mohmmadsedeg30-design/Information-gathering-Kizuna.git
cd Information-gathering-Kizuna
pip install -r requirements.txt
python kizuna_x.py
```

### Windows
```bash
git clone https://github.com/mohmmadsedeg30-design/Information-gathering-Kizuna.git
cd Information-gathering-Kizuna
pip install -r requirements.txt
python kizuna_x.py
```

---

## المتطلبات

```
requests
phonenumbers
dnspython
email-validator
rich
python-whois
```

التثبيت اليدوي:
```bash
pip install requests phonenumbers dnspython email-validator rich python-whois
```

---

## النتائج

يتم حفظ النتائج تلقائياً في مجلد `results/` بصيغة JSON عند الاختيار.
السجلات في `logs/kizuna.log`.

---

## تحذير قانوني

```
هذه الأداة مخصصة للاستخدام التعليمي وعلى أنظمتك الخاصة فقط.
المطور غير مسؤول عن أي استخدام غير مشروع.
```

---

## المتطلبات

- Python 3.8+
- اتصال بالإنترنت للوحدات التي تعتمد على APIs خارجية
