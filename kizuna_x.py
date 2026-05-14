#!/usr/bin/python3
# ==========================================================
#   KIZUNA X — Advanced OSINT Framework v2.0
#   Modular · Parallel · Professional
# ==========================================================

import os
import sys
import json
import socket
import platform
import threading
import time
import logging
import hashlib
import ipaddress
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Third-party ────────────────────────────────────────────
try:
    import requests
    import phonenumbers
    import dns.resolver
    import whois
    from email_validator import validate_email, EmailNotValidError
    from phonenumbers import geocoder, carrier, timezone as ph_tz
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.text import Text
    from rich.columns import Columns
    from rich import box
except ImportError as e:
    print(f"[!] Missing dependency: {e}")
    print("[*] Run: pip install requests phonenumbers dnspython email-validator rich python-whois")
    sys.exit(1)

# ==========================================================
#   CONFIG & LOGGING
# ==========================================================

VERSION   = "2.0"
LOG_DIR   = "logs"
SAVE_DIR  = "results"

for d in (LOG_DIR, SAVE_DIR):
    os.makedirs(d, exist_ok=True)

logging.basicConfig(
    filename=f"{LOG_DIR}/kizuna.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console = Console()

def log(action: str, target: str, status: str = "OK"):
    logging.info(f"{action:<15} | target={target} | status={status}")

# ==========================================================
#   BANNER
# ==========================================================

BANNER = r"""
██╗  ██╗██╗███████╗██╗   ██╗███╗   ██╗ █████╗
██║ ██╔╝██║╚══███╔╝██║   ██║████╗  ██║██╔══██╗
█████╔╝ ██║  ███╔╝ ██║   ██║██╔██╗ ██║███████║
██╔═██╗ ██║ ███╔╝  ██║   ██║██║╚██╗██║██╔══██║
██║  ██╗██║███████╗╚██████╔╝██║ ╚████║██║  ██║
╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
        OSINT FRAMEWORK  ·  v{VERSION}
"""

# ==========================================================
#   HELPERS
# ==========================================================

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def pause():
    console.print("\n[dim][ ENTER to continue ][/dim]")
    input()

def section(title: str, color: str = "cyan"):
    clear()
    console.print(Panel.fit(f"[bold]{title}[/bold]", style=color, padding=(0, 4)))
    console.print()

def save_result(name: str, data: dict):
    """Save module result as JSON."""
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SAVE_DIR}/{name}_{ts}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    console.print(f"[dim]💾 Saved → {path}[/dim]")

def make_table(title: str, rows: list[tuple], headers=("FIELD", "VALUE"),
               style: str = "cyan") -> Table:
    t = Table(title=title, box=box.SIMPLE_HEAVY, border_style=style,
              header_style=f"bold {style}", show_lines=False)
    for h in headers:
        t.add_column(h, overflow="fold")
    for row in rows:
        t.add_row(*[str(c) for c in row])
    return t

# ==========================================================
#   MODULE 1 — PHONE LOOKUP
# ==========================================================

def phone_lookup():
    section("📱  PHONE ANALYZER", "cyan")
    number = Prompt.ask("[cyan]Phone number[/cyan] (e.g. +966501234567)")

    try:
        parsed  = phonenumbers.parse(number)
        valid   = phonenumbers.is_valid_number(parsed)
        possible= phonenumbers.is_possible_number(parsed)
        country = geocoder.description_for_number(parsed, "en")
        sim     = carrier.name_for_number(parsed, "en")
        tz_list = ph_tz.time_zones_for_number(parsed)
        fmt_intl= phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        fmt_e164= phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        ntype   = phonenumbers.number_type(parsed)
        type_map= {
            0:"FIXED_LINE", 1:"MOBILE", 2:"FIXED_OR_MOBILE",
            3:"TOLL_FREE", 4:"PREMIUM_RATE", 6:"VOIP", 7:"PERSONAL",
            10:"UAN", 27:"EMERGENCY", 28:"VOICEMAIL",
        }
        num_type = type_map.get(ntype, "UNKNOWN")

        rows = [
            ("E.164 Format",    fmt_e164),
            ("International",   fmt_intl),
            ("Valid",           "✅ YES" if valid   else "❌ NO"),
            ("Possible",        "✅ YES" if possible else "❌ NO"),
            ("Country",         country or "—"),
            ("Carrier",         sim     or "—"),
            ("Number Type",     num_type),
            ("Timezones",       ", ".join(tz_list) if tz_list else "—"),
            ("Country Code",    str(parsed.country_code)),
            ("National Number", str(parsed.national_number)),
        ]

        console.print(make_table("PHONE RESULTS", rows))

        result = dict(rows)
        if Prompt.ask("\n[dim]Save result?[/dim]", choices=["y","n"], default="n") == "y":
            save_result("phone", result)

        log("PHONE_LOOKUP", number)

    except phonenumbers.NumberParseException as e:
        console.print(f"[red]Parse error:[/red] {e}")
        log("PHONE_LOOKUP", number, "ERROR")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        log("PHONE_LOOKUP", number, "ERROR")

    pause()

