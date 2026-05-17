#!/usr/bin/env python3
##  KIZUNA X  v4.0  —  50 Tools: OSINT · Media · Fun · Utilities
##  Author: mohmmadsedeg30-design  |  License: MIT

import os,sys,json,socket,hashlib,logging,ipaddress,threading
import time,math,random,base64,urllib.parse,shutil,platform,re,ssl
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor,as_completed
from typing import Optional

# ── auto-install ──────────────────────────────────────────────
PKGS={"requests":"requests","phonenumbers":"phonenumbers","dns":"dnspython",
      "whois":"python-whois","email_validator":"email-validator",
      "dotenv":"python-dotenv","PIL":"Pillow","rich":"rich",
      "pyfiglet":"pyfiglet","qrcode":"qrcode[pil]","colorama":"colorama"}
import importlib
for mod,pkg in PKGS.items():
    if not importlib.util.find_spec(mod):
        os.system(f"pip install {pkg} --break-system-packages -q")

import requests,phonenumbers,dns.resolver,whois
from phonenumbers import carrier,geocoder,timezone as ph_tz
from email_validator import validate_email,EmailNotValidError
from dotenv import load_dotenv
from PIL import Image
import pyfiglet,qrcode,colorama
from colorama import Fore,Style
from rich.console import Console,Group
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.progress import Progress,SpinnerColumn,BarColumn,TextColumn
from rich import box

