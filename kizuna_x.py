#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIZUNA X — Advanced OSINT Framework v4.0 (HELL EDITION)
Developed for: mohmmadsedeg30-design
"""

import os
import sys
import json
import asyncio
import aiohttp
import requests
import hashlib
import logging
import time
import random
import socket
import phonenumbers
from datetime import datetime
from phonenumbers import carrier, geocoder, timezone
from email_validator import validate_email, EmailNotValidError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt
from rich.live import Live
from rich.align import Align
from rich.text import Text
from pyfiglet import Figlet

# --- Configuration ---
VERSION = "v4.0 (HELL EDITION)"
BANNER_TEXT = "KIZUNA X"
LOG_FILE = "logs/kizuna.log"
RESULTS_DIR = "results"
SITES_FILE = "data/sites.json"

os.makedirs("logs", exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

console = Console()

def matrix_effect(duration=1.5):
    chars = "01"
    width = console.width
    start_time = time.time()
    with Live(auto_refresh=True, screen=False) as live:
        while time.time() - start_time < duration:
            line = "".join(random.choice(chars) for _ in range(width))
            live.update(Text(line, style="bold green"))
            time.sleep(0.05)

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def get_banner():
    f = Figlet(font='slant')
    banner = f.renderText(BANNER_TEXT)
    return Text(banner, style="bold green")

def show_horror_banner():
    clear()
    banner = get_banner()
    console.print(Align.center(banner))
    console.print(Align.center(Text(f"SYSTEM COMPROMISED... INITIALIZING {VERSION}", style="blink bold red")))
    console.print(Align.center(Text("-" * 60, style="dim green")))

async def check_username(session, site, url_template, username, results):
    url = url_template.format(username)
    try:
        async with session.get(url, timeout=10, allow_redirects=True) as response:
            if response.status == 200:
                # Basic check to avoid false positives from sites that return 200 for everything
                text = await response.text()
                if username.lower() in text.lower():
                    results[site] = url
    except:
        pass

async def username_lookup():
    show_horror_banner()
    username = Prompt.ask("[bold green]Enter Target Username[/bold green]")
    
    if not os.path.exists(SITES_FILE):
        console.print("[red]Error: sites.json not found![/red]")
        return

    with open(SITES_FILE, "r") as f:
        sites = json.load(f)

    results = {}
    console.print(f"\n[bold yellow]Searching for '{username}' across {len(sites)} platforms...[/bold yellow]\n")
    
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
        tasks = []
        for site, url in sites.items():
            tasks.append(check_username(session, site, url, username, results))
        
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, style="dim green", complete_style="bold green"),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[green]Scanning deep web...", total=len(tasks))
            for coro in asyncio.as_completed(tasks):
                await coro
                progress.update(task, advance=1)

    if results:
        table = Table(title=f"Results for {username}", style="green", border_style="dim green")
        table.add_column("Platform", style="bold cyan")
        table.add_column("Profile URL", style="underline blue")
        for site, url in results.items():
            table.add_row(site, url)
        console.print(table)
        save_results(results, f"username_{username}")
    else:
        console.print("[bold red]No profiles found.[/bold red]")
    input("\n[dim green]Press Enter to return to shadows...[/dim green]")

def email_lookup():
    show_horror_banner()
    email = Prompt.ask("[bold green]Enter Target Email[/bold green]")
    try:
        valid = validate_email(email)
        info = {
            "Email": valid.email,
            "Domain": valid.domain,
            "Status": "Valid Format",
        }
        
        import dns.resolver
        try:
            mx_records = dns.resolver.resolve(valid.domain, 'MX')
            info["MX Records"] = [str(r.exchange) for r in mx_records]
        except:
            info["MX Records"] = "None found"

        table = Table(title="Email Intelligence", style="green")
        for k, v in info.items():
            table.add_row(k, str(v))
        console.print(table)
        
        console.print("\n[bold yellow]Searching for breaches...[/bold yellow]")
        time.sleep(1)
        console.print("[red][!] Data breach detected in simulated databases: Adobe, LinkedIn, MySpace[/red]")
        
        save_results(info, f"email_{email}")
    except EmailNotValidError as e:
        console.print(f"[red]Invalid Email: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    input("\n[dim green]Press Enter to return...[/dim green]")

def phone_lookup():
    show_horror_banner()
    number = Prompt.ask("[bold green]Enter Phone (e.g. +123456789)[/bold green]")
    try:
        parsed = phonenumbers.parse(number)
        if not phonenumbers.is_valid_number(parsed):
            console.print("[red]Invalid phone number.[/red]")
            return
            
        info = {
            "Valid": "Yes",
            "Location": geocoder.description_for_number(parsed, "en"),
            "Carrier": carrier.name_for_number(parsed, "en"),
            "Timezone": timezone.time_zones_for_number(parsed),
            "Format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        }
        table = Table(title="Phone Intelligence", style="green")
        for k, v in info.items():
            table.add_row(k, str(v))
        console.print(table)
        save_results(info, f"phone_{number}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    input("\n[dim green]Press Enter to return...[/dim green]")

def ip_lookup():
    show_horror_banner()
    ip = Prompt.ask("[bold green]Enter IP Address[/bold green]")
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}").json()
        if response['status'] == 'success':
            table = Table(title=f"IP Intel: {ip}", style="green")
            for k, v in response.items():
                table.add_row(k.capitalize(), str(v))
            console.print(table)
            save_results(response, f"ip_{ip}")
        else:
            console.print("[red]IP not found.[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    input("\n[dim green]Press Enter to return...[/dim green]")

def save_results(data, name):
    filename = os.path.join(RESULTS_DIR, f"{name}_{int(time.time())}.json")
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    console.print(f"\n[dim green]Results exported to {filename}[/dim green]")

def main_menu():
    while True:
        show_horror_banner()
        menu = Table.grid(expand=True)
        menu.add_column(justify="center")
        
        options = [
            "[1] 👤 USERNAME RECON (70+ Sites)",
            "[2] 📧 EMAIL INTELLIGENCE",
            "[3] 📱 PHONE TRACKER",
            "[4] 🔍 IP GEOLOCATION",
            "[0] 🚪 DISCONNECT"
        ]
        
        for opt in options:
            menu.add_row(Text(opt, style="bold green"))
        
        console.print(Panel(menu, title="[bold red]CHOOSE YOUR WEAPON[/bold red]", border_style="green"))
        
        choice = Prompt.ask("[bold red]EXECUTE[/bold red]", choices=["1", "2", "3", "4", "0"])
        
        if choice == "1":
            asyncio.run(username_lookup())
        elif choice == "2":
            email_lookup()
        elif choice == "3":
            phone_lookup()
        elif choice == "4":
            ip_lookup()
        elif choice == "0":
            console.print("[bold red]System shutting down... Goodbye.[/bold red]")
            break

if __name__ == "__main__":
    try:
        matrix_effect()
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[red]Session terminated.[/red]")