# ==========================================================
#   MODULE 2 — EMAIL LOOKUP
# ==========================================================

def email_lookup():
    section("📧  EMAIL ANALYZER", "green")
    email = Prompt.ask("[green]Email address[/green]")

    try:
        valid  = validate_email(email, check_deliverability=True)
        domain = valid.domain
        rows   = [("Normalized", valid.normalized), ("Domain", domain)]

        # MX records
        try:
            mx_records = sorted(
                dns.resolver.resolve(domain, "MX"),
                key=lambda r: r.preference
            )
            for r in mx_records:
                rows.append((f"MX (pref {r.preference})", str(r.exchange).rstrip(".")))
        except Exception:
            rows.append(("MX Records", "None / Unresolvable"))

        # SPF
        try:
            txt = dns.resolver.resolve(domain, "TXT")
            spf = next((str(r) for r in txt if "v=spf" in str(r).lower()), None)
            rows.append(("SPF Record", spf or "Not found"))
        except Exception:
            rows.append(("SPF Record", "Query failed"))

        # DMARC
        try:
            dmarc = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
            rows.append(("DMARC", str(list(dmarc)[0]).strip('"')))
        except Exception:
            rows.append(("DMARC", "Not found"))

        console.print(make_table("EMAIL RESULTS", rows, style="green"))

        if Prompt.ask("\n[dim]Save result?[/dim]", choices=["y","n"], default="n") == "y":
            save_result("email", dict(rows))

        log("EMAIL_LOOKUP", email)

    except EmailNotValidError as e:
        console.print(f"[red]Invalid email:[/red] {e}")
        log("EMAIL_LOOKUP", email, "INVALID")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        log("EMAIL_LOOKUP", email, "ERROR")

    pause()

# ==========================================================
#   MODULE 3 — DOMAIN LOOKUP
# ==========================================================

def domain_lookup():
    section("🌐  DOMAIN ANALYZER", "yellow")
    target = Prompt.ask("[yellow]Domain[/yellow] (e.g. example.com)")

    rows = []

    # WHOIS
    try:
        info = whois.whois(target)
        important = [
            "domain_name","registrar","creation_date","expiration_date",
            "updated_date","name_servers","status","org","country","emails"
        ]
        for k in important:
            v = info.get(k)
            if v:
                rows.append((k.replace("_"," ").title(), v))
    except Exception as e:
        rows.append(("WHOIS", f"Failed: {e}"))

    # DNS records
    for rtype in ("A","AAAA","CNAME","NS","TXT","MX","SOA"):
        try:
            answers = dns.resolver.resolve(target, rtype, lifetime=3)
            for ans in answers:
                rows.append((f"DNS {rtype}", str(ans).rstrip(".")))
        except Exception:
            pass

    if rows:
        console.print(make_table("DOMAIN RESULTS", rows, style="yellow"))
    else:
        console.print("[red]No data found.[/red]")

    if Prompt.ask("\n[dim]Save result?[/dim]", choices=["y","n"], default="n") == "y":
        save_result("domain", dict(rows))

    log("DOMAIN_LOOKUP", target)
    pause()

# ==========================================================
#   MODULE 4 — IP LOOKUP
# ==========================================================