load_dotenv(); colorama.init(autoreset=True)
for d in ("logs","results","output"): os.makedirs(d,exist_ok=True)
logging.basicConfig(filename="logs/kizuna.log",level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
console=Console()

BANNER=r"""
██╗  ██╗██╗███████╗██╗   ██╗███╗   ██╗ █████╗
██║ ██╔╝██║╚══███╔╝██║   ██║████╗  ██║██╔══██╗
█████╔╝ ██║  ███╔╝ ██║   ██║██╔██╗ ██║███████║
██╔═██╗ ██║ ███╔╝  ██║   ██║██║╚██╗██║██╔══██║
██║  ██╗██║███████╗╚██████╔╝██║ ╚████║██║  ██║
╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
      50 Tools · OSINT · Media · Fun · Utils  v4.0
"""

# ── helpers ───────────────────────────────────────────────────
def clear(): os.system("clear" if os.name!="nt" else "cls")
def pause(): console.print("\n[dim][ ENTER ][/dim]"); input()
def log(a,t): logging.info(f"{a:<20} | {t}")
def http_get(url,params=None,timeout=10):
    try: return requests.get(url,params=params,timeout=timeout,headers={"User-Agent":"KizunaX/4.0"})
    except: return None
def section(title,color="cyan"):
    clear(); console.print(Panel.fit(f"[bold]{title}[/bold]",style=color,padding=(0,4))); console.print()
def make_table(title,rows,headers=("FIELD","VALUE"),style="cyan"):
    t=Table(title=title,box=box.ROUNDED,border_style=style,
            header_style=f"bold {style}",show_lines=True,title_style=f"bold {style}")
    for h in headers: t.add_column(h,overflow="fold")
    for r in rows: t.add_row(*[str(c) for c in r])
    return t
def save_json(name,data):
    ts=datetime.now().strftime("%Y%m%d_%H%M%S"); p=f"results/{name}_{ts}.json"
    with open(p,"w",encoding="utf-8") as f: json.dump(data,f,indent=4,default=str,ensure_ascii=False)
    console.print(f"[dim]saved → {p}[/dim]")
def ask_save(data,name):
    if Prompt.ask("\n[dim]Save?[/dim]",choices=["y","n"],default="n")=="y": save_json(name,data)

ASCII_CHARS="@%#*+=-:. "
def resize_img(img,w=100):
    ow,oh=img.size; return img.resize((w,int(w*(oh/ow)/2.0)))
def p2a(v): return ASCII_CHARS[v*len(ASCII_CHARS)//256]

# ════════════════════════════════════════════════════════════
#  OSINT TOOLS  1-10
# ════════════════════════════════════════════════════════════
def t01_phone():
    section("📱 PHONE OSINT","cyan")
    n=Prompt.ask("[cyan]Number[/cyan] (+966XXXXXXXXX)")
    try:
        p=phonenumbers.parse(n); valid=phonenumbers.is_valid_number(p)
        e164=phonenumbers.format_number(p,phonenumbers.PhoneNumberFormat.E164)
        TYPES={0:"FIXED",1:"MOBILE",2:"FIXED/MOBILE",3:"TOLL_FREE",6:"VOIP"}
        rows=[("E164",e164),("International",phonenumbers.format_number(p,phonenumbers.PhoneNumberFormat.INTERNATIONAL)),
              ("Valid","✅" if valid else "❌"),("Country",geocoder.description_for_number(p,"en") or "—"),
              ("Carrier",carrier.name_for_number(p,"en") or "—"),
              ("Type",TYPES.get(phonenumbers.number_type(p),"UNKNOWN")),
              ("Dial Code",f"+{p.country_code}"),
              ("Timezones",", ".join(ph_tz.time_zones_for_number(p)) or "—")]
        k=os.getenv("NUMVERIFY_API_KEY")
        if k:
            r=http_get("http://apilayer.net/api/validate",params={"access_key":k,"number":e164})
            if r and r.ok:
                d=r.json()
                for key in ("carrier","line_type","location"):
                    if d.get(key): rows.append((key.title(),d[key]))
        console.print(make_table(f"PHONE: {n}",rows)); ask_save(dict(rows),"phone")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t02_email():
    section("📧 EMAIL OSINT","green")
    email=Prompt.ask("[green]Email[/green]")
    try:
        v=validate_email(email,check_deliverability=True); d=v.domain
        rows=[("Normalized",v.normalized),("Domain",d)]
        try:
            for r in sorted(dns.resolver.resolve(d,"MX"),key=lambda x:x.preference):
                rows.append((f"MX p{r.preference}",str(r.exchange).rstrip(".")))
        except: rows.append(("MX","None"))
        for lb,qn in [("SPF",""),("DMARC","_dmarc."),("DKIM","default._domainkey.")]:
            try:
                for rec in dns.resolver.resolve(f"{qn}{d}","TXT",lifetime=4):
                    rows.append((lb,str(rec).strip('"')[:80]))
            except: rows.append((lb,"Not found"))
        try:
            r=http_get("https://disposable.github.io/disposable-email-domains/domains.json",timeout=5)
            if r: rows.append(("Disposable","⚠️" if d in set(r.json()) else "✅"))
        except: pass
        console.print(make_table(f"EMAIL: {email}",rows,style="green")); ask_save(dict(rows),"email")
    except EmailNotValidError as e: console.print(f"[red]{e}[/red]")
    pause()

def t03_ip():
    section("🔍 IP OSINT","magenta")
    raw=Prompt.ask("[magenta]IP/hostname[/magenta]")
    try: ipaddress.ip_address(raw); ip=raw
    except:
        try: ip=socket.gethostbyname(raw); console.print(f"[dim]→{ip}[/dim]")
        except: console.print("[red]Cannot resolve.[/red]"); pause(); return
    rows=[("Query",ip)]
    try:
        r=http_get(f"http://ip-api.com/json/{ip}?fields=66846719")
        if r:
            d=r.json()
            for k in ["country","regionName","city","zip","lat","lon","timezone","isp","org","as","reverse","mobile","proxy","hosting"]:
                if k in d: rows.append((k.title(),str(d[k])))
            if d.get("lat") and d.get("lon"):
                rows.append(("Maps",f"https://maps.google.com/?q={d['lat']},{d['lon']}"))
    except: pass
    try:
        rev=".".join(reversed(ip.split(".")))+".in-addr.arpa"
        rows.append(("PTR",str(list(dns.resolver.resolve(rev,"PTR",lifetime=4))[0]).rstrip(".")))
    except: pass
    console.print(make_table(f"IP: {ip}",rows,style="magenta")); ask_save(dict(rows),"ip"); pause()

def t04_domain():
    section("🌐 DOMAIN OSINT","yellow")
    t=Prompt.ask("[yellow]Domain[/yellow]"); rows=[]
    try:
        info=whois.whois(t)
        for k in ["domain_name","registrar","creation_date","expiration_date","updated_date","name_servers","org","country"]:
            if info.get(k): rows.append((k.replace("_"," ").title(),str(info[k])[:80]))
    except Exception as e: rows.append(("WHOIS Error",str(e)))
    for rt in ["A","AAAA","MX","NS","TXT","SOA","CAA"]:
        try:
            for a in dns.resolver.resolve(t,rt,lifetime=4): rows.append((f"DNS {rt}",str(a).rstrip(".")[:80]))
        except: pass
    try:
        r=http_get(f"https://crt.sh/?q=%.{t}&output=json",timeout=12)
        if r:
            subs=set()
            for e in r.json():
                for n in e.get("name_value","").split("\n"):
                    n=n.strip().lower()
                    if n.endswith(t) and "*" not in n: subs.add(n)
            for i,s in enumerate(sorted(subs)[:15]): rows.append((f"Sub {i+1}",s))
    except: pass
    console.print(make_table(f"DOMAIN: {t}",rows,style="yellow")); ask_save(rows,"domain"); pause()

def t05_dns():
    section("📡 DNS DEEP SCAN","bright_cyan")
    t=Prompt.ask("[bright_cyan]Domain[/bright_cyan]"); rows=[]
    for rt in ["A","AAAA","CNAME","MX","NS","TXT","SOA","CAA","DNSKEY","SRV"]:
        try:
            for a in dns.resolver.resolve(t,rt,lifetime=5): rows.append((rt,str(a).rstrip(".")))
        except: pass
    try:
        for ns in dns.resolver.resolve(t,"NS",lifetime=4):
            try:
                z=dns.zone.from_xfr(dns.query.xfr(str(ns).rstrip("."),t,lifetime=5))
                rows.append(("AXFR",f"⚠️ VULNERABLE — {len(z.nodes)} records")); break
            except: rows.append(("AXFR","✅ Refused"))
    except: pass
    console.print(make_table(f"DNS:{t}",rows,headers=("TYPE","VALUE"),style="bright_cyan"))
    ask_save(rows,"dns"); pause()

WORDLIST=["www","mail","api","dev","staging","admin","cdn","app","portal","vpn",
          "ftp","smtp","ns1","ns2","shop","blog","support","git","dashboard","test","auth"]
def t06_subdomains():
    section("🔭 SUBDOMAIN ENUM","bright_green")
    domain=Prompt.ask("[bright_green]Domain[/bright_green]"); found={}
    console.print("[yellow]crt.sh…[/yellow]")
    try:
        r=http_get(f"https://crt.sh/?q=%.{domain}&output=json",timeout=15)
        if r:
            for e in r.json():
                for n in e.get("name_value","").split("\n"):
                    n=n.strip().lower()
                    if n.endswith(f".{domain}") and "*" not in n: found.setdefault(n,[]).append("crt.sh")
    except: pass
    console.print("[yellow]DNS bruteforce…[/yellow]"); lock=threading.Lock()
    def chk(sub):
        fqdn=f"{sub}.{domain}"
        try:
            ans=dns.resolver.resolve(fqdn,"A",lifetime=2)
            with lock: found.setdefault(fqdn,[]).append(f"DNS:{','.join(str(r) for r in ans)}")
        except: pass
    with ThreadPoolExecutor(max_workers=80) as ex: list(ex.map(chk,WORDLIST))
    rows=[(s,", ".join(src)) for s,src in sorted(found.items())]
    console.print(make_table(f"SUBDOMAINS:{domain}({len(rows)})",rows,headers=("SUBDOMAIN","SOURCE"),style="bright_green"))
    ask_save(found,"subdomains"); pause()

def t07_ssl():
    section("🔒 SSL CERTIFICATE","bright_white")
    host=Prompt.ask("[white]Domain[/white]"); port=int(Prompt.ask("Port","443"))
    try:
        ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
        with ctx.wrap_socket(socket.socket(),server_hostname=host) as s:
            s.settimeout(8); s.connect((host,port)); cert=s.getpeercert()
        rows=[("Subject",str(cert.get("subject",""))),("Issuer",str(cert.get("issuer",""))),
              ("Valid From",cert.get("notBefore","—")),("Valid To",cert.get("notAfter","—")),
              ("Serial",str(cert.get("serialNumber","—")))]
        for tp,v in cert.get("subjectAltName",())[:8]: rows.append((f"SAN({tp})",v))
        console.print(make_table(f"SSL:{host}",rows,style="bright_white")); ask_save(dict(rows),"ssl")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t08_myip():
    section("🌍 MY IP INFO","cyan"); rows=[]
    try:
        r=http_get("https://api.ipify.org?format=json")
        if r: rows.append(("Public IP",r.json().get("ip","?")))
    except: pass
    try: rows.append(("Local IP",socket.gethostbyname(socket.gethostname())))
    except: pass
    try:
        if rows:
            r=http_get(f"http://ip-api.com/json/{rows[0][1]}?fields=66846719")
            if r:
                d=r.json()
                for k in ["country","regionName","city","isp","org","timezone"]:
                    if k in d: rows.append((k.title(),d[k]))
    except: pass
    console.print(make_table("MY IP",rows)); pause()

def t09_url_expand():
    section("🔗 URL EXPANDER","cyan")
    url=Prompt.ask("[cyan]Short URL[/cyan]")
    try:
        r=requests.get(url,allow_redirects=True,timeout=10)
        rows=[("Original",url),("Final",r.url),("Status",str(r.status_code)),("Hops",str(len(r.history)))]
        for i,h in enumerate(r.history): rows.append((f"Redirect {i+1}",h.url))
        console.print(make_table("URL EXPAND",rows))
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t10_http_headers():
    section("🌐 HTTP HEADERS","yellow")
    url=Prompt.ask("[yellow]URL[/yellow]")
    if not url.startswith("http"): url="https://"+url
    try:
        r=requests.get(url,timeout=10,headers={"User-Agent":"KizunaX/4.0"})
        rows=[("Status",str(r.status_code)),("Final URL",r.url)]+list(r.headers.items())
        console.print(make_table(f"HEADERS:{url}",rows,style="yellow"))
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

# ════════════════════════════════════════════════════════════
#  MEDIA TOOLS  11-20
# ════════════════════════════════════════════════════════════
def t11_img_ascii_bw():
    section("🖼️ IMAGE → ASCII (B&W)","white")
    path=Prompt.ask("Image path").strip()
    if not os.path.isfile(path): console.print("[red]Not found.[/red]"); pause(); return
    w=int(Prompt.ask("Width","120"))
    try:
        img=resize_img(Image.open(path).convert("L"),w)
        pixels=list(img.getdata()); iw=img.width; art=""
        for i,p in enumerate(pixels):
            art+=p2a(p)
            if (i+1)%iw==0: art+="\n"
        out=f"output/ascii_bw_{datetime.now().strftime('%H%M%S')}.txt"
        with open(out,"w",encoding="utf-8") as f: f.write(art)
        for line in art.split("\n")[:25]: print(line)
        console.print(f"\n[dim]saved → {out}[/dim]")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t12_img_ascii_color():
    section("🎨 IMAGE → ASCII (COLORED)","bright_magenta")
    path=Prompt.ask("Image path").strip()
    if not os.path.isfile(path): console.print("[red]Not found.[/red]"); pause(); return
    w=int(Prompt.ask("Width","80"))
    try:
        img=resize_img(Image.open(path).convert("RGB"),w)
        iw=img.width; pixels=list(img.getdata()); lines=[]; row=""
        for i,(r,g,b) in enumerate(pixels):
            gray=int(0.299*r+0.587*g+0.114*b)
            row+=f"\033[38;2;{r};{g};{b}m{p2a(gray)}"
            if (i+1)%iw==0: lines.append(row+"\033[0m"); row=""
        for line in lines[:25]: print(line)
        out=f"output/ascii_color_{datetime.now().strftime('%H%M%S')}.txt"
        with open(out,"w",encoding="utf-8") as f: f.write("\n".join(lines))
        console.print(f"\n[dim]saved → {out}[/dim]")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t13_img_blocks():
    section("🟦 IMAGE → BLOCK ART","bright_cyan")
    path=Prompt.ask("Image path").strip()
    if not os.path.isfile(path): console.print("[red]Not found.[/red]"); pause(); return
    w=int(Prompt.ask("Width blocks","60"))
    try:
        img=resize_img(Image.open(path).convert("RGB"),w); iw=img.width
        for i,(r,g,b) in enumerate(list(img.getdata())):
            print(f"\033[48;2;{r};{g};{b}m  \033[0m",end="")
            if (i+1)%iw==0: print()
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t14_video_ascii_color():
    section("🎬 VIDEO → ASCII (COLORED)","bright_yellow")
    try: import cv2
    except: console.print("[red]pip install opencv-python-headless --break-system-packages[/red]"); pause(); return
    path=Prompt.ask("Video path").strip()
    if not os.path.isfile(path): console.print("[red]Not found.[/red]"); pause(); return
    w=int(Prompt.ask("Width","80")); fps=int(Prompt.ask("Max FPS","10"))
    cap=cv2.VideoCapture(path)
    if not cap.isOpened(): console.print("[red]Cannot open.[/red]"); pause(); return
    vfps=cap.get(cv2.CAP_PROP_FPS) or 24; skip=max(1,int(vfps/fps)); fn=0
    console.print("[dim]Ctrl+C to stop[/dim]")
    try:
        while True:
            ret,frame=cap.read()
            if not ret: break
            fn+=1
            if fn%skip!=0: continue
            from PIL import Image as PILImage
            img=resize_img(PILImage.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)),w)
            iw=img.width; pixels=list(img.getdata()); rows_out=[]; row=""
            for i,(r,g,b) in enumerate(pixels):
                row+=f"\033[38;2;{r};{g};{b}m{p2a(int(0.299*r+0.587*g+0.114*b))}"
                if (i+1)%iw==0: rows_out.append(row+"\033[0m"); row=""
            os.system("clear"); print("\n".join(rows_out)); time.sleep(1/fps)
    except KeyboardInterrupt: pass
    cap.release(); pause()

