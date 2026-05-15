#!/usr/bin/env python3

##   KIZUNA X   :   Advanced OSINT Intelligence Framework
##   Version    :   3.0
##   Modules    :   Phone · Email · Domain · IP · DNS · Hash

import os
import sys
import json
import socket
import hashlib
import logging
import ipaddress
from datetime import datetime
from typing import Optional

import requests
import phonenumbers
import dns.resolver
import whois
from phonenumbers import carrier, geocoder, timezone as ph_tz
from email_validator import validate_email, EmailNotValidError
from dotenv import load_dotenv
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich import box

load_dotenv()

os.makedirs("logs",    exist_ok=True)
os.makedirs("results", exist_ok=True)

logging.basicConfig(
    filename="logs/kizuna.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console = Console()

BANNER = r"""
██╗  ██╗██╗███████╗██╗   ██╗███╗   ██╗ █████╗
██║ ██╔╝██║╚══███╔╝██║   ██║████╗  ██║██╔══██╗
█████╔╝ ██║  ███╔╝ ██║   ██║██╔██╗ ██║███████║
██╔═██╗ ██║ ███╔╝  ██║   ██║██║╚██╗██║██╔══██║
██║  ██╗██║███████╗╚██████╔╝██║ ╚████║██║  ██║
╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
          Advanced OSINT Framework v3.0
"""

# ════════════════════════════════════════════════════════════
#   HELPERS
# ════════════════════════════════════════════════════════════

def log(action: str, target: str, status: str = "OK"):
    logging.info(f"{action:<20} | target={target} | status={status}")

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def pause():
    console.print("\n[dim][ ENTER to continue ][/dim]")
    input()

def http_get(url: str, params=None, timeout=10) -> Optional[requests.Response]:
    ua = os.getenv("USER_AGENT", "Mozilla/5.0 KizunaX/3.0")
    try:
        return requests.get(url, params=params,
                            headers={"User-Agent": ua},
                            timeout=timeout)
    except Exception:
        return None

def make_table(title: str, rows: list, headers=("FIELD", "VALUE"),
               style: str = "cyan") -> Table:
    t = Table(title=title, box=box.ROUNDED, border_style=style,
              header_style=f"bold {style}", show_lines=True,
              title_style=f"bold {style}")
    for h in headers:
        t.add_column(h, overflow="fold")
    for row in rows:
        t.add_row(*[str(c) for c in row])
    return t

def save_result(name: str, data: dict):
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"results/{name}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str, ensure_ascii=False)
    console.print(f"[dim]💾 Saved → {path}[/dim]")
    return path

def ask_save(data: dict, name: str):
    if Prompt.ask("\n[dim]Save result?[/dim]", choices=["y","n"], default="n") == "y":
        path = save_result(name, data)
        with open(path) as f:
            content = f.read()
        console.print(Panel(
            Syntax(content, "json", theme="monokai", line_numbers=False),
            title="JSON Preview", border_style="dim"
        ))

# ════════════════════════════════════════════════════════════
#   MODULE 1 — PHONE
# ════════════════════════════════════════════════════════════

class PhoneOSINT:
    def __init__(self, number: str):
        self.number  = number
        self.results = {}

    def run(self):
        try:
            parsed   = phonenumbers.parse(self.number)
            valid    = phonenumbers.is_valid_number(parsed)
            possible = phonenumbers.is_possible_number(parsed)
            region   = phonenumbers.region_code_for_number(parsed) or "—"
            country  = geocoder.description_for_number(parsed, "en")
            sim      = carrier.name_for_number(parsed, "en")
            tz_list  = ph_tz.time_zones_for_number(parsed)
            fmt_e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            fmt_intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            fmt_natl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            TYPE_MAP = {
                0:"FIXED_LINE", 1:"MOBILE", 2:"FIXED_OR_MOBILE",
                3:"TOLL_FREE",  4:"PREMIUM_RATE", 6:"VOIP",
                7:"PERSONAL",  10:"UAN", 28:"VOICEMAIL",
            }
            num_type = TYPE_MAP.get(phonenumbers.number_type(parsed), "UNKNOWN")
            self.results["basic"] = {
                "E164":          fmt_e164,
                "International": fmt_intl,
                "National":      fmt_natl,
                "Valid":         "✅ YES" if valid    else "❌ NO",
                "Possible":      "✅ YES" if possible else "❌ NO",
                "Region":        region,
                "Country":       country  or "—",
                "Carrier":       sim      or "—",
                "Type":          num_type,
                "Dial Code":     f"+{parsed.country_code}",
                "Timezones":     ", ".join(tz_list) if tz_list else "—",
            }
            key = os.getenv("NUMVERIFY_API_KEY")
            if key:
                r = http_get("http://apilayer.net/api/validate",
                             params={"access_key": key, "number": fmt_e164})
                if r and r.status_code == 200:
                    d = r.json()
                    self.results["numverify"] = {
                        k: d[k] for k in
                        ("valid","local_format","international_format",
                         "carrier","line_type","location","country_name")
                        if k in d
                    }
        except phonenumbers.NumberParseException as e:
            console.print(f"[red]Parse error:[/red] {e}")

    def display(self):
        tables = [make_table(s.upper(), list(d.items()), style="cyan")
                  for s, d in self.results.items()]
        if tables:
            console.print(Panel(Group(*tables),
                                title=f"📱 PHONE: {self.number}",
                                border_style="cyan"))


def phone_lookup():
    clear()
    console.print(Panel.fit("[bold cyan]📱  PHONE OSINT[/bold cyan]", padding=(0,4)))
    number = Prompt.ask("[cyan]Phone number[/cyan] (e.g. +966501234567)")
    m = PhoneOSINT(number)
    with console.status("[cyan]Gathering phone intelligence…[/cyan]"):
        m.run()
    m.display()
    log("PHONE_LOOKUP", number)
    ask_save(m.results, "phone")
    pause()

# ════════════════════════════════════════════════════════════
#   MODULE 2 — EMAIL
# ════════════════════════════════════════════════════════════

class EmailOSINT:
    def __init__(self, email: str):
        self.email   = email
        self.results = {}

    def run(self):
        try:
            valid  = validate_email(self.email, check_deliverability=True)
            domain = valid.domain
            self.results["basic"] = {"Normalized": valid.normalized, "Domain": domain}
            mx_rows = {}
            try:
                for r in sorted(dns.resolver.resolve(domain, "MX"), key=lambda x: x.preference):
                    mx_rows[f"MX (p{r.preference})"] = str(r.exchange).rstrip(".")
            except Exception:
                mx_rows["MX"] = "None"
            self.results["mx"] = mx_rows
            security = {}
            for label, qname in [("SPF",""),("DMARC","_dmarc."),("BIMI","default._bimi.")]:
                try:
                    recs = dns.resolver.resolve(f"{qname}{domain}", "TXT", lifetime=4)
                    for rec in recs:
                        security[label] = str(rec).strip('"')
                except Exception:
                    security[label] = "Not found"
            self.results["security"] = security
            try:
                r = http_get(
                    "https://disposable.github.io/disposable-email-domains/domains.json",
                    timeout=5)
                if r and r.status_code == 200:
                    disposable = domain in set(r.json())
                    self.results["reputation"] = {
                        "Disposable": "⚠️ YES" if disposable else "✅ NO"
                    }
            except Exception:
                pass
        except EmailNotValidError as e:
            console.print(f"[red]Invalid email:[/red] {e}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def display(self):
        tables = [make_table(s.upper(), list(d.items()), style="green")
                  for s, d in self.results.items()]
        if tables:
            console.print(Panel(Group(*tables),
                                title=f"📧 EMAIL: {self.email}",
                                border_style="green"))


def email_lookup():
    clear()
    console.print(Panel.fit("[bold green]📧  EMAIL OSINT[/bold green]", padding=(0,4)))
    email = Prompt.ask("[green]Email address[/green]")
    m = EmailOSINT(email)
    with console.status("[green]Gathering email intelligence…[/green]"):
        m.run()
    m.display()
    log("EMAIL_LOOKUP", email)
    ask_save(m.results, "email")
    pause()

# ════════════════════════════════════════════════════════════
#   MODULE 3 — DOMAIN
# ════════════════════════════════════════════════════════════

class DomainOSINT:
    def __init__(self, domain: str):
        self.domain  = domain
        self.results = {}

    def run(self):
        try:
            info = whois.whois(self.domain)
            keys = ["domain_name","registrar","creation_date","expiration_date",
                    "updated_date","name_servers","status","org","country","emails"]
            self.results["whois"] = {
                k.replace("_"," ").title(): info[k]
                for k in keys if info.get(k)
            }
        except Exception as e:
            self.results["whois"] = {"Error": str(e)}
        dns_data = {}
        for rtype in ["A","AAAA","MX","NS","TXT","SOA","CAA"]:
            try:
                answers = dns.resolver.resolve(self.domain, rtype, lifetime=4)
                dns_data[rtype] = [str(a).rstrip(".") for a in answers]
            except Exception:
                pass
        self.results["dns"] = {k: ", ".join(v) for k, v in dns_data.items()}
        try:
            r = http_get(f"https://crt.sh/?q=%.{self.domain}&output=json", timeout=12)
            if r and r.status_code == 200:
                subs = set()
                for entry in r.json():
                    for name in entry.get("name_value","").split("\n"):
                        name = name.strip().lower()
                        if name.endswith(self.domain) and "*" not in name:
                            subs.add(name)
                self.results["subdomains"] = {
                    f"Sub {i+1}": s for i, s in enumerate(sorted(subs))
                }
        except Exception:
            pass

    def display(self):
        tables = [make_table(s.upper(), list(d.items()), style="yellow")
                  for s, d in self.results.items()]
        if tables:
            console.print(Panel(Group(*tables),
                                title=f"🌐 DOMAIN: {self.domain}",
                                border_style="yellow"))


def domain_lookup():
    clear()
    console.print(Panel.fit("[bold yellow]🌐  DOMAIN OSINT[/bold yellow]", padding=(0,4)))
    target = Prompt.ask("[yellow]Domain[/yellow] (e.g. example.com)")
    m = DomainOSINT(target)
    with console.status("[yellow]Gathering domain intelligence…[/yellow]"):
        m.run()
    m.display()
    log("DOMAIN_LOOKUP", target)
    ask_save(m.results, "domain")
    pause()

# ════════════════════════════════════════════════════════════
#   MODULE 4 — IP
# ════════════════════════════════════════════════════════════

class IPOSINT:
    def __init__(self, ip: str):
        self.ip      = ip
        self.results = {}

    def run(self):
        try:
            ipaddress.ip_address(self.ip)
        except ValueError:
            try:
                self.ip = socket.gethostbyname(self.ip)
                console.print(f"[dim]Resolved → {self.ip}[/dim]")
            except Exception:
                console.print("[red]Cannot resolve.[/red]")
                return
        try:
            r = http_get(f"http://ip-api.com/json/{self.ip}?fields=66846719")
            if r and r.status_code == 200:
                d = r.json()
                self.results["geolocation"] = {
                    k.title().replace("_"," "): d[k]
                    for k in ["country","regionName","city","zip","lat","lon",
                               "timezone","isp","org","as","reverse","mobile",
                               "proxy","hosting"]
                    if k in d
                }
        except Exception:
            pass
        try:
            rev = ".".join(reversed(self.ip.split("."))) + ".in-addr.arpa"
            ptr = dns.resolver.resolve(rev, "PTR", lifetime=4)
            self.results["ptr"] = {"PTR": str(list(ptr)[0]).rstrip(".")}
        except Exception:
            pass
        geo = self.results.get("geolocation", {})
        lat = geo.get("Lat"); lon = geo.get("Lon")
        if lat and lon:
            self.results["maps"] = {
                "Coordinates": f"{lat}, {lon}",
                "Google Maps": f"https://maps.google.com/?q={lat},{lon}"
            }

    def display(self):
        tables = [make_table(s.upper(), list(d.items()), style="magenta")
                  for s, d in self.results.items()]
        if tables:
            console.print(Panel(Group(*tables),
                                title=f"🔍 IP: {self.ip}",
                                border_style="magenta"))


def ip_lookup():
    clear()
    console.print(Panel.fit("[bold magenta]🔍  IP OSINT[/bold magenta]", padding=(0,4)))
    raw = Prompt.ask("[magenta]IP / hostname[/magenta]")
    m = IPOSINT(raw)
    with console.status("[magenta]Gathering IP intelligence…[/magenta]"):
        m.run()
    m.display()
    log("IP_LOOKUP", raw)
    ask_save(m.results, "ip")
    pause()

# ════════════════════════════════════════════════════════════
#   MODULE 5 — DNS DEEP SCAN
# ════════════════════════════════════════════════════════════

class DNSScan:
    def __init__(self, domain: str):
        self.domain  = domain
        self.results = {}

    def run(self):
        for rtype in ["A","AAAA","CNAME","MX","NS","TXT","SOA","CAA","DNSKEY","SRV"]:
            try:
                answers = dns.resolver.resolve(self.domain, rtype, lifetime=5)
                self.results[rtype] = [str(a).rstrip(".") for a in answers]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                pass
            except Exception as e:
                self.results[rtype] = [f"Error: {e}"]
        try:
            ns_recs = dns.resolver.resolve(self.domain, "NS", lifetime=4)
            for ns in ns_recs:
                ns_str = str(ns).rstrip(".")
                try:
                    z = dns.zone.from_xfr(dns.query.xfr(ns_str, self.domain, lifetime=5))
                    self.results["AXFR"] = [f"⚠️ VULNERABLE via {ns_str} — {len(z.nodes)} records"]
                    break
                except Exception:
                    self.results["AXFR"] = ["✅ Refused"]
        except Exception:
            pass

    def display(self):
        rows = [(rtype, v) for rtype, values in self.results.items() for v in values]
        if rows:
            console.print(Panel(
                make_table("DNS RECORDS", rows, headers=("TYPE","VALUE"), style="bright_cyan"),
                title=f"📡 DNS: {self.domain}", border_style="bright_cyan"
            ))


def dns_scan():
    clear()
    console.print(Panel.fit("[bold bright_cyan]📡  DNS DEEP SCAN[/bold bright_cyan]", padding=(0,4)))
    target = Prompt.ask("[bright_cyan]Domain[/bright_cyan]")
    m = DNSScan(target)
    with console.status("[bright_cyan]Scanning DNS records…[/bright_cyan]"):
        m.run()
    m.display()
    log("DNS_SCAN", target)
    ask_save(m.results, "dns")
    pause()

# ════════════════════════════════════════════════════════════
#   MODULE 6 — HASH TOOLS
# ════════════════════════════════════════════════════════════

ALGOS = {
    "MD5":      hashlib.md5,
    "SHA1":     hashlib.sha1,
    "SHA224":   hashlib.sha224,
    "SHA256":   hashlib.sha256,
    "SHA384":   hashlib.sha384,
    "SHA512":   hashlib.sha512,
    "SHA3-256": hashlib.sha3_256,
    "BLAKE2b":  hashlib.blake2b,
}

def hash_tools():
    clear()
    console.print(Panel.fit("[bold blue]🔑  HASH TOOLS[/bold blue]", padding=(0,4)))
    console.print("[1] Hash text\n[2] Hash file\n[3] Compare hashes\n[4] Identify hash type")
    choice = Prompt.ask("Select", choices=["1","2","3","4"])
    if choice == "1":
        text = Prompt.ask("Text")
        rows = [(algo, fn(text.encode()).hexdigest()) for algo, fn in ALGOS.items()]
        console.print(Panel(
            make_table("HASH RESULTS", rows, headers=("ALGORITHM","HASH"), style="blue"),
            border_style="blue"))
    elif choice == "2":
        path = Prompt.ask("File path").strip()
        if not os.path.isfile(path):
            console.print("[red]File not found.[/red]"); pause(); return
        hashes = {a: fn() for a, fn in ALGOS.items()}
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                for h in hashes.values(): h.update(chunk)
        rows = [(a, h.hexdigest()) for a, h in hashes.items()]
        console.print(Panel(
            make_table(f"FILE: {os.path.basename(path)}", rows,
                       headers=("ALGORITHM","HASH"), style="blue"),
            border_style="blue"))
    elif choice == "3":
        h1 = Prompt.ask("Hash 1").strip().lower()
        h2 = Prompt.ask("Hash 2").strip().lower()
        console.print("\n[green]✅ MATCH[/green]" if h1 == h2 else "\n[red]❌ MISMATCH[/red]")
    elif choice == "4":
        h = Prompt.ask("Hash").strip()
        LENGTHS = {32:"MD5", 40:"SHA-1", 56:"SHA-224", 64:"SHA-256",
                   96:"SHA-384", 128:"SHA-512"}
        guess = LENGTHS.get(len(h), "Unknown")
        console.print(f"\nLength {len(h)} chars → likely [bold]{guess}[/bold]")
    pause()

# ════════════════════════════════════════════════════════════
#   MAIN MENU
# ════════════════════════════════════════════════════════════

MENU = [
    ("1", "📱  Phone OSINT",   "cyan",        phone_lookup),
    ("2", "📧  Email OSINT",   "green",       email_lookup),
    ("3", "🌐  Domain OSINT",  "yellow",      domain_lookup),
    ("4", "🔍  IP OSINT",      "magenta",     ip_lookup),
    ("5", "📡  DNS Deep Scan", "bright_cyan", dns_scan),
    ("6", "🔑  Hash Tools",    "blue",        hash_tools),
    ("0", "🚪  Exit",          "dim red",     None),
]

def print_menu():
    clear()
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print(f"  [dim]{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}[/dim]\n")
    items = MENU[:-1]
    half  = (len(items) + 1) // 2
    for i in range(half):
        l = items[i]
        r = items[i + half] if i + half < len(items) else None
        lstr = f"  [{l[2]}][ {l[0]} ][/{l[2]}]  {l[1]:<30}"
        rstr = f"[{r[2]}][ {r[0]} ][/{r[2]}]  {r[1]}" if r else ""
        console.print(lstr + rstr)
    console.print(f"\n  [dim red][ 0 ][/dim red]  🚪 Exit\n")

def main():
    console.print(Panel(BANNER, title="KIZUNA X",
                        subtitle="Advanced OSINT Framework v3.0",
                        border_style="cyan"))
    while True:
        print_menu()
        choice = Prompt.ask("[bold]Select module[/bold]")
        if choice == "0":
            console.print("\n[red]Goodbye.[/red]\n")
            sys.exit(0)
        fn = next((f for k,_,_,f in MENU if k == choice and f), None)
        if fn:
            fn()
        else:
            console.print("[red]Invalid choice.[/red]")
            import time; time.sleep(0.6)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[red]Interrupted.[/red]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]FATAL:[/bold red] {e}")
        logging.critical(e, exc_info=True)
        sys.exit(1)