def ip_lookup():
    section("🔍  IP ANALYZER", "magenta")
    ip = Prompt.ask("[magenta]IP address[/magenta]")

    # Validate
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        # Maybe hostname — resolve it
        try:
            ip = socket.gethostbyname(ip)
            console.print(f"[dim]Resolved to: {ip}[/dim]")
        except Exception:
            console.print("[red]Invalid IP or unresolvable hostname.[/red]")
            pause()
            return

    try:
        data = requests.get(
            f"https://ip-api.com/json/{ip}?fields=66846719",
            timeout=8
        ).json()

        if data.get("status") == "fail":
            console.print(f"[red]Lookup failed:[/red] {data.get('message')}")
        else:
            order = [
                "query","status","country","countryCode","region","regionName",
                "city","zip","lat","lon","timezone","isp","org","as","asname",
                "reverse","mobile","proxy","hosting"
            ]
            rows = [(k, data[k]) for k in order if k in data]
            console.print(make_table("IP RESULTS", rows, style="magenta"))

            if Prompt.ask("\n[dim]Save result?[/dim]", choices=["y","n"], default="n") == "y":
                save_result("ip", data)

        log("IP_LOOKUP", ip)

    except requests.RequestException as e:
        console.print(f"[red]Network error:[/red] {e}")
        log("IP_LOOKUP", ip, "ERROR")

    pause()

# ==========================================================
#   MODULE 5 — PORT SCANNER  (own systems / authorized only)
# ==========================================================

def port_scanner():
    section("🔌  PORT SCANNER", "red")
    console.print("[dim yellow]⚠  For use on systems you own or have written permission to test.[/dim yellow]\n")

    target = Prompt.ask("[red]Target IP / hostname[/red]")
    try:
        rng = Prompt.ask("Port range [default 1-1024]", default="1-1024")
        p1, p2 = map(int, rng.split("-"))
        p1, p2 = max(1, p1), min(65535, p2)
    except ValueError:
        console.print("[red]Invalid range.[/red]")
        pause()
        return

    workers = int(Prompt.ask("Threads [default 200]", default="200"))
    timeout = float(Prompt.ask("Timeout seconds [default 0.4]", default="0.4"))

    console.print(f"\n[yellow]Scanning {target} ports {p1}–{p2} with {workers} threads…[/yellow]")
    start = time.time()

    open_ports: dict[int, str] = {}
    lock = threading.Lock()

    COMMON_SERVICES = {
        21:"FTP", 22:"SSH", 23:"TELNET", 25:"SMTP", 53:"DNS",
        80:"HTTP", 110:"POP3", 143:"IMAP", 443:"HTTPS", 445:"SMB",
        3306:"MySQL", 3389:"RDP", 5432:"PostgreSQL", 6379:"Redis",
        8080:"HTTP-Alt", 8443:"HTTPS-Alt", 27017:"MongoDB",
    }

    def probe(port: int):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                if s.connect_ex((target, port)) == 0:
                    svc = COMMON_SERVICES.get(port, "")
                    try:
                        svc = socket.getservbyport(port) or svc
                    except Exception:
                        pass
                    with lock:
                        open_ports[port] = svc
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=workers) as ex:
        ex.map(probe, range(p1, p2 + 1))

    elapsed = time.time() - start

    if open_ports:
        rows = [(str(p), open_ports[p] or "—") for p in sorted(open_ports)]
        console.print(make_table(
            f"OPEN PORTS on {target}  ({len(rows)} found, {elapsed:.1f}s)",
            rows, headers=("PORT","SERVICE"), style="red"
        ))
    else:
        console.print(f"[dim]No open ports found in {p1}–{p2}. ({elapsed:.1f}s)[/dim]")

    log("PORT_SCAN", target)
    pause()

# ==========================================================
#   MODULE 6 — HASH TOOLS
# ==========================================================

ALGOS = {
    "md5":    hashlib.md5,
    "sha1":   hashlib.sha1,
    "sha224": hashlib.sha224,
    "sha256": hashlib.sha256,
    "sha384": hashlib.sha384,
    "sha512": hashlib.sha512,
}

def hash_tools():
    section("🔑  HASH TOOLS", "blue")
    console.print("[1] Generate hash from text")
    console.print("[2] Generate hash from file")
    console.print("[3] Compare two hashes")
    choice = Prompt.ask("\nSelect", choices=["1","2","3"])

    if choice == "1":
        text = Prompt.ask("Enter text")
        rows = [(algo.upper(), fn(text.encode()).hexdigest()) for algo, fn in ALGOS.items()]
        console.print(make_table("HASH RESULTS", rows, headers=("ALGORITHM","HASH"), style="blue"))

    elif choice == "2":
        path = Prompt.ask("File path").strip()
        if not os.path.isfile(path):
            console.print("[red]File not found.[/red]")
            pause()
            return
        hashes = {a: fn() for a, fn in ALGOS.items()}
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                for h in hashes.values():
                    h.update(chunk)
        rows = [(a.upper(), h.hexdigest()) for a, h in hashes.items()]
        console.print(make_table(f"FILE HASHES: {os.path.basename(path)}", rows,
                                  headers=("ALGORITHM","HASH"), style="blue"))

    elif choice == "3":
        h1 = Prompt.ask("Hash 1").strip().lower()
        h2 = Prompt.ask("Hash 2").strip().lower()
        match = h1 == h2
        console.print(f"\n{'[green]✅ MATCH[/green]' if match else '[red]❌ MISMATCH[/red]'}")

    pause()