def t15_video_ascii_bw():
    section("🎬 VIDEO → ASCII (B&W)","white")
    try: import cv2
    except: console.print("[red]pip install opencv-python-headless --break-system-packages[/red]"); pause(); return
    path=Prompt.ask("Video path").strip()
    if not os.path.isfile(path): console.print("[red]Not found.[/red]"); pause(); return
    w=int(Prompt.ask("Width","100")); fps=int(Prompt.ask("Max FPS","10"))
    cap=cv2.VideoCapture(path)
    if not cap.isOpened(): console.print("[red]Cannot open.[/red]"); pause(); return
    vfps=cap.get(cv2.CAP_PROP_FPS) or 24; skip=max(1,int(vfps/fps)); fn=0
    console.print("[dim]Ctrl+C to stop[/dim]")
    try:
        while True:
            ret,frame=cap.read()
            if not ret: break
            fn+=1
            if fn%skip!=0: continue
            from PIL import Image as PILImage
            img=resize_img(PILImage.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)).convert("L"),w)
            pixels=list(img.getdata()); iw=img.width; art=""
            for i,p in enumerate(pixels):
                art+=p2a(p)
                if (i+1)%iw==0: art+="\n"
            os.system("clear"); print(art); time.sleep(1/fps)
    except KeyboardInterrupt: pass
    cap.release(); pause()

def t16_img_info():
    section("ℹ️ IMAGE INFO","white"); path=Prompt.ask("Image path").strip()
    if not os.path.isfile(path): console.print("[red]Not found.[/red]"); pause(); return
    try:
        img=Image.open(path)
        rows=[("File",os.path.basename(path)),("Format",img.format or "—"),("Mode",img.mode),
              ("Size",f"{img.width}×{img.height}px"),("File Size",f"{os.path.getsize(path)//1024}KB")]
        try:
            from PIL.ExifTags import TAGS
            raw=img._getexif()
            if raw:
                for tag,val in list(raw.items())[:15]:
                    rows.append((str(TAGS.get(tag,tag)),str(val)[:60]))
        except: pass
        console.print(make_table("IMAGE INFO",rows))
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t17_img_resize():
    section("📐 IMAGE RESIZE","cyan"); path=Prompt.ask("Image path").strip()
    if not os.path.isfile(path): console.print("[red]Not found.[/red]"); pause(); return
    w=int(Prompt.ask("Width px")); h=int(Prompt.ask("Height px"))
    try:
        out=f"output/resized_{w}x{h}_{os.path.basename(path)}"
        Image.open(path).resize((w,h),Image.LANCZOS).save(out)
        console.print(f"[green]✅ {out}[/green]")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t18_img_gray():
    section("⬛ IMAGE → GRAYSCALE","white"); path=Prompt.ask("Image path").strip()
    if not os.path.isfile(path): console.print("[red]Not found.[/red]"); pause(); return
    try:
        out=f"output/gray_{os.path.basename(path)}"
        Image.open(path).convert("L").save(out); console.print(f"[green]✅ {out}[/green]")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t19_img_negative():
    section("🔄 IMAGE → NEGATIVE","bright_white"); path=Prompt.ask("Image path").strip()
    if not os.path.isfile(path): console.print("[red]Not found.[/red]"); pause(); return
    try:
        from PIL import ImageOps
        out=f"output/negative_{os.path.basename(path)}"
        ImageOps.invert(Image.open(path).convert("RGB")).save(out); console.print(f"[green]✅ {out}[/green]")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t20_qr():
    section("📲 QR CODE GENERATOR","green")
    data=Prompt.ask("[green]Text/URL[/green]"); name=Prompt.ask("Filename","qr")
    try:
        qr=qrcode.QRCode(version=1,box_size=10,border=4)
        qr.add_data(data); qr.make(fit=True)
        out=f"output/{name}.png"; qr.make_image(fill_color="black",back_color="white").save(out)
        console.print(f"[green]✅ {out}[/green]")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

# ════════════════════════════════════════════════════════════
#  FUN TOOLS  21-30
# ════════════════════════════════════════════════════════════
def t21_ascii_text():
    section("✍️ ASCII TEXT ART","bright_yellow")
    text=Prompt.ask("[yellow]Text[/yellow]"); font=Prompt.ask("Font (slant/banner3/doom/big)","slant")
    try:
        art=pyfiglet.figlet_format(text,font=font)
        color=random.choice(["cyan","magenta","yellow","green","bright_blue"])
        console.print(f"[bold {color}]{art}[/bold {color}]")
        if Prompt.ask("Save?",choices=["y","n"],default="n")=="y":
            out=f"output/ascii_text_{datetime.now().strftime('%H%M%S')}.txt"
            with open(out,"w") as f: f.write(art)
            console.print(f"[dim]{out}[/dim]")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t22_rainbow():
    section("🌈 RAINBOW TEXT","bright_magenta")
    text=Prompt.ask("[magenta]Text[/magenta]"); big=Prompt.ask("Big?",choices=["y","n"],default="y")
    if big=="y": text=pyfiglet.figlet_format(text,font="slant")
    C=["\033[31m","\033[33m","\033[32m","\033[36m","\033[34m","\033[35m"]; i=0
    for ch in text:
        if ch not in (" ","\n"): print(f"{C[i%len(C)]}{ch}\033[0m",end=""); i+=1
        else: print(ch,end="")
    print(); pause()