# ==========================================================
#   MODULE 7 — SYSTEM INFO
# ==========================================================

def system_info():
    section("💻  SYSTEM INFO", "white")
    rows = [
        ("OS",          platform.system()),
        ("Release",     platform.release()),
        ("Version",     platform.version()),
        ("Architecture",platform.machine()),
        ("Processor",   platform.processor() or "—"),
        ("Hostname",    platform.node()),
        ("Python",      sys.version.split()[0]),
    ]

    # Network interfaces
    try:
        hostname = socket.gethostname()
        rows.append(("Local IP", socket.gethostbyname(hostname)))
    except Exception:
        pass

    # Public IP
    try:
        pub_ip = requests.get("https://api.ipify.org", timeout=4).text.strip()
        rows.append(("Public IP", pub_ip))
    except Exception:
        rows.append(("Public IP", "Unavailable"))

    console.print(make_table("SYSTEM INFORMATION", rows))
    pause()

# ==========================================================
#   MODULE 8 — DNS DEEP SCAN
# ==========================================================

def dns_deep_scan():
    section("📡  DNS DEEP SCAN", "bright_cyan")
    target = Prompt.ask("[bright_cyan]Domain[/bright_cyan]")

    RTYPES = ["A","AAAA","CNAME","MX","NS","TXT","SOA","PTR","SRV","CAA","DNSKEY"]
    rows   = []

    for rtype in RTYPES:
        try:
            answers = dns.resolver.resolve(target, rtype, lifetime=4)
            for ans in answers:
                rows.append((rtype, str(ans).rstrip(".")))
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except Exception as e:
            rows.append((rtype, f"Error: {e}"))

    if rows:
        console.print(make_table(f"DNS RECORDS: {target}", rows,
                                  headers=("TYPE","VALUE"), style="bright_cyan"))
    else:
        console.print("[red]No DNS records found.[/red]")

    log("DNS_SCAN", target)
    pause()

# ==========================================================
#   MAIN MENU
# ==========================================================

MENU_ITEMS = [
    ("1", "📱  Phone Lookup",   "cyan"),
    ("2", "📧  Email Lookup",   "green"),
    ("3", "🌐  Domain Lookup",  "yellow"),
    ("4", "🔍  IP Lookup",      "magenta"),
    ("5", "🔌  Port Scanner",   "red"),
    ("6", "🔑  Hash Tools",     "blue"),
    ("7", "💻  System Info",    "white"),
    ("8", "📡  DNS Deep Scan",  "bright_cyan"),
    ("0", "🚪  Exit",           "dim"),
]

ACTIONS = {
    "1": phone_lookup,
    "2": email_lookup,
    "3": domain_lookup,
    "4": ip_lookup,
    "5": port_scanner,
    "6": hash_tools,
    "7": system_info,
    "8": dns_deep_scan,
}

def menu():
    while True:
        clear()
        console.print(f"[bold cyan]{BANNER.format(VERSION=VERSION)}[/bold cyan]")
        console.print(f"  [dim]{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}[/dim]\n")

        for key, label, color in MENU_ITEMS:
            console.print(f"  [{color}][{key}][/{color}]  {label}")

        choice = Prompt.ask("\n[bold]Select module[/bold]")

        if choice == "0":
            console.print("\n[red]Goodbye.[/red]\n")
            sys.exit(0)

        action = ACTIONS.get(choice)
        if action:
            action()
        else:
            console.print("[red]Invalid choice.[/red]")
            time.sleep(0.8)

# ==========================================================
#   ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        console.print("\n\n[red]Interrupted.[/red]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]FATAL:[/bold red] {e}")
        logging.critical(f"FATAL: {e}", exc_info=True)
        sys.exit(1)