def t23_matrix():
    section("💚 MATRIX RAIN","green"); dur=int(Prompt.ask("Duration (s)","10"))
    cols=shutil.get_terminal_size().columns
    chars="アイウエオカキクケコ0123456789ABCDEF"
    drops=[random.randint(-20,0) for _ in range(cols//2)]
    end=time.time()+dur
    try:
        while time.time()<end:
            line=""
            for i,drop in enumerate(drops):
                if drop>0 and random.random()>0.5: line+=f"\033[32m{random.choice(chars)}\033[0m "
                else: line+="  "
                drops[i]+=1
                if drops[i]>random.randint(10,30): drops[i]=random.randint(-20,0)
            print("\r"+line[:cols],end="",flush=True); time.sleep(0.05)
        print()
    except KeyboardInterrupt: print()
    pause()

def t24_hacker_typer():
    section("⌨️ HACKER TYPER","green")
    console.print("[dim]Press any key to type. Ctrl+C to stop.[/dim]\n")
    CODE="import socket,os,threading\nfrom cryptography.fernet import Fernet\n\ndef run(host,port=443):\n    key=Fernet.generate_key()\n    f=Fernet(key)\n    payload=f.encrypt(b'DATA_XOR_0xFF')\n    s=socket.socket()\n    s.connect((host,port))\n    s.sendall(payload)\n    return f.decrypt(s.recv(4096))\n\nif __name__=='__main__':\n    import sys\n    print('[*] Connecting to',sys.argv[1])\n    print('[+]',run(sys.argv[1]))\n"
    idx=0
    try:
        import tty,termios
        fd=sys.stdin.fileno(); old=termios.tcgetattr(fd); tty.setraw(fd)
        while True:
            ch=sys.stdin.read(1)
            if ch=="\x03": break
            while idx<len(CODE) and CODE[idx]==" ": idx+=1
            if idx<len(CODE):
                c=CODE[idx]; idx+=1
                if c=="\n": print()
                else: print(f"\033[32m{c}\033[0m",end="",flush=True)
        termios.tcsetattr(fd,termios.TCSADRAIN,old)
    except Exception:
        for line in CODE.split("\n"):
            for ch in line: print(f"\033[32m{ch}\033[0m",end="",flush=True); time.sleep(0.04)
            print()
    print(); pause()

def t25_spinners():
    section("⏳ SPINNERS DEMO","cyan")
    for sp in ["⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏","◐◓◑◒","▖▘▝▗","←↖↑↗→↘↓↙"]:
        for _ in range(3):
            for ch in sp: print(f"\r\033[36m{ch}\033[0m Running…",end="",flush=True); time.sleep(0.1)
    print("\r[Done]            "); pause()

def t26_colors():
    section("🎨 COLOR PALETTE","bright_magenta")
    print("\n── 8 Basic ──")
    for i in range(8): print(f"\033[4{i}m  {i}  \033[0m",end=" ")
    print("\n\n── 256 Colors ──")
    for i in range(256):
        print(f"\033[48;5;{i}m  \033[0m",end="")
        if (i+1)%16==0: print()
    print("\n\n── RGB Gradient ──")
    for r in range(0,256,32):
        for g in range(0,256,64): print(f"\033[48;2;{r};{g};128m  \033[0m",end="")
        print()
    pause()

def t27_clock():
    section("🕐 ASCII LIVE CLOCK","cyan"); console.print("[dim]Ctrl+C stop[/dim]")
    try:
        while True:
            os.system("clear")
            console.print(f"[bold cyan]{pyfiglet.figlet_format(datetime.now().strftime('%H:%M:%S'),font='big')}[/bold cyan]")
            console.print(f"[dim]{datetime.now().strftime('%A, %B %d, %Y')}[/dim]"); time.sleep(1)
    except KeyboardInterrupt: pass
    pause()

def t28_countdown():
    section("⏱️ COUNTDOWN TIMER","yellow"); sec=int(Prompt.ask("[yellow]Seconds[/yellow]"))
    try:
        for r in range(sec,0,-1):
            os.system("clear"); console.print(f"[bold yellow]{pyfiglet.figlet_format(str(r),font='big')}[/bold yellow]"); time.sleep(1)
        os.system("clear"); console.print(f"[bold green]{pyfiglet.figlet_format('DONE!',font='big')}[/bold green]"); print("\a")
    except KeyboardInterrupt: pass
    pause()

def t29_passgen():
    import string; section("🔐 PASSWORD GENERATOR","bright_green")
    length=int(Prompt.ask("Length","16")); count=int(Prompt.ask("Count","5"))
    sym=Prompt.ask("Symbols?",choices=["y","n"],default="y")
    chars=string.ascii_letters+string.digits+("!@#$%^&*" if sym=="y" else "")
    rows=[(str(i+1),"".join(random.choices(chars,k=length))) for i in range(count)]
    console.print(make_table("PASSWORDS",rows,headers=("#","PASSWORD"),style="bright_green")); pause()

JOKES=[("Why do programmers prefer dark mode?","Because light attracts bugs! 🐛"),
       ("How many programmers to change a bulb?","None — that's a hardware problem."),
       ("Why do Java devs wear glasses?","Because they don't C#."),
       ("A SQL query walks into a bar…","…asks two tables: 'Can I JOIN you?'"),
       ("Why was the JS developer sad?","He didn't Node how to Express himself."),
       ("99 bugs in the code…","Take one down — 127 bugs in the code."),
       ("!false","It's funny because it's true."),
       ("How to comfort a JS bug?","You console it.")]
def t30_joke():
    section("😂 RANDOM JOKE","bright_yellow")
    q,a=random.choice(JOKES)
    console.print(Panel(f"[bold yellow]{q}[/bold yellow]",title="❓",border_style="yellow"))
    Prompt.ask("[dim]ENTER for answer[/dim]",default="")
    console.print(Panel(f"[bold green]{a}[/bold green]",title="💡",border_style="green")); pause()

# ════════════════════════════════════════════════════════════
#  UTILITIES  31-50
# ════════════════════════════════════════════════════════════
def t31_quote():
    section("💬 RANDOM QUOTE","bright_cyan")
    try:
        r=http_get("https://api.quotable.io/random",timeout=6)
        if r and r.ok:
            d=r.json()
            console.print(Panel(f'[italic cyan]"{d["content"]}"[/italic cyan]\n\n[dim]— {d["author"]}[/dim]',title="Quote",border_style="cyan",padding=(1,4)))
        else: raise Exception()
    except:
        quotes=[("First, solve the problem. Then, write the code.","John Johnson"),
                ("Code is like humor. When you have to explain it, it's bad.","Cory House"),
                ("Make it work, make it right, make it fast.","Kent Beck")]
        q,a=random.choice(quotes)
        console.print(Panel(f'[italic cyan]"{q}"[/italic cyan]\n\n[dim]— {a}[/dim]',title="Quote",border_style="cyan",padding=(1,4)))
    pause()

def t32_base64():
    section("🔤 BASE64 TOOL","blue"); console.print("[1] Encode  [2] Decode"); c=Prompt.ask("Select",choices=["1","2"])
    text=Prompt.ask("Input")
    try:
        if c=="1": console.print(f"\n[green]{base64.b64encode(text.encode()).decode()}[/green]")
        else: console.print(f"\n[green]{base64.b64decode(text.encode()).decode()}[/green]")
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

MORSE={'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..','0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.','.':".-.-.-",',':"--..--",'?':"..--..",' ':'/'}
def t33_encoder():
    section("🔡 TEXT ENCODER","bright_blue")
    console.print("[1] Caesar  [2] ROT13  [3] Text→Morse  [4] Morse→Text")
    c=Prompt.ask("Select",choices=["1","2","3","4"]); text=Prompt.ask("Input")
    if c=="1":
        sh=int(Prompt.ask("Shift","13"))
        r="".join(chr((ord(ch)-ord('A')+sh)%26+ord('A')) if ch.isupper() else chr((ord(ch)-ord('a')+sh)%26+ord('a')) if ch.islower() else ch for ch in text)
        console.print(f"\n[green]{r}[/green]")
    elif c=="2":
        import codecs; console.print(f"\n[green]{codecs.encode(text,'rot_13')}[/green]")
    elif c=="3":
        console.print(f"\n[green]{' '.join(MORSE.get(ch.upper(),'?') for ch in text)}[/green]")
    elif c=="4":
        rev={v:k for k,v in MORSE.items()}; console.print(f"\n[green]{''.join(rev.get(w,'?') for w in text.split())}[/green]")
    pause()

def t34_units():
    section("📏 UNIT CONVERTER","cyan"); console.print("[1] Temperature  [2] Length  [3] Weight  [4] Data")
    c=Prompt.ask("Select",choices=["1","2","3","4"]); v=float(Prompt.ask("Value"))
    if c=="1":
        console.print(make_table("TEMPERATURE",[("°C→°F",f"{v*9/5+32:.2f}"),("°C→K",f"{v+273.15:.2f}"),("°F→°C",f"{(v-32)*5/9:.2f}")]))
    elif c=="2":
        console.print(make_table("LENGTH",[("km→mi",f"{v*0.621371:.4f}"),("mi→km",f"{v*1.60934:.4f}"),("m→ft",f"{v*3.28084:.4f}"),("ft→m",f"{v*0.3048:.4f}"),("in→cm",f"{v*2.54:.4f}"),("cm→in",f"{v/2.54:.4f}")]))
    elif c=="3":
        console.print(make_table("WEIGHT",[("kg→lbs",f"{v*2.20462:.4f}"),("lbs→kg",f"{v*0.453592:.4f}"),("g→oz",f"{v*0.035274:.4f}")]))
    elif c=="4":
        console.print(make_table("DATA",[("Bytes→KB",f"{v/1024:.4f}"),("Bytes→MB",f"{v/1048576:.4f}"),("Bytes→GB",f"{v/1073741824:.4f}"),("KB→MB",f"{v/1024:.4f}"),("MB→GB",f"{v/1024:.4f}")]))
    pause()

def t35_base_conv():
    section("🔢 BASE CONVERTER","blue"); inp=Prompt.ask("[blue]Input[/blue]"); frm=int(Prompt.ask("From base","10"))
    try:
        n=int(inp,frm)
        console.print(make_table("BASE CONVERSION",[("Binary",bin(n)[2:]),("Octal",oct(n)[2:]),("Decimal",str(n)),("Hex",hex(n)[2:].upper())],style="blue"))
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t36_text_stats():
    section("📊 TEXT STATS","green"); console.print("[dim]Paste text, then press Enter twice:[/dim]")
    lines=[]; 
    while True:
        l=input(); lines.append(l)
        if len(lines)>=2 and lines[-1]=="" and lines[-2]=="": break
    text="\n".join(lines); words=text.split()
    console.print(make_table("TEXT STATS",[
        ("Chars (with spaces)",len(text)),("Chars (no spaces)",len(text.replace(" ",""))),
        ("Words",len(words)),("Lines",text.count("\n")+1),
        ("Sentences",text.count(".")+text.count("!")+text.count("?")),
        ("Avg word len",f"{sum(len(w) for w in words)/max(len(words),1):.1f}"),
    ],style="green")); pause()

def t37_url_enc():
    section("🔗 URL ENCODE/DECODE","cyan"); console.print("[1] Encode  [2] Decode")
    c=Prompt.ask("Select",choices=["1","2"]); text=Prompt.ask("Input")
    console.print(f"\n[green]{urllib.parse.quote(text) if c=='1' else urllib.parse.unquote(text)}[/green]"); pause()

def t38_ping():
    section("📶 PING","cyan"); host=Prompt.ask("[cyan]Host[/cyan]"); count=Prompt.ask("Count","4")
    os.system(f"ping -c {count} {host}" if os.name!="nt" else f"ping -n {count} {host}"); pause()

def t39_traceroute():
    section("🗺️ TRACEROUTE","magenta"); host=Prompt.ask("[magenta]Host[/magenta]")
    os.system(f"traceroute {host}" if os.name!="nt" else f"tracert {host}"); pause()

def t40_dns_quick():
    section("📡 DNS QUICK","bright_cyan"); domain=Prompt.ask("[cyan]Domain[/cyan]"); rtype=Prompt.ask("Type","A").upper()
    try:
        rows=[(rtype,str(a).rstrip(".")) for a in dns.resolver.resolve(domain,rtype,lifetime=5)]
        console.print(make_table(f"DNS {rtype}:{domain}",rows,headers=("TYPE","VALUE"),style="bright_cyan"))
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t41_whois():
    section("🌐 WHOIS QUICK","yellow"); t=Prompt.ask("[yellow]Domain/IP[/yellow]")
    try:
        info=whois.whois(t); rows=[(k.replace("_"," ").title(),str(v)[:80]) for k,v in info.items() if v][:20]
        console.print(make_table(f"WHOIS:{t}",rows,style="yellow"))
    except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t42_binary():
    section("💾 TEXT ↔ BINARY","blue"); console.print("[1] Text→Binary  [2] Binary→Text")
    c=Prompt.ask("Select",choices=["1","2"]); text=Prompt.ask("Input")
    if c=="1": console.print(f"\n[green]{' '.join(format(ord(ch),'08b') for ch in text)}[/green]")
    else:
        try: console.print(f"\n[green]{''.join(chr(int(b,2)) for b in text.split())}[/green]")
        except Exception as e: console.print(f"[red]{e}[/red]")
    pause()

def t43_hexdump():
    section("🔍 HEX DUMP","bright_white"); console.print("[1] Text→Hex  [2] File dump")
    c=Prompt.ask("Select",choices=["1","2"])
    if c=="1":
        text=Prompt.ask("Text"); console.print(f"\n[green]{' '.join(format(ord(ch),'02X') for ch in text)}[/green]")
    else:
        p=Prompt.ask("File path").strip()
        if not os.path.isfile(p): console.print("[red]Not found.[/red]"); pause(); return
        with open(p,"rb") as f: data=f.read(512)
        for i in range(0,len(data),16):
            chunk=data[i:i+16]
            console.print(f"[dim]{i:04X}[/dim]  {' '.join(f'{b:02X}' for b in chunk):<48}  [cyan]{''.join(chr(b) if 32<=b<127 else '.' for b in chunk)}[/cyan]")
    pause()

def t44_colorconv():
    section("🎨 COLOR CONVERTER","bright_magenta"); console.print("[1] HEX→RGB  [2] RGB→HEX")
    c=Prompt.ask("Select",choices=["1","2"])
    if c=="1":
        h=Prompt.ask("HEX").strip("#")
        try:
            r,g,b=int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
            console.print(f"\n[bold]RGB: ({r},{g},{b})[/bold]")
            print(f"\033[48;2;{r};{g};{b}m          \033[0m  preview")
        except Exception as e: console.print(f"[red]{e}[/red]")
    else:
        r=int(Prompt.ask("R")); g=int(Prompt.ask("G")); b=int(Prompt.ask("B"))
        console.print(f"\n[bold]HEX: #{r:02X}{g:02X}{b:02X}[/bold]")
        print(f"\033[48;2;{r};{g};{b}m          \033[0m  preview")
    pause()

def t45_random_data():
    import uuid,string; section("🎲 RANDOM DATA","bright_green")
    console.print(make_table("RANDOM",[
        ("UUID v4",str(uuid.uuid4())),("UUID v1",str(uuid.uuid1())),
        ("Random int",str(random.randint(1,1000000))),
        ("Random float",str(round(random.uniform(0,100),6))),
        ("Random hex","".join(random.choices("0123456789abcdef",k=32))),
        ("Random str","".join(random.choices(string.ascii_letters,k=16))),
        ("PIN (6 digits)","".join(random.choices(string.digits,k=6))),
        ("Coin flip",random.choice(["HEADS 🪙","TAILS 🪙"])),
        ("Dice d6",str(random.randint(1,6))),("Dice d20",str(random.randint(1,20))),
    ],style="bright_green")); pause()

def t46_network():
    section("🌐 NETWORK INFO","cyan"); rows=[]
    try: rows.append(("Hostname",socket.gethostname()))
    except: pass
    try: rows.append(("Local IP",socket.gethostbyname(socket.gethostname())))
    except: pass
    try:
        r=http_get("https://api.ipify.org",timeout=5)
        if r: rows.append(("Public IP",r.text.strip()))
    except: pass
    console.print(make_table("NETWORK",rows)); pause()

def t47_hash():
    section("🔑 HASH TOOLS","blue"); console.print("[1] Hash text  [2] Hash file  [3] Compare  [4] Identify")
    c=Prompt.ask("Select",choices=["1","2","3","4"])
    ALGOS={"MD5":hashlib.md5,"SHA1":hashlib.sha1,"SHA256":hashlib.sha256,"SHA512":hashlib.sha512,"SHA3-256":hashlib.sha3_256,"BLAKE2b":hashlib.blake2b}
    if c=="1":
        text=Prompt.ask("Text"); rows=[(a,fn(text.encode()).hexdigest()) for a,fn in ALGOS.items()]
        console.print(make_table("HASHES",rows,headers=("ALGO","HASH"),style="blue"))
    elif c=="2":
        p=Prompt.ask("File path").strip()
        if not os.path.isfile(p): console.print("[red]Not found.[/red]"); pause(); return
        hashes={a:fn() for a,fn in ALGOS.items()}
        with open(p,"rb") as f:
            for chunk in iter(lambda:f.read(65536),b""):
                for h in hashes.values(): h.update(chunk)
        rows=[(a,h.hexdigest()) for a,h in hashes.items()]
        console.print(make_table(f"FILE:{os.path.basename(p)}",rows,headers=("ALGO","HASH"),style="blue"))
    elif c=="3":
        h1=Prompt.ask("Hash 1").strip().lower(); h2=Prompt.ask("Hash 2").strip().lower()
        console.print("[green]✅ MATCH[/green]" if h1==h2 else "[red]❌ MISMATCH[/red]")
    elif c=="4":
        h=Prompt.ask("Hash").strip()
        LENS={32:"MD5",40:"SHA-1",64:"SHA-256",128:"SHA-512"}
        console.print(f"[bold]{LENS.get(len(h),'Unknown')}[/bold] (len={len(h)})")
    pause()

def t48_sysinfo():
    section("💻 SYSTEM INFO","white")
    rows=[("OS",platform.system()),("Release",platform.release()),("Arch",platform.machine()),
          ("Hostname",platform.node()),("Python",sys.version.split()[0]),("CPU cores",str(os.cpu_count()))]
    try: rows.append(("Local IP",socket.gethostbyname(socket.gethostname())))
    except: pass
    try:
        r=http_get("https://api.ipify.org",timeout=4)
        if r: rows.append(("Public IP",r.text.strip()))
    except: pass
    try:
        rows.append(("Disk",f"{shutil.disk_usage('/').total//1073741824}GB total / {shutil.disk_usage('/').free//1073741824}GB free"))
    except: pass
    console.print(make_table("SYSTEM",rows)); pause()

def t49_speedtest():
    section("⚡ SPEED TEST","yellow"); console.print("[yellow]Testing… (20-30s)[/yellow]")
    try:
        import speedtest; st=speedtest.Speedtest()
        with console.status("Best server…"): st.get_best_server()
        with console.status("Download…"): dl=st.download()/1e6
        with console.status("Upload…"): ul=st.upload()/1e6
        rows=[("Download",f"{dl:.2f} Mbps"),("Upload",f"{ul:.2f} Mbps"),
              ("Ping",f"{st.results.ping:.1f} ms"),("ISP",st.results.client.get("isp","?"))]
        console.print(make_table("SPEED",rows,style="yellow"))
    except Exception as e: console.print(f"[red]speedtest-cli needed: pip install speedtest-cli --break-system-packages[/red]")
    pause()

def t50_about():
    section("ℹ️ ABOUT","bright_cyan")
    console.print(f"[bold cyan]{pyfiglet.figlet_format('KIZUNA X',font='slant')}[/bold cyan]")
    console.print(make_table("ABOUT",[
        ("Version","4.0"),("Author","mohmmadsedeg30-design"),
        ("GitHub","https://github.com/mohmmadsedeg30-design/Information-gathering-Kizuna"),
        ("License","MIT"),("Total Tools","50"),
        ("Categories","OSINT · Media · Fun · Utilities"),
        ("Built with","Python · Rich · Pillow · pyfiglet · opencv"),
    ],style="bright_cyan")); pause()

# ════════════════════════════════════════════════════════════
#  MENU
# ════════════════════════════════════════════════════════════
CATS=[
    ("🔍 OSINT",[("1","📱 Phone OSINT",t01_phone),("2","📧 Email OSINT",t02_email),
        ("3","🔍 IP OSINT",t03_ip),("4","🌐 Domain OSINT",t04_domain),
        ("5","📡 DNS Deep",t05_dns),("6","🔭 Subdomains",t06_subdomains),
        ("7","🔒 SSL Info",t07_ssl),("8","🌍 My IP",t08_myip),
        ("9","🔗 URL Expander",t09_url_expand),("10","🌐 HTTP Headers",t10_http_headers)]),
    ("🖼️ MEDIA",[("11","🖼️ ASCII B&W",t11_img_ascii_bw),("12","🎨 ASCII Color",t12_img_ascii_color),
        ("13","🟦 Block Art",t13_img_blocks),("14","🎬 Video→ASCII Color",t14_video_ascii_color),
        ("15","🎬 Video→ASCII B&W",t15_video_ascii_bw),("16","ℹ️ Image Info",t16_img_info),
        ("17","📐 Resize",t17_img_resize),("18","⬛ Grayscale",t18_img_gray),
        ("19","🔄 Negative",t19_img_negative),("20","📲 QR Code",t20_qr)]),
    ("🎨 FUN",[("21","✍️ ASCII Text",t21_ascii_text),("22","🌈 Rainbow",t22_rainbow),
        ("23","💚 Matrix Rain",t23_matrix),("24","⌨️ Hacker Typer",t24_hacker_typer),
        ("25","⏳ Spinners",t25_spinners),("26","🎨 Color Palette",t26_colors),
        ("27","🕐 ASCII Clock",t27_clock),("28","⏱️ Countdown",t28_countdown),
        ("29","🔐 Password Gen",t29_passgen),("30","😂 Joke",t30_joke)]),
    ("🛠️ UTILITIES",[("31","💬 Random Quote",t31_quote),("32","🔤 Base64",t32_base64),
        ("33","🔡 Text Encoder",t33_encoder),("34","📏 Unit Conv",t34_units),
        ("35","🔢 Base Conv",t35_base_conv),("36","📊 Text Stats",t36_text_stats),
        ("37","🔗 URL Encode",t37_url_enc),("38","📶 Ping",t38_ping),
        ("39","🗺️ Traceroute",t39_traceroute),("40","📡 DNS Quick",t40_dns_quick)]),
    ("🔬 MORE",[("41","🌐 Whois",t41_whois),("42","💾 Text↔Binary",t42_binary),
        ("43","🔍 Hex Dump",t43_hexdump),("44","🎨 Color Conv",t44_colorconv),
        ("45","🎲 Random Data",t45_random_data),("46","🌐 Network",t46_network),
        ("47","🔑 Hash Tools",t47_hash),("48","💻 System Info",t48_sysinfo),
        ("49","⚡ Speed Test",t49_speedtest),("50","ℹ️ About",t50_about)]),
]
ALL={k:fn for _,tools in CATS for k,_,fn in tools}

def print_menu():
    clear(); console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print(f"  [bold]KIZUNA X[/bold]  [dim]v4.0 · 50 Tools · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")
    for cat_name,tools in CATS:
        console.print(f"  [bold white]── {cat_name} ──[/bold white]")
        half=(len(tools)+1)//2
        for i in range(half):
            l=tools[i]; r=tools[i+half] if i+half<len(tools) else None
            lstr=f"  [cyan][{l[0]:>2}][/cyan] {l[1]:<28}"
            rstr=f"[cyan][{r[0]:>2}][/cyan] {r[1]}" if r else ""
            console.print(lstr+rstr)
        console.print()
    console.print("  [dim red][ 0][/dim red] 🚪 Exit\n")

def main():
    console.print(Panel(f"[bold cyan]{BANNER}[/bold cyan]",title="[bold]KIZUNA X[/bold]",
        subtitle="[dim]50 Tools · OSINT · Media · Fun · Utilities[/dim]",border_style="cyan"))
    while True:
        print_menu(); choice=Prompt.ask("[bold]Tool number[/bold]")
        if choice=="0": console.print("\n[red]Goodbye.[/red]\n"); sys.exit(0)
        fn=ALL.get(choice)
        if fn: fn()
        else: console.print("[red]Invalid.[/red]"); time.sleep(0.5)

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt: console.print("\n\n[red]Interrupted.[/red]\n"); sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]FATAL:[/bold red] {e}")
        logging.critical(e,exc_info=True); sys.exit(1)
