# -*- coding: utf-8 -*-
"""CORE OPTI — dashboard + More toggles + embedded tweaks (no external .reg needed)"""
import os, sys, math, time, ctypes, random, threading, subprocess, webbrowser, json, queue
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path

def is_admin():
    try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception: return False

def run_as_admin():
    if sys.platform != "win32": return
    params = " ".join(['"%s"' % a for a in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)

def app_dir():
    if getattr(sys, "frozen", False): return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def tweaks_dir(): return app_dir() / "tweaks"
def ram_dir(): return app_dir() / "RAM"
def backup_dir(): return app_dir() / "backups"
def config_path(): return app_dir() / "core_opti_config.json"
DISCORD_URL = "https://discord.gg/shfExpqfqm"

def load_config():
    p = config_path()
    defaults = {
        "more_state": {},
        "geometry": "1060x700+80+40",
        "theme": "Neon Green",
        "last_profile": "",
        "reboot_needed": False,
    }
    try:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                defaults.update(data)
    except Exception:
        pass
    return defaults

def save_config(cfg):
    try:
        config_path().write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def detect_windows_theme():
    """Return 'AMOLED' if system prefers dark, else 'Ice'."""
    try:
        raw = subprocess.run(
            ["reg", "query", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "/v", "AppsUseLightTheme"],
            capture_output=True, text=True, timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0,
        )
        if "0x0" in (raw.stdout or ""):
            return "AMOLED"
        return "Ice"
    except Exception:
        return "Neon Green"

def free_space_gb(letter="C"):
    try:
        import psutil
        u = psutil.disk_usage(letter + ":\\")
        return u.free / (1024 ** 3)
    except Exception:
        try:
            raw = _ps("$d=Get-PSDrive %s; [math]::Round($d.Free/1GB,2)" % letter)
            return float(raw.splitlines()[0]) if raw else 0.0
        except Exception:
            return 0.0

THEMES = {
    "Cyber": dict(BG="#080b12", SIDE="#0d111a", CARD="#121824", CARD2="#182131", NEON="#7c4dff", NEON_DIM="#3b286d", NEON_SOFT="#211a3b", TEXT="#f1edff", MUTED="#8d91a6", BORDER="#30294a"),
    "Ice": dict(BG="#071017", SIDE="#0b1720", CARD="#10212c", CARD2="#15303d", NEON="#63d8ff", NEON_DIM="#24516a", NEON_SOFT="#12313d", TEXT="#e9fbff", MUTED="#86a4af", BORDER="#24404c"),
    "Emerald": dict(BG="#07110d", SIDE="#0c1812", CARD="#11221a", CARD2="#172d22", NEON="#43f58a", NEON_DIM="#205d3a", NEON_SOFT="#123422", TEXT="#edfff4", MUTED="#82a693", BORDER="#28523b"),
    "AMOLED": dict(BG="#000000", SIDE="#020202", CARD="#070707", CARD2="#0d0d0d", NEON="#ffffff", NEON_DIM="#4d4d4d", NEON_SOFT="#171717", TEXT="#ffffff", MUTED="#8a8a8a", BORDER="#242424"),
    "RGB": dict(BG="#08090d", SIDE="#0c0e14", CARD="#12151d", CARD2="#171b25", NEON="#00f5ff", NEON_DIM="#173c55", NEON_SOFT="#10252d", TEXT="#edf7ff", MUTED="#7e8b9e", BORDER="#26303c"),
    "Neon Green": dict(BG="#0b0d10", SIDE="#0e1116", CARD="#141820", CARD2="#181c26", NEON="#3dff8a", NEON_DIM="#1a4d32", NEON_SOFT="#0d281c", TEXT="#e8eef5", MUTED="#7a8699", BORDER="#1e2430"),
    "Cyber Cyan": dict(BG="#0a0e12", SIDE="#0c1218", CARD="#121a22", CARD2="#162028", NEON="#00e5ff", NEON_DIM="#0a4a55", NEON_SOFT="#0a2228", TEXT="#e0f7fa", MUTED="#6a8a94", BORDER="#1a2a32"),
    "Violet": dict(BG="#0c0b10", SIDE="#12101a", CARD="#1a1624", CARD2="#201c2c", NEON="#b388ff", NEON_DIM="#3d2a66", NEON_SOFT="#1a1028", TEXT="#f0e8ff", MUTED="#8a7a9a", BORDER="#2a2438"),
    "Amber": dict(BG="#100e0a", SIDE="#16120c", CARD="#1e1810", CARD2="#241e14", NEON="#ffc107", NEON_DIM="#5c4500", NEON_SOFT="#2a1e08", TEXT="#fff8e1", MUTED="#9a8a6a", BORDER="#322818"),
}
class Theme:
    def __init__(self, n="Neon Green"): self.apply(n)
    def apply(self, n):
        for k,v in THEMES.get(n, THEMES["Neon Green"]).items(): setattr(self,k,v)
        self.name = n
TH = Theme()

def rr(c,x1,y1,x2,y2,r=12,**kw):
    pts=[x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1]
    return c.create_polygon(pts, smooth=True, **kw)

def _hide():
    kw={}
    if sys.platform=="win32":
        try: kw["creationflags"]=subprocess.CREATE_NO_WINDOW
        except Exception: pass
    return kw

def _ps(cmd):
    try:
        r=subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-WindowStyle","Hidden","-Command",cmd],
            capture_output=True,text=True,encoding="utf-8",errors="ignore",timeout=60,**_hide())
        return (r.stdout or "").strip()
    except Exception: return ""

def gather_sysinfo(cb):
    info={k:"—" for k in ("cpu","cores","gpu","vram","ram_total","ram_type","os","os_ver","disk","disk_size")}
    script=r"""
$cpu=Get-CimInstance Win32_Processor -EA SilentlyContinue|Select -First 1
$gpu=Get-CimInstance Win32_VideoController -EA SilentlyContinue|Select -First 1
$cs=Get-CimInstance Win32_ComputerSystem -EA SilentlyContinue
$os=Get-CimInstance Win32_OperatingSystem -EA SilentlyContinue
$disk=Get-CimInstance Win32_DiskDrive -EA SilentlyContinue|Select -First 1
$mem=Get-CimInstance Win32_PhysicalMemory -EA SilentlyContinue|Select -First 1
"CPU=$($cpu.Name)"; "CORES=$($cpu.NumberOfCores)"; "GPU=$($gpu.Name)"; "VRAM=$($gpu.AdapterRAM)"
"RAM=$($cs.TotalPhysicalMemory)"; "RAMTYPE=$($mem.SMBIOSMemoryType)"; "OS=$($os.Caption)"; "OSVER=$($os.Version)"
"DISK=$($disk.Model)"; "DISKSIZE=$($disk.Size)"
"""
    try:
        data={}
        for line in _ps(script).splitlines():
            if "=" in line:
                k,v=line.split("=",1); data[k.strip()]=v.strip()
        info["cpu"]=data.get("CPU") or "CPU"
        info["cores"]=(data.get("CORES") or "?")+" Cores"
        info["gpu"]=data.get("GPU") or "GPU"
        try: info["vram"]="%.0f GB"%(int(data.get("VRAM") or 0)/(1024**3))
        except Exception: pass
        try: info["ram_total"]="%.1f GB"%(int(data.get("RAM") or 0)/(1024**3))
        except Exception: pass
        mt=data.get("RAMTYPE") or ""
        info["ram_type"]="DDR5" if mt=="34" else ("DDR4" if mt=="26" else "RAM")
        info["os"]=data.get("OS") or "Windows"; info["os_ver"]=data.get("OSVER") or "—"
        info["disk"]=data.get("DISK") or "Disk"
        try: info["disk_size"]="%.0f GB"%(int(data.get("DISKSIZE") or 0)/(1024**3))
        except Exception: pass
    except Exception: pass
    cb(info)


_HAS_PSUTIL = None
_HAS_NVIDIA = None
_LAST_LOADS = {"cpu": 0.0, "ram": 0.0, "disk": 0.0, "gpu": 0.0, "t": 0.0}

def sample_loads(force=False):
    """CPU / RAM / Disk / GPU % — быстрый, с кэшем ~0.9 с, без лишних окон."""
    global _HAS_PSUTIL, _HAS_NVIDIA, _LAST_LOADS
    now = time.time()
    if not force and (now - _LAST_LOADS["t"]) < 0.9:
        return dict(_LAST_LOADS)
    out = {"cpu": 0.0, "ram": 0.0, "disk": 0.0, "gpu": 0.0, "t": now}
    if _HAS_PSUTIL is None:
        try:
            import psutil  # noqa: F401
            _HAS_PSUTIL = True
        except Exception:
            _HAS_PSUTIL = False
    if _HAS_PSUTIL:
        try:
            import psutil
            # non-blocking: interval=None использует предыдущий замер
            out["cpu"] = float(psutil.cpu_percent(interval=None))
            out["ram"] = float(psutil.virtual_memory().percent)
            try:
                out["disk"] = float(psutil.disk_usage("C:\\").percent)
            except Exception:
                try:
                    out["disk"] = float(psutil.disk_usage("/").percent)
                except Exception:
                    out["disk"] = 0.0
        except Exception:
            pass
    else:
        try:
            raw = _ps("(Get-CimInstance Win32_Processor).LoadPercentage")
            out["cpu"] = float(raw.splitlines()[0]) if raw else 0.0
        except Exception:
            pass
        try:
            raw = _ps("$o=Get-CimInstance Win32_OperatingSystem; [math]::Round(($o.TotalVisibleMemorySize-$o.FreePhysicalMemory)*100/$o.TotalVisibleMemorySize,1)")
            out["ram"] = float(raw.splitlines()[0]) if raw else 0.0
        except Exception:
            pass
        try:
            raw = _ps("$d=Get-PSDrive C; [math]::Round(($d.Used/($d.Used+$d.Free))*100,1)")
            out["disk"] = float(raw.splitlines()[0]) if raw else 0.0
        except Exception:
            pass
    if _HAS_NVIDIA is not False:
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=1.2, **_hide()
            )
            if r.returncode == 0 and r.stdout.strip():
                out["gpu"] = float(r.stdout.strip().splitlines()[0])
                _HAS_NVIDIA = True
            else:
                _HAS_NVIDIA = False
        except Exception:
            _HAS_NVIDIA = False
    _LAST_LOADS = out
    return dict(out)


# ---- widgets ----
class ToolTip:
    """Лёгкий tooltip без лишних окон."""
    def __init__(self, widget, text, delay=450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _e=None):
        self._hide()
        self._id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
            self._tip = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry("+%d+%d" % (x, y))
            try:
                tw.attributes("-topmost", True)
            except Exception:
                pass
            lbl = tk.Label(
                tw, text=self.text, justify="left",
                background=TH.CARD2, foreground=TH.TEXT,
                relief="solid", borderwidth=1,
                font=("Segoe UI", 8), padx=8, pady=4,
            )
            lbl.pack()
        except Exception:
            self._tip = None

    def _hide(self, _e=None):
        if self._id:
            try:
                self.widget.after_cancel(self._id)
            except Exception:
                pass
            self._id = None
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


class NeonBtn(tk.Canvas):
    def __init__(self, m, text, command, w=140, h=34, tip=None, **kw):
        super().__init__(m, width=w, height=h, bg=m.cget("bg"), highlightthickness=0, bd=0, **kw)
        self.cmd, self.txt, self.W, self.H = command, text, w, h
        self.hov = False
        self._draw()
        self.bind("<Button-1>", lambda e: command and command())
        self.bind("<Enter>", lambda e: self._h(True))
        self.bind("<Leave>", lambda e: self._h(False))
        if tip:
            ToolTip(self, tip)

    def _h(self, v):
        self.hov = v
        self._draw()

    def _draw(self):
        self.delete("all")
        rr(
            self, 1, 1, self.W - 1, self.H - 1, r=10,
            fill=TH.NEON_SOFT if self.hov else TH.CARD,
            outline=TH.NEON if self.hov else TH.NEON_DIM, width=1,
        )
        self.create_text(self.W // 2, self.H // 2, text=self.txt, fill=TH.NEON, font=("Segoe UI Semibold", 10))

    def refresh(self):
        self.configure(bg=self.master.cget("bg"))
        self._draw()

class SideItem(tk.Canvas):
    def __init__(self,m,text,command,w=184,h=34):
        super().__init__(m,width=w,height=h,bg=TH.SIDE,highlightthickness=0,bd=0)
        self.cmd,self.txt,self.W,self.H=command,text,w,h; self.active=self.hov=False; self._draw()
        self.bind("<Button-1>",lambda e: command and command())
        self.bind("<Enter>",lambda e: self._s(hov=True)); self.bind("<Leave>",lambda e: self._s(hov=False))
    def _s(self,hov=None,active=None):
        if hov is not None: self.hov=hov
        if active is not None: self.active=active
        self._draw()
    def set_active(self,a): self._s(active=a)
    def _draw(self):
        self.delete("all"); on=self.active or self.hov
        rr(self,3,2,self.W-3,self.H-2,r=10,fill=TH.NEON_SOFT if on else TH.SIDE,outline=TH.NEON if on else TH.SIDE,width=1)
        self.create_text(14,self.H//2,text=self.txt,anchor="w",fill=TH.NEON if on else TH.MUTED,font=("Segoe UI Semibold",10))
    def refresh(self): self.configure(bg=TH.SIDE); self._draw()

class InfoCard(tk.Canvas):
    def __init__(self,m,title,sub,lines,w=248,h=118):
        super().__init__(m,width=w,height=h,bg=m.cget("bg"),highlightthickness=0,bd=0)
        self.W,self.H,self.title,self.sub,self.lines=w,h,title,sub,lines; self.hov=False; self._draw()
        self.bind("<Enter>",lambda e: self._h(True)); self.bind("<Leave>",lambda e: self._h(False))
    def _h(self,v): self.hov=v; self._draw()
    def _draw(self):
        self.delete("all")
        rr(self,1,1,self.W-1,self.H-1,r=14,fill=TH.CARD2 if self.hov else TH.CARD,outline=TH.NEON if self.hov else TH.BORDER,width=1)
        self.create_text(16,16,text=self.title,anchor="w",fill=TH.NEON,font=("Segoe UI Semibold",11))
        self.create_text(16,34,text=self.sub,anchor="w",fill=TH.MUTED,font=("Segoe UI",8))
        y=52
        for k,v in self.lines:
            self.create_text(16,y,text=k,anchor="w",fill=TH.MUTED,font=("Segoe UI",8))
            self.create_text(16,y+12,text=str(v)[:40],anchor="w",fill=TH.TEXT,font=("Segoe UI Semibold",9)); y+=28



class LoadGauge(tk.Canvas):
    """Ровный кружок нагрузки (oval + arc, без ломаных линий)."""
    def __init__(self, master, title="CPU", size=120):
        super().__init__(master, width=size, height=size + 22, bg=master.cget("bg"), highlightthickness=0, bd=0)
        self.size = size
        self.title = title
        self.value = 0.0
        self._paint()
    def set(self, pct):
        self.value = max(0.0, min(100.0, float(pct)))
        self._paint()
    def _paint(self):
        self.delete("all")
        s = self.size
        pad = 10
        x1, y1, x2, y2 = pad, pad, s - pad, s - pad
        self.create_oval(x1, y1, x2, y2, outline=TH.NEON_DIM, width=8)
        if self.value >= 0.5:
            self.create_arc(x1, y1, x2, y2, start=90, extent=-3.6 * self.value,
                            style=tk.ARC, outline=TH.NEON, width=8)
        self.create_text(s/2, s/2 - 4, text="%d%%" % int(round(self.value)),
                         fill=TH.NEON, font=("Segoe UI", 14, "bold"))
        self.create_text(s/2, s + 6, text=self.title, fill=TH.MUTED, font=("Segoe UI", 9))


class SmoothRing(tk.Canvas):
    """Гладкий круг прогресса с плавной анимацией."""
    def __init__(self,m,size=200):
        super().__init__(m,width=size,height=size,bg=m.cget("bg"),highlightthickness=0,bd=0); self.size=size; self.display=0.; self.target=0.; self.status="Ready"; self._aid=None; self._paint()
    def set(self,pct,status=None):
        self.target=max(0.,min(100.,float(pct)))
        if status is not None:self.status=str(status)
        if self._aid is None:self._tick()
    def _tick(self):
        d=self.target-self.display
        if abs(d)<.18:self.display=self.target; self._aid=None; self._paint(); return
        self.display+=d*.22; self._paint(); self._aid=self.after(16,self._tick)
    def _paint(self):
        self.delete("all"); s=self.size; pad=15; x1,y1,x2,y2=pad,pad,s-pad,s-pad
        self.create_oval(x1,y1,x2,y2,outline=TH.NEON_DIM,width=12)
        if self.display>=.05:self.create_arc(x1,y1,x2,y2,start=90,extent=-3.6*self.display,style=tk.ARC,outline=TH.NEON,width=12)
        self.create_text(s/2,s/2-10,text="%d%%"%int(round(self.display)),fill=TH.NEON,font=("Segoe UI",25,"bold"))
        st=self.status[:24]+("…" if len(self.status)>24 else "")
        self.create_text(s/2,s/2+20,text=st,fill=TH.MUTED,font=("Segoe UI",8))

class ToggleCard(tk.Canvas):
    """Закруглённая карточка + аккуратный switch."""
    def __init__(self, master, title, desc, key, state, on_toggle, w=470, h=64, tip=None):
        super().__init__(master, width=w, height=h, bg=master.cget("bg"), highlightthickness=0, bd=0)
        self.key = key
        self.state = bool(state)
        self.on_toggle = on_toggle
        self.title = title
        self.desc = desc
        self.W = w
        self.H = h
        self.bind("<Button-1>", lambda e: self._click())
        self._paint()
        if tip:
            ToolTip(self, tip)

    def _click(self):
        self.state = not self.state
        self._paint()
        self.on_toggle(self.key, self.state)

    def set_state(self, on, notify=True):
        self.state = bool(on)
        self._paint()
        if notify:
            self.on_toggle(self.key, self.state)

    def _paint(self):
        self.delete("all")
        out = TH.NEON if self.state else TH.BORDER
        fill = TH.NEON_SOFT if self.state else TH.CARD
        rr(self, 1, 1, self.W - 1, self.H - 1, r=16, fill=fill, outline=out, width=1)
        self.create_text(16, 20, text=self.title, anchor="w", fill=TH.NEON, font=("Segoe UI Semibold", 10))
        self.create_text(16, 40, text=self.desc, anchor="w", fill=TH.MUTED, font=("Segoe UI", 8), width=self.W - 90)
        sx, sy = self.W - 58, 18
        tw, th = 44, 24
        track = TH.NEON if self.state else TH.NEON_DIM
        self.create_oval(sx, sy, sx + th, sy + th, fill=track, outline="")
        self.create_oval(sx + tw - th, sy, sx + tw, sy + th, fill=track, outline="")
        self.create_rectangle(sx + th // 2, sy, sx + tw - th // 2, sy + th, fill=track, outline="")
        kx = sx + tw - th + 2 if self.state else sx + 2
        self.create_oval(kx, sy + 2, kx + th - 4, sy + th - 2, fill="#f5fff8", outline="")

class LiveBG(tk.Canvas):
    """Лёгкий анимированный фон: мягкие glow-пятна + частицы. Пауза, когда окно не активно."""
    def __init__(self, m):
        super().__init__(m, highlightthickness=0, bd=0, bg=TH.BG)
        self.run = True
        self.paused = False
        self.ps = []
        self._frame = 0
        self.after(80, self._init)
        self.after(40, self._tick)
        try:
            m.bind("<FocusIn>", lambda e: self._set_pause(False), add="+")
            m.bind("<FocusOut>", lambda e: self._set_pause(True), add="+")
        except Exception:
            pass

    def _set_pause(self, v):
        self.paused = bool(v)

    @staticmethod
    def _hsv(h, s=.72, v=1.0):
        import colorsys
        r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, s, v)
        return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

    def _init(self):
        w = max(self.winfo_width(), 300)
        h = max(self.winfo_height(), 300)
        # меньше частиц = меньше нагрузка на CPU
        n = 8 if getattr(TH, "name", "") == "RGB" else 6
        self.ps = [
            {
                "x": random.random() * w,
                "y": random.random() * h,
                "r": random.uniform(1.0, 2.0),
                "vx": random.uniform(-0.10, 0.10),
                "vy": random.uniform(-0.08, 0.08),
            }
            for _ in range(n)
        ]

    def _tick(self):
        if not self.run:
            return
        if self.paused:
            self.after(120, self._tick)
            return
        try:
            self.delete("p")
            w = max(self.winfo_width(), 100)
            h = max(self.winfo_height(), 100)
            t = time.time()
            self._frame += 1
            if getattr(TH, "name", "") == "RGB":
                for i, (bx, by) in enumerate(((.25, .32), (.75, .58), (.48, .82))):
                    c = self._hsv(t * 6 + i * 120, .60, .38)
                    x = bx * w + math.sin(t * 0.10 + i) * 28
                    y = by * h + math.cos(t * 0.09 + i) * 20
                    self.create_oval(x - 90, y - 90, x + 90, y + 90, fill=c, outline="", tags="p")
                pc = self._hsv(t * 6 + 140, .68, .50)
            else:
                for i, (bx, by) in enumerate(((.28, .38), (.72, .62))):
                    x = bx * w + math.sin(t * 0.15 + i) * 16
                    y = by * h + math.cos(t * 0.14 + i) * 12
                    self.create_oval(x - 36, y - 36, x + 36, y + 36, fill=TH.NEON_SOFT, outline="", tags="p")
                pc = TH.NEON_DIM
            for q in self.ps:
                q["x"] += q["vx"]
                q["y"] += q["vy"]
                if q["x"] < 0 or q["x"] > w:
                    q["vx"] *= -1
                if q["y"] < 0 or q["y"] > h:
                    q["vy"] *= -1
                self.create_oval(
                    q["x"] - q["r"], q["y"] - q["r"],
                    q["x"] + q["r"], q["y"] + q["r"],
                    fill=pc, outline="", tags="p"
                )
        except tk.TclError:
            return
        # ~25 FPS достаточно для фона, меньше нагрузки
        self.after(40, self._tick)

    def stop(self):
        self.run = False

    def refresh_bg(self):
        self.configure(bg=TH.BG)
        self._init()

class E:
    SERVICES=(
        "SysMain","WSearch","DiagTrack","dmwappushservice","diagnosticshub.standardcollector.service",
        "DsSvc","WerSvc","wercplsupport","XblAuthManager","XblGameSave","XboxNetApiSvc","XboxGipSvc",
        "GamingServices","GamingServicesNet","Spooler","Fax","PrintNotify","RemoteRegistry","RemoteAccess",
        "TermService","SessionEnv","UmRdpService","RpcLocator","WbioSrvc","TabletInputService","MapsBroker",
        "lfsvc","SCardSvr","ScDeviceEnum","SCPolicySvc","TapiSrv","PhoneSvc","SmsRouter","RetailDemo",
        "fdPHost","FDResPub","wisvc","DoSvc","WMPNetworkSvc","seclogon","CscService",
        "MixedRealityOpenXRSvc","spectrum","perceptionsimulation","icssvc","WalletService","WpnService",
        "PushToInstall","MessagingService","PcaSvc","stisvc","GraphicsPerfSvc","FontCache","edgeupdate","edgeupdatem",
        "MicrosoftEdgeElevationService","BDESVC","HvHost","ssh-agent",
        "AJRouter","CDPSvc","CDPUserSvc","OneSyncSvc","WorkFoldersSvc",
        "WiaRpc","DeviceAssociationService","DispBrokerDesktopSvc","NPSMSvc",
    )
    TASKS=(
        r"Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
        r"Microsoft\Windows\Application Experience\ProgramDataUpdater",
        r"Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
        r"Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
        r"Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector",
        r"Microsoft\Windows\Feedback\Siuf\DmClient",
        r"Microsoft\Windows\Maps\MapsUpdateTask",
        r"Microsoft\Windows\Windows Error Reporting\QueueReporting",
        r"Microsoft\Windows\Defrag\ScheduledDefrag",
    )
    @staticmethod
    def run(cmd, cwd=None):
        try:
            kw=dict(shell=True,capture_output=True,text=True,encoding="utf-8",errors="ignore",timeout=40,cwd=cwd)
            kw.update(_hide()); subprocess.run(cmd,**kw); return True
        except Exception: return False
    @staticmethod
    def reg(path, name, value, typ="REG_DWORD"):
        if typ=="REG_DWORD": E.run('reg add "%s" /v %s /t REG_DWORD /d %s /f'%(path,name,value))
        else: E.run('reg add "%s" /v %s /t REG_SZ /d "%s" /f'%(path,name,value))
    @staticmethod
    def sc_off(n):
        E.run('sc stop "%s"' % n)
        E.run('sc config "%s" start= disabled' % n)
        # дубль через реестр — надёжнее на части сборок
        E.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\%s" /v Start /t REG_DWORD /d 4 /f' % n)

    @staticmethod
    def sc_on(n, mode="demand"):
        start_map = {"boot": 0, "system": 1, "auto": 2, "demand": 3, "disabled": 4}
        d = start_map.get(mode, 3)
        E.run('sc config "%s" start= %s' % (n, mode))
        E.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\%s" /v Start /t REG_DWORD /d %d /f' % (n, d))
        E.run('sc start "%s"' % n)


    @classmethod
    def cleanup(cls, log, prog):
        steps=[(10,"TEMP",r'del /f /s /q "%TEMP%\*"'),(22,"WinTemp",r'del /f /s /q "C:\Windows\Temp\*"'),
               (34,"Prefetch",r'del /f /s /q "C:\Windows\Prefetch\*"'),(46,"DNS","ipconfig /flushdns"),
               (58,"Thumbs",r'del /f /s /q "%LocalAppData%\Microsoft\Windows\Explorer\thumbcache_*.db"'),
               (70,"DX",r'del /f /s /q "%LocalAppData%\D3DSCache\*"'),
               (82,"FontCache",r'del /f /s /q "%WinDir%\ServiceProfiles\LocalService\AppData\Local\FontCache\*"'),
               (92,"UpdateCache",'net stop wuauserv & net stop bits & rd /s /q "C:\\Windows\\SoftwareDistribution\\Download" & mkdir "C:\\Windows\\SoftwareDistribution\\Download"'),
               (100,"Done",None)]
        for p,n,c in steps:
            prog(p,n); log(n)
            if c: cls.run(c)
            time.sleep(0.03)
        return True

    @classmethod
    def game_tweaks(cls, log, prog):
        acts=[
            ("GameDVR", lambda:(cls.reg(r"HKCU\System\GameConfigStore","GameDVR_Enabled",0),
                cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR","AppCaptureEnabled",0),
                cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR","AllowGameDVR",0))),
            ("FSE", lambda:(cls.reg(r"HKCU\System\GameConfigStore","GameDVR_FSEBehaviorMode",2),
                cls.reg(r"HKCU\System\GameConfigStore","GameDVR_FSEBehavior",2),
                cls.reg(r"HKCU\System\GameConfigStore","GameDVR_HonorUserFSEBehaviorMode",1),
                cls.reg(r"HKCU\System\GameConfigStore","GameDVR_DXGIHonorFSEWindowsCompatible",1))),
            ("MMCSS", lambda:(cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile","NetworkThrottlingIndex",0xFFFFFFFF),
                cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile","SystemResponsiveness",0),
                cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games","GPU Priority",8),
                cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games","Priority",6))),
            ("Prefetch", lambda:(cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters","EnablePrefetcher",0),
                cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters","EnableSuperfetch",0))),
            ("Telemetry", lambda:(cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection","AllowTelemetry",0),
                cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection","AllowTelemetry",0))),
            ("Visual", lambda:(cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects","VisualFXSetting",2),
                cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize","EnableTransparency",0),
                cls.reg(r"HKCU\Control Panel\Desktop","MenuShowDelay","0","REG_SZ"),
                cls.reg(r"HKCU\Control Panel\Desktop\WindowMetrics","MinAnimate","0","REG_SZ"))),
            ("Background", lambda: cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications","GlobalUserDisabled",1)),
            ("GPU/Priority", lambda:(cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers","HwSchMode",2),
                cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl","Win32PrioritySeparation",26))),
            ("Response", lambda:(cls.reg(r"HKCU\Control Panel\Desktop","AutoEndTasks","1","REG_SZ"),
                cls.reg(r"HKCU\Control Panel\Desktop","HungAppTimeout","1000","REG_SZ"),
                cls.reg(r"HKCU\Control Panel\Desktop","WaitToKillAppTimeout","2000","REG_SZ"))),
            ("Mouse", lambda:(cls.reg(r"HKCU\Control Panel\Mouse","MouseSpeed","0","REG_SZ"),
                cls.reg(r"HKCU\Control Panel\Mouse","MouseThreshold1","0","REG_SZ"),
                cls.reg(r"HKCU\Control Panel\Mouse","MouseThreshold2","0","REG_SZ"))),
            ("Widgets", lambda:(cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced","TaskbarDa",0),
                cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Dsh","AllowNewsAndInterests",0))),
            ("NTFS", lambda:(cls.run("fsutil behavior set disablelastaccess 1"), cls.run("fsutil behavior set disable8dot3 1"))),
            ("Network", lambda:(
                cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile","NetworkThrottlingIndex",0xFFFFFFFF),
                cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters","DefaultTTL",64),
            )),
            ("Cortana", lambda:(
                cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search","AllowCortana",0),
                cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Search","BingSearchEnabled",0),
            )),
            ("Tips", lambda:(
                cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager","SoftLandingEnabled",0),
                cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager","SubscribedContent-338389Enabled",0),
            )),
            ("Notifications", lambda:(
                cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\PushNotifications","ToastEnabled",0),
            )),
            ("Timer", lambda:(
                cls.run("bcdedit /set useplatformclock false"),
                cls.run("bcdedit /set disabledynamictick yes"),
                cls.run("bcdedit /set useplatformtick yes"),
            )),
            ("Store auto", lambda: cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\WindowsStore","AutoDownload",2)),
            ("Power throttle", lambda: cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling","PowerThrottlingOff",1)),
            ("Hiberboot", lambda: cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power","HiberbootEnabled",0)),
            ("Game Mode", lambda:(
                cls.reg(r"HKCU\Software\Microsoft\GameBar","AutoGameModeEnabled",1),
                cls.reg(r"HKCU\Software\Microsoft\GameBar","AllowAutoGameMode",1),
            )),
            ("Delivery Opt", lambda: cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config","DODownloadMode",0)),

        ]
        for i,(n,fn) in enumerate(acts):
            prog(int((i+1)/len(acts)*100), n); log(n)
            try: fn()
            except Exception: pass
            time.sleep(0.02)
        prog(100,"Done"); return True

    @classmethod
    def kill_services(cls, log, prog):
        svcs = list(cls.SERVICES)
        extra = (
            "DiagTrack","dmwappushservice","WSearch","SysMain",
            "XblAuthManager","XblGameSave","XboxNetApiSvc","XboxGipSvc",
            "GamingServices","GamingServicesNet","Spooler","Fax","PrintNotify",
            "WbioSrvc","TabletInputService","MapsBroker","lfsvc","PhoneSvc",
            "RetailDemo","WerSvc","PcaSvc","DoSvc","WMPNetworkSvc","MessagingService",
            "WalletService","icssvc","PushToInstall","wisvc","CscService","stisvc",
            "GraphicsPerfSvc","FontCache","edgeupdate","edgeupdatem",
            "MicrosoftEdgeElevationService","TermService","SessionEnv","UmRdpService",
            "RemoteRegistry","RemoteAccess","MixedRealityOpenXRSvc","WorkFoldersSvc",
            "WiaRpc","ssh-agent","AJRouter","OneSyncSvc","CDPSvc","DispBrokerDesktopSvc",
            "NPSMSvc","shpamsvc","AssignedAccessManagerSvc","spectrum","perceptionsimulation",
            "SCardSvr","TapiSrv","fdPHost","FDResPub","WdiServiceHost","WdiSystemHost",
            "DusmSvc","InventorySvc","InstallService","AppReadiness","ClipSVC",
            "","","","DeviceAssociationService",
            "DialogBlockingService","EntAppSvc","FrameServer","MapsBroker",
            "MessagingService","PhoneSvc","PrintNotify","PushToInstall","QWAVE",
            "RasAuto","RasMan","RetailDemo","RmSvc","SCPolicySvc","seclogon",
            "SensorDataService","SensorService","SensrSvc","SharedAccess",
            "SmsRouter","SNMPTRAP","SSDPSRV","swprv","TapiSrv","TabletInputService",
            "UevAgentService","VacSvc","WbioSrvc","WMPNetworkSvc","WpcMonSvc",
            "WPDBusEnum","WwanSvc","XboxGipSvc","XblAuthManager","XblGameSave","XboxNetApiSvc",
        )
        # unique preserve order
        seen=set(); all_svcs=[]
        for s in list(svcs)+list(extra):
            if s not in seen:
                seen.add(s); all_svcs.append(s)
        for i,s in enumerate(all_svcs):
            prog(int((i+1)/len(all_svcs)*100), s[:18]); log(s); cls.sc_off(s)
        prog(100,"Done"); return True


    @classmethod
    def disable_tasks(cls, log, prog):
        for i,t in enumerate(cls.TASKS):
            prog(int((i+1)/len(cls.TASKS)*100), "task"); log(t)
            cls.run('schtasks /Change /TN "%s" /Disable'%t)
        prog(100,"Done"); return True

    @classmethod
    def cpu_boost(cls, log, prog):
        """CPU + GPU + memory performance stack."""
        steps = [
            (8, "High", "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
            (16, "Ultimate", "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61"),
            (22, "Activate", "powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61"),
            (30, "CPU min100", "powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMIN 100"),
            (36, "CPU max100", "powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 100"),
            (42, "Boost mode", "powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PERFBOOSTMODE 2"),
            (48, "Unpark", "powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR CPMINCORES 100"),
            (54, "PCIE", "powercfg /setacvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 0"),
            (60, "Apply power", "powercfg /setactive SCHEME_CURRENT"),
            (66, "Hibernate off", "powercfg /hibernate off"),
        ]
        for p, n, c in steps:
            prog(p, n); log(n); cls.run(c)
        prog(72, "CPU reg")
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling", "PowerThrottlingOff", 1)
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", 38)
        # GPU: max performance hints
        prog(80, "GPU")
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", 2)
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers\Scheduler", "EnablePreemption", 1)
        # AMD ULPS off (harmless if no AMD key)
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000", "EnableUlps", 0)
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000", "EnableUlps_NA", 0)
        # NVIDIA power: prefer max perf via PowerMizer if present
        pass
        # Memory performance (safe-ish)
        prog(90, "RAM")
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", "DisablePagingExecutive", 1)
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", "LargeSystemCache", 0)
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", "SecondLevelDataCache", 1024)
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", "IoPageLockLimit", 983040)
        # disable memory compression (Win10+)
        cls.run('powershell -NoProfile -WindowStyle Hidden -Command "Disable-MMAgent -MemoryCompression -ErrorAction SilentlyContinue"')
        # MMCSS Games
        base = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
        cls.reg(base, "GPU Priority", 8)
        cls.reg(base, "Priority", 6)
        cls.reg(base, "Scheduling Category", "High", "REG_SZ")
        cls.reg(base, "SFIO Priority", "High", "REG_SZ")
        prog(100, "Done")
        return True



    @classmethod
    def create_safety_backup(cls,log=None,prog=None):
        d=app_dir()/"backups";d.mkdir(exist_ok=True);root=d/("backup_"+time.strftime("%Y%m%d_%H%M%S"));root.mkdir(exist_ok=True)
        if prog:prog(20,"Registry")
        cls.run('reg export "HKCU\Software\Microsoft\Windows\CurrentVersion" "%s\hkcu.reg" /y'%root)
        if prog:prog(60,"Services")
        (root/"services.txt").write_text(cls.run_capture('powershell -NoProfile -Command "Get-Service | Select Name,Status,StartType | ConvertTo-Csv -NoTypeInformation"'),encoding="utf-8")
        (d/"LAST").write_text(str(root),encoding="utf-8")
        if prog:prog(100,"Backup ready")
        if log:log(str(root))
        return True
    @classmethod
    def run_capture(cls,cmd):
        try:
            r=subprocess.run(cmd,shell=True,capture_output=True,text=True,encoding="utf-8",errors="ignore",timeout=40,**_hide());return (r.stdout or "")+(r.stderr or "")
        except Exception as e:return str(e)
    @classmethod
    def rollback_last(cls,log=None,prog=None):
        f=app_dir()/"backups"/"LAST"
        if not f.exists():
            if prog:prog(100,"No backup")
            return False
        root=Path(f.read_text(encoding="utf-8",errors="ignore").strip());reg=root/"hkcu.reg"
        if reg.exists():cls.run('reg import "%s"'%reg)
        if prog:prog(100,"Rollback done")
        if log:log(str(root))
        return True

    # ---- More toggles actions ----
    @classmethod
    def more_copilot(cls, on):
        v=1 if on else 0; btn=0 if on else 1
        cls.reg(r"HKCU\Software\Policies\Microsoft\Windows\WindowsCopilot","TurnOffWindowsCopilot",v)
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot","TurnOffWindowsCopilot",v)
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced","ShowCopilotButton",btn)

    @classmethod
    def more_onedrive(cls, on):
        if on:
            cls.run("taskkill /f /im OneDrive.exe")
            cls.run(r'if exist "%SystemRoot%\System32\OneDriveSetup.exe" "%SystemRoot%\System32\OneDriveSetup.exe" /uninstall')
            cls.run(r'if exist "%SystemRoot%\SysWOW64\OneDriveSetup.exe" "%SystemRoot%\SysWOW64\OneDriveSetup.exe" /uninstall')
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\OneDrive","DisableFileSyncNGSC",1)
            cls.run('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v OneDrive /f')
        else:
            cls.run('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive" /v DisableFileSyncNGSC /f')

    @classmethod
    def more_defender(cls, on):
        return  # disabled

    @classmethod
    def more_edge(cls, on):
        if on:
            cls.run("taskkill /f /im msedge.exe & taskkill /f /im msedgewebview2.exe & taskkill /f /im MicrosoftEdgeUpdate.exe")
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\EdgeUpdate","AutoUpdateCheckPeriodMinutes",0)
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\EdgeUpdate","UpdateDefault",0)
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Edge","StartupBoostEnabled",0)
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Edge","BackgroundModeEnabled",0)
            for s in ("edgeupdate","edgeupdatem","MicrosoftEdgeElevationService"):
                cls.sc_off(s)
            cls.run('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "Microsoft Edge" /f')
        else:
            for s in ("edgeupdate","edgeupdatem"):
                cls.sc_on(s,"demand")

    @classmethod
    def more_telemetry(cls, on):
        if on:
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection","AllowTelemetry",0)
            cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo","Enabled",0)
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System","PublishUserActivities",0)
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System","UploadUserActivities",0)
            cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager","SystemPaneSuggestionsEnabled",0)
            for s in ("DiagTrack","dmwappushservice"): cls.sc_off(s)
            for t in cls.TASKS: cls.run('schtasks /Change /TN "%s" /Disable'%t)
        else:
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection","AllowTelemetry",1)

    @classmethod
    def more_vbs(cls, on):
        if on:
            cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard","EnableVirtualizationBasedSecurity",0)
            cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity","Enabled",0)
            cls.run("bcdedit /set hypervisorlaunchtype off")
        else:
            cls.run("bcdedit /set hypervisorlaunchtype auto")

    @classmethod
    def more_widgets(cls, on):
        if on:
            cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced","TaskbarDa",0)
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Dsh","AllowNewsAndInterests",0)
            cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Feeds","ShellFeedsTaskbarViewMode",2)
        else:
            cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced","TaskbarDa",1)

    @classmethod
    def more_uwp(cls, on):
        if not on: return
        apps="Microsoft.OutlookForWindows,microsoft.windowscommunicationsapps,MicrosoftTeams,MSTeams,Microsoft.YourPhone,Microsoft.XboxApp,Microsoft.XboxGamingOverlay,Microsoft.GetHelp,Microsoft.Getstarted,Microsoft.MicrosoftSolitaireCollection,Microsoft.SkypeApp,Microsoft.WindowsFeedbackHub,Microsoft.WindowsMaps,Microsoft.BingNews,Microsoft.BingWeather,Microsoft.Clipchamp,Microsoft.ZuneMusic,Microsoft.ZuneVideo,Microsoft.549981C3F5F10,MicrosoftWindows.Client.WebExperience"
        ps="$apps=@('%s'); foreach($a in $apps.Split(',')){ Get-AppxPackage -Name $a -AllUsers -EA SilentlyContinue | Remove-AppxPackage -EA SilentlyContinue }" % "','".join(apps.split(","))
        _ps(ps)

    @classmethod
    def more_spectre(cls, on):
        if on:
            cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management","FeatureSettings",1)
            cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management","FeatureSettingsOverride",3)
            cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management","FeatureSettingsOverrideMask",3)
            cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Kernel","DisableTsx",1)
        else:
            cls.run('reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v FeatureSettingsOverride /f')

    @classmethod
    def more_standby_ram(cls, on):
        if on:
            _ps("Get-Process | Where-Object {$_.WorkingSet64 -gt 100MB -and $_.ProcessName -notmatch 'csrss|lsass|services|svchost|dwm|explorer'} | ForEach-Object { try{ $_.MinWorkingSet=1; $_.MaxWorkingSet=1}catch{} }")

    @classmethod
    def more_cortana(cls, on):
        if on:
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search", "AllowCortana", 0)
            cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Search", "BingSearchEnabled", 0)
            cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Search", "CortanaConsent", 0)
        else:
            cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search", "AllowCortana", 1)

    @classmethod
    def more_tips(cls, on):
        v = 0 if on else 1
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SoftLandingEnabled", v)
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338389Enabled", v)

    @classmethod
    def more_notify(cls, on):
        if on:
            cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\PushNotifications", "ToastEnabled", 0)
        else:
            cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\PushNotifications", "ToastEnabled", 1)

    @classmethod
    def more_gamebar(cls, on):
        v = 0 if on else 1
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", v)
        cls.reg(r"HKCU\Software\Microsoft\GameBar", "UseNexusForGameBarEnabled", v)

    @classmethod
    def more_fastboot(cls, on):
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power", "HiberbootEnabled", 0 if on else 1)
        if on:
            cls.run("powercfg /hibernate off")

    @classmethod
    def more_search(cls, on):
        if on:
            cls.sc_off("WSearch")
        else:
            cls.sc_on("WSearch", "auto")


    @classmethod
    def more_startup(cls, on):
        if on:
            cls.run('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /va /f')

    @classmethod
    def more_updates_manual(cls, on):
        if on:
            for s in ("wuauserv", "UsoSvc", "BITS"):
                E.run('sc config "%s" start= demand' % s)
            cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config", "DODownloadMode", 0)
        else:
            for s in ("wuauserv", "BITS"):
                cls.sc_on(s, "auto")

    @classmethod
    def more_xbox(cls, on):
        for s in ("XblAuthManager", "XblGameSave", "XboxNetApiSvc", "XboxGipSvc", "GamingServices", "GamingServicesNet"):
            if on:
                cls.sc_off(s)
            else:
                cls.sc_on(s, "demand")

    @classmethod
    def more_print(cls, on):
        cls.sc_off("Spooler") if on else cls.sc_on("Spooler","auto")

    @classmethod
    def more_fax(cls, on):
        cls.sc_off("Fax") if on else cls.sc_on("Fax","demand")

    @classmethod
    def more_biometric(cls, on):
        cls.sc_off("WbioSrvc") if on else cls.sc_on("WbioSrvc","demand")

    @classmethod
    def more_tablet(cls, on):
        cls.sc_off("TabletInputService") if on else cls.sc_on("TabletInputService","demand")

    @classmethod
    def more_maps(cls, on):
        cls.sc_off("MapsBroker") if on else cls.sc_on("MapsBroker","demand")

    @classmethod
    def more_phone(cls, on):
        cls.sc_off("PhoneSvc") if on else cls.sc_on("PhoneSvc","demand")

    @classmethod
    def more_retail(cls, on):
        cls.sc_off("RetailDemo") if on else None

    @classmethod
    def more_diagtrack(cls, on):
        cls.sc_off("DiagTrack") if on else cls.sc_on("DiagTrack","auto")

    @classmethod
    def more_sysmain(cls, on):
        cls.sc_off("SysMain") if on else cls.sc_on("SysMain","auto")

    @classmethod
    def more_wer(cls, on):
        cls.sc_off("WerSvc") if on else cls.sc_on("WerSvc","demand")

    @classmethod
    def more_rdp(cls, on):
        for s in ("TermService","SessionEnv","UmRdpService"):
            cls.sc_off(s) if on else cls.sc_on(s,"demand")

    @classmethod
    def more_remoteReg(cls, on):
        cls.sc_off("RemoteRegistry") if on else cls.sc_on("RemoteRegistry","demand")

    @classmethod
    def more_bluetooth(cls, on):
        cls.sc_off("BthAvctpSvc") if on else cls.sc_on("BthAvctpSvc","demand")

    @classmethod
    def more_location(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location","Value","Deny" if on else "Allow","REG_SZ")

    @classmethod
    def more_camera(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam","Value","Deny" if on else "Allow","REG_SZ")

    @classmethod
    def more_mic(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone","Value","Deny" if on else "Allow","REG_SZ")

    @classmethod
    def more_accountinfo(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\userAccountInformation","Value","Deny" if on else "Allow","REG_SZ")

    @classmethod
    def more_appdiag(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\appDiagnostics","Value","Deny" if on else "Allow","REG_SZ")

    @classmethod
    def more_bgapps(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications","GlobalUserDisabled",1 if on else 0)

    @classmethod
    def more_transparency(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize","EnableTransparency",0 if on else 1)

    @classmethod
    def more_animations(cls, on):
        cls.reg(r"HKCU\Control Panel\Desktop\WindowMetrics","MinAnimate","0" if on else "1","REG_SZ")
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced","TaskbarAnimations",0 if on else 1)

    @classmethod
    def more_aeropeek(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\DWM","EnableAeroPeek",0 if on else 1)

    @classmethod
    def more_sticky(cls, on):
        cls.reg(r"HKCU\Control Panel\Accessibility\StickyKeys","Flags","506" if on else "510","REG_SZ")

    @classmethod
    def more_filterkeys(cls, on):
        cls.reg(r"HKCU\Control Panel\Accessibility\Keyboard Response","Flags","122" if on else "126","REG_SZ")

    @classmethod
    def more_togglekeys(cls, on):
        cls.reg(r"HKCU\Control Panel\Accessibility\ToggleKeys","Flags","58" if on else "62","REG_SZ")

    @classmethod
    def more_mousekeys(cls, on):
        cls.reg(r"HKCU\Control Panel\Accessibility\MouseKeys","Flags","0" if on else "62","REG_SZ")

    @classmethod
    def more_gamedvr(cls, on):
        cls.reg(r"HKCU\System\GameConfigStore","GameDVR_Enabled",0 if on else 1)
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR","AppCaptureEnabled",0 if on else 1)

    @classmethod
    def more_fse(cls, on):
        if on:
            cls.reg(r"HKCU\System\GameConfigStore","GameDVR_FSEBehaviorMode",2)
            cls.reg(r"HKCU\System\GameConfigStore","GameDVR_FSEBehavior",2)
            cls.reg(r"HKCU\System\GameConfigStore","GameDVR_HonorUserFSEBehaviorMode",1)

    @classmethod
    def more_prefetcher(cls, on):
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters","EnablePrefetcher",0 if on else 3)
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters","EnableSuperfetch",0 if on else 3)

    @classmethod
    def more_lastaccess(cls, on):
        cls.run("fsutil behavior set disablelastaccess %d" % (1 if on else 0))

    @classmethod
    def more_8dot3(cls, on):
        cls.run("fsutil behavior set disable8dot3 %d" % (1 if on else 0))

    @classmethod
    def more_hibernate(cls, on):
        cls.run("powercfg /hibernate %s" % ("off" if on else "on"))

    @classmethod
    def more_reserved(cls, on):
        if on:
            cls.run("DISM /Online /Set-ReservedStorageState /State:Disabled")

    @classmethod
    def more_delivery(cls, on):
        cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config","DODownloadMode",0 if on else 1)

    @classmethod
    def more_activity(cls, on):
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System","PublishUserActivities",0 if on else 1)
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System","UploadUserActivities",0 if on else 1)

    @classmethod
    def more_ads(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo","Enabled",0 if on else 1)

    @classmethod
    def more_input(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\InputPersonalization","RestrictImplicitTextCollection",1 if on else 0)
        cls.reg(r"HKCU\Software\Microsoft\InputPersonalization","RestrictImplicitInkCollection",1 if on else 0)

    @classmethod
    def more_ink(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Personalization\Settings","AcceptedPrivacyPolicy",0 if on else 1)

    @classmethod
    def more_storeauto(cls, on):
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\WindowsStore","AutoDownload",2 if on else 4)

    @classmethod
    def more_smartscreen(cls, on):
        return  # disabled

    @classmethod
    def more_uac(cls, on):
        return  # disabled

    @classmethod
    def more_firewall(cls, on):
        return  # disabled

    @classmethod
    def more_hyperv(cls, on):
        cls.run("bcdedit /set hypervisorlaunchtype %s" % ("off" if on else "auto"))

    @classmethod
    def more_coreparking(cls, on):
        if on:
            cls.run("powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR CPMINCORES 100")
            cls.run("powercfg /setactive SCHEME_CURRENT")

    @classmethod
    def more_gpupreempt(cls, on):
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers\Scheduler","EnablePreemption",1 if on else 0)

    @classmethod
    def more_mmcss(cls, on):
        if on:
            b=r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
            cls.reg(b,"GPU Priority",8); cls.reg(b,"Priority",6)
            cls.reg(b,"Scheduling Category","High","REG_SZ"); cls.reg(b,"SFIO Priority","High","REG_SZ")

    @classmethod
    def more_netthrottle(cls, on):
        cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile","NetworkThrottlingIndex",0xFFFFFFFF if on else 10)

    @classmethod
    def more_tcpnodelay(cls, on):
        cls.reg(r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters","TcpNoDelay",1 if on else 0)

    @classmethod
    def more_visualfx(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects","VisualFXSetting",2 if on else 0)

    @classmethod
    def more_menu(cls, on):
        cls.reg(r"HKCU\Control Panel\Desktop","MenuShowDelay","0" if on else "400","REG_SZ")

    @classmethod
    def more_mouseaccel(cls, on):
        if on:
            cls.reg(r"HKCU\Control Panel\Mouse","MouseSpeed","0","REG_SZ")
            cls.reg(r"HKCU\Control Panel\Mouse","MouseThreshold1","0","REG_SZ")
            cls.reg(r"HKCU\Control Panel\Mouse","MouseThreshold2","0","REG_SZ")
        else:
            cls.reg(r"HKCU\Control Panel\Mouse","MouseSpeed","1","REG_SZ")

    @classmethod
    def more_gameMode(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\GameBar","AutoGameModeEnabled",1 if on else 0)
        cls.reg(r"HKCU\Software\Microsoft\GameBar","AllowAutoGameMode",1 if on else 0)

    @classmethod
    def more_fullscreenopt(cls, on):
        if on:
            cls.reg(r"HKCU\System\GameConfigStore","GameDVR_DXGIHonorFSEWindowsCompatible",1)
            cls.reg(r"HKCU\System\GameConfigStore","GameDVR_FSEBehaviorMode",2)

    @classmethod
    def more_powershelltelem(cls, on):
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell","EnableTelemetry",0 if on else 1)

    @classmethod
    def more_office(cls, on):
        if on:
            cls.reg(r"HKCU\Software\Policies\Microsoft\Office\16.0\osm","Enablelogging",0)
            cls.reg(r"HKCU\Software\Policies\Microsoft\Office\16.0\osm","EnableUpload",0)

    @classmethod
    def more_widgets2(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced","TaskbarDa",0 if on else 1)

    @classmethod
    def more_newsfeeds(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Feeds","ShellFeedsTaskbarViewMode",2 if on else 0)

    @classmethod
    def more_storageSense(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\StorageSense\Parameters\StoragePolicy","01",0 if on else 1)

    @classmethod
    def more_timeline(cls, on):
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System","EnableActivityFeed",0 if on else 1)

    @classmethod
    def more_clipboard(cls, on):
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System", "AllowCrossDeviceClipboard", 0 if on else 1)

    @classmethod
    def more_nearby(cls, on):
        cls.reg(r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CDP","NearShareChannelUserAuthPolicy",0 if on else 2)

    @classmethod
    def more_focusassist(cls, on):
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache\DefaultAccount","",0)



    @classmethod
    def delete_onedrive(cls, log, prog):
        prog(10, "Kill OneDrive"); log("OneDrive")
        cls.run("taskkill /f /im OneDrive.exe")
        prog(40, "Uninstall")
        cls.run(r'if exist "%SystemRoot%\SysWOW64\OneDriveSetup.exe" "%SystemRoot%\SysWOW64\OneDriveSetup.exe" /uninstall')
        cls.run(r'if exist "%SystemRoot%\System32\OneDriveSetup.exe" "%SystemRoot%\System32\OneDriveSetup.exe" /uninstall')
        prog(70, "Policy")
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\OneDrive", "DisableFileSyncNGSC", 1)
        cls.run('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v OneDrive /f')
        prog(100, "Done"); return True

    @classmethod
    def delete_copilot(cls, log, prog):
        prog(20, "Policy"); log("Copilot")
        cls.reg(r"HKCU\Software\Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", 1)
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", 1)
        cls.reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ShowCopilotButton", 0)
        prog(60, "Appx")
        _ps("Get-AppxPackage -AllUsers *Copilot* | Remove-AppxPackage -ErrorAction SilentlyContinue; Get-AppxPackage *MicrosoftWindows.Client.CBS* -ErrorAction SilentlyContinue | ForEach-Object { $_ }")
        # Windows 11 Copilot package names vary
        _ps("Get-AppxPackage -AllUsers *Windows.DevHome* | Remove-AppxPackage -EA SilentlyContinue")
        prog(100, "Done"); return True

    @classmethod
    def delete_mail(cls, log, prog):
        prog(20, "Mail/Calendar"); log("Mail")
        apps = [
            "microsoft.windowscommunicationsapps",  # Mail + Calendar
            "Microsoft.OutlookForWindows",
            "Microsoft.Office.OneNote",
        ]
        for i,a in enumerate(apps):
            prog(20+int((i+1)/len(apps)*70), a[:20])
            _ps("Get-AppxPackage -AllUsers -Name '%s' | Remove-AppxPackage -EA SilentlyContinue; Get-AppxProvisionedPackage -Online | Where-Object {$_.DisplayName -like '%s'} | Remove-AppxProvisionedPackage -Online -EA SilentlyContinue" % (a,a))
        prog(100, "Done"); return True

    @classmethod
    def delete_bloat(cls, log, prog):
        apps = [
            "Microsoft.XboxApp","Microsoft.Xbox.TCUI","Microsoft.XboxGameOverlay",
            "Microsoft.XboxGamingOverlay","Microsoft.XboxIdentityProvider","Microsoft.XboxSpeechToTextOverlay",
            "Microsoft.GamingApp","Microsoft.GetHelp","Microsoft.Getstarted",
            "Microsoft.MicrosoftOfficeHub","Microsoft.MicrosoftSolitaireCollection",
            "Microsoft.MicrosoftStickyNotes","Microsoft.People","Microsoft.SkypeApp",
            "Microsoft.WindowsFeedbackHub","Microsoft.WindowsMaps","Microsoft.WindowsSoundRecorder",
            "Microsoft.BingNews","Microsoft.BingWeather","Microsoft.BingSearch","Microsoft.BingFinance",
            "Microsoft.Todos","Microsoft.PowerAutomateDesktop","Microsoft.549981C3F5F10",
            "Microsoft.Windows.DevHome","Microsoft.Clipchamp","Microsoft.ZuneMusic","Microsoft.ZuneVideo",
            "Microsoft.MixedReality.Portal","Microsoft.Microsoft3DViewer","Microsoft.WindowsAlarms",
            "Microsoft.WindowsCamera","MicrosoftCorporationII.QuickAssist",
            "MicrosoftWindows.Client.WebExperience","Microsoft.YourPhone","MicrosoftTeams","MSTeams",
            "Microsoft.MicrosoftJournal","Microsoft.Windows.Photos","Microsoft.ScreenSketch",
            "Microsoft.WindowsCalculator","Microsoft.Paint","Microsoft.WindowsStore",
        ]
        # Keep Store/Photos/Calculator/Paint optional - user asked junk: skip Store Photos Calc Paint for safety
        apps = [a for a in apps if a not in (
            "Microsoft.WindowsStore","Microsoft.Windows.Photos","Microsoft.WindowsCalculator","Microsoft.Paint","Microsoft.ScreenSketch"
        )]
        for i,a in enumerate(apps):
            prog(int((i+1)/len(apps)*100), a.split(".")[-1][:18]); log(a)
            _ps(
                "Get-AppxPackage -AllUsers -Name '%s' -EA SilentlyContinue | Remove-AppxPackage -EA SilentlyContinue; "
                "Get-AppxProvisionedPackage -Online -EA SilentlyContinue | Where-Object {$_.DisplayName -eq '%s'} | "
                "ForEach-Object { Remove-AppxProvisionedPackage -Online -PackageName $_.PackageName -EA SilentlyContinue }" % (a, a)
            )
        prog(100, "Done"); return True

    @classmethod
    def delete_edge_block(cls, log, prog):
        """Не удаляет Edge полностью (система), но режет фон/автозапуск/обновления."""
        prog(10, "Kill Edge"); log("Edge limit")
        cls.run("taskkill /f /im msedge.exe & taskkill /f /im msedgewebview2.exe & taskkill /f /im MicrosoftEdgeUpdate.exe")
        prog(40, "Policy")
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\EdgeUpdate", "AutoUpdateCheckPeriodMinutes", 0)
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\EdgeUpdate", "UpdateDefault", 0)
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Edge", "StartupBoostEnabled", 0)
        cls.reg(r"HKLM\SOFTWARE\Policies\Microsoft\Edge", "BackgroundModeEnabled", 0)
        prog(70, "Services")
        for s in ("edgeupdate","edgeupdatem","MicrosoftEdgeElevationService"):
            cls.sc_off(s)
        prog(100, "Done"); return True


    @classmethod
    def folder_tweaks(cls, log, prog):
        folder = tweaks_dir()
        files = sorted(
            [p for ext in (".reg", ".bat", ".cmd", ".ps1") for p in folder.glob("*" + ext)],
            key=lambda x: x.name.lower(),
        )
        if not files:
            prog(100, "Empty")
            return True
        for i, f in enumerate(files):
            prog(int((i + 1) / len(files) * 100), f.name[:18])
            log(f.name)
            if f.suffix.lower() == ".reg":
                cls.run('regedit /s "%s"' % f)
            elif f.suffix.lower() in (".bat", ".cmd"):
                cls.run('cmd /c "%s"' % f, cwd=str(folder))
            else:
                cls.run(
                    'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%s"' % f,
                    cwd=str(folder),
                )
        prog(100, "Done")
        return True

    @classmethod
    def ram_profile(cls, log, prog, label):
        folder = ram_dir(); folder.mkdir(exist_ok=True)
        for c in [folder/(label+".bat"), folder/(label+".reg"), folder/(label+".ps1"),
                  folder/(label.replace(" ", "")+".bat")]:
            if c.exists():
                prog(30, c.name); log(c.name)
                if c.suffix.lower() == ".reg":
                    cls.run('regedit /s "%s"' % c)
                elif c.suffix.lower() in (".bat", ".cmd"):
                    cls.run('cmd /c "(echo.|\"%s\")"' % str(c), cwd=str(folder))
                else:
                    cls.run('powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%s"' % c, cwd=str(folder))
                prog(100, "Done"); return True
        prog(100, "Not found"); return False


    @staticmethod
    def _backup_stamp():
        return time.strftime("%Y%m%d_%H%M%S")

    @classmethod
    def create_backup(cls, log=None, prog=None):
        """Create a restore point plus registry/power/service snapshots."""
        folder = backup_dir() / cls._backup_stamp()
        folder.mkdir(parents=True, exist_ok=True)
        if prog: prog(10, "Restore Point")
        if log: log("Creating restore point")
        # Restore Point can fail when System Protection is disabled; continue with file backups.
        cls.run('powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Checkpoint-Computer -Description \'CORE OPTI\' -RestorePointType \'MODIFY_SETTINGS\' -ErrorAction Stop } catch {}"')
        if prog: prog(30, "Registry")
        cls.run('reg export "HKCU\\Software" "%s" /y' % (folder / "HKCU_Software.reg"))
        cls.run('reg export "HKCU\\Control Panel" "%s" /y' % (folder / "HKCU_ControlPanel.reg"))
        cls.run('reg export "HKLM\\SOFTWARE" "%s" /y' % (folder / "HKLM_Software.reg"))
        cls.run('reg export "HKLM\\SYSTEM\\CurrentControlSet\\Control" "%s" /y' % (folder / "HKLM_Control.reg"))
        if prog: prog(55, "Power Plan")
        cls.run('powercfg /getactivescheme > "%s"' % (folder / "powerplan.txt"))
        cls.run('powercfg /export "%s" SCHEME_CURRENT' % (folder / "powerplan.pow"))
        if prog: prog(75, "Services")
        cls.run('powershell -NoProfile -Command "Get-Service | Select Name,Status,StartType | Export-Csv -NoTypeInformation -Encoding UTF8 \'%s\'"' % (folder / "services.csv"))
        if prog: prog(90, "Metadata")
        (folder / "README.txt").write_text(
            "CORE OPTI backup\\nCreated: %s\\nRegistry backups, power plan and service snapshot are stored here.\\n" % time.strftime("%Y-%m-%d %H:%M:%S"),
            encoding="utf-8")
        if prog: prog(100, "Backup ready")
        if log: log(str(folder))
        return str(folder)

    @classmethod
    def rollback_backup(cls, folder, log=None, prog=None):
        """Restore registry backups and the saved power plan."""
        folder = Path(folder)
        if not folder.exists(): return False
        files = [folder/"HKCU_Software.reg", folder/"HKCU_ControlPanel.reg", folder/"HKLM_Software.reg", folder/"HKLM_Control.reg"]
        existing = [x for x in files if x.exists()]
        total = max(1, len(existing) + 1)
        for i, f in enumerate(existing, 1):
            if prog: prog(int(i/total*80), f.name)
            if log: log(f.name)
            cls.run('reg import "%s"' % f)
        powf = folder/"powerplan.pow"
        if powf.exists():
            if prog: prog(90, "Power Plan")
            cls.run('powercfg /import "%s"' % powf)
        if prog: prog(100, "Rollback done")
        if log: log("Rollback complete; restart Windows to apply all changes")
        return bool(existing)

    @classmethod
    def list_backups(cls):
        d=backup_dir()
        d.mkdir(exist_ok=True)
        return sorted([x for x in d.iterdir() if x.is_dir()], key=lambda x:x.name, reverse=True)

    @classmethod
    def verify_system(cls):
        checks=[]
        checks.append(("Admin", is_admin()))
        try:
            raw=cls.run_capture('powercfg /getactivescheme')
            checks.append(("Power plan detected", bool(raw)))
        except Exception: checks.append(("Power plan detected", False))
        for svc in ("WSearch","SysMain","wuauserv","BITS"):
            out=cls.run_capture('sc query "%s"' % svc)
            checks.append(("Service %s exists" % svc, "SERVICE_NAME" in out or "FAILED" not in out))
        checks.append(("Backup folder", backup_dir().exists()))
        return checks

    @staticmethod
    def run_capture(cmd):
        try:
            kw=dict(shell=True,capture_output=True,text=True,encoding="utf-8",errors="ignore",timeout=20)
            kw.update(_hide())
            r=subprocess.run(cmd,**kw)
            return (r.stdout or "") + (r.stderr or "")
        except Exception: return ""

    @classmethod
    def write_report(cls, log=None, prog=None):
        d=backup_dir(); d.mkdir(exist_ok=True)
        f=d/("CORE_OPTI_report_"+cls._backup_stamp()+".txt")
        if prog: prog(20,"Collecting")
        lines=["CORE OPTI SYSTEM REPORT", "="*28, "Time: "+time.strftime("%Y-%m-%d %H:%M:%S"), "Admin: "+str(is_admin()), ""]
        try:
            lines += ["OS:", cls.run_capture('powershell -NoProfile -Command "(Get-CimInstance Win32_OperatingSystem).Caption"').strip()]
            lines += ["CPU:", cls.run_capture('powershell -NoProfile -Command "(Get-CimInstance Win32_Processor | Select -First 1 -Expand Name)"').strip()]
            lines += ["GPU:", cls.run_capture('powershell -NoProfile -Command "(Get-CimInstance Win32_VideoController | Select -First 1 -Expand Name)"').strip()]
            lines += ["Active power plan:", cls.run_capture('powercfg /getactivescheme').strip()]
        except Exception: pass
        lines.append("")
        lines.append("Verification:")
        for k,v in cls.verify_system(): lines.append("[%s] %s" % ("OK" if v else "FAIL", k))
        f.write_text("\n".join(lines)+"\n", encoding="utf-8")
        if prog: prog(100,"Report saved")
        if log: log(str(f))
        return str(f)

    @classmethod
    def optimize_profile(cls, profile, log, prog):
        """Profiles use existing CORE OPTI engines; backup must be created first."""
        cls.create_backup(log, lambda p,s: prog(int(p*0.25), s))
        if profile == "Safe":
            cls.cleanup(log, lambda p,s: prog(25+int(p*0.35), s))
            cls.game_tweaks(log, lambda p,s: prog(60+int(p*0.40), s))
        elif profile == "Gaming":
            cls.game_tweaks(log, lambda p,s: prog(20+int(p*0.30), s))
            cls.cpu_boost(log, lambda p,s: prog(50+int(p*0.35), s))
            cls.disable_tasks(log, lambda p,s: prog(85+int(p*0.15), s))
        elif profile == "Extreme":
            cls.game_tweaks(log, lambda p,s: prog(15+int(p*0.25), s))
            cls.cpu_boost(log, lambda p,s: prog(40+int(p*0.35), s))
            cls.disable_tasks(log, lambda p,s: prog(75+int(p*0.10), s))
            cls.kill_services(log, lambda p,s: prog(85+int(p*0.15), s))
        cls.write_report(log, lambda p,s: prog(100,s))
        return True

    @classmethod
    def startup_items(cls):
        """Return Run-key startup entries without changing them."""
        ps="""$a=@(); foreach($p in @('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run','HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run')) { if(Test-Path $p){ $o=Get-ItemProperty $p; foreach($x in $o.PSObject.Properties){ if($x.Name -notmatch '^PS'){$a += [pscustomobject]@{Location=$p;Name=$x.Name;Command=[string]$x.Value}} } } }; $a | ConvertTo-Csv -NoTypeInformation"""
        out=_ps(ps)
        rows=[]
        for line in out.splitlines()[1:]:
            parts=[x.strip('"') for x in line.split('","')]
            if len(parts)>=3: rows.append(parts[:3])
        return rows

    @classmethod
    def unload(cls, log, prog):
        prog(30,"Power"); cls.run("powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e")
        prog(60,"GameDVR"); cls.reg(r"HKCU\System\GameConfigStore","GameDVR_Enabled",1)
        prog(100,"Done"); return True


# ---- Smart Optimizer / diagnostics ----
class SmartOptimizer:
    @staticmethod
    def scan():
        info={"warnings":[],"cpu":0,"ram":0,"disk":0,"gpu":"Unknown","disk_model":"Unknown","os":"Unknown"}
        try:
            x=sample_loads(); info.update({"cpu":x["cpu"],"ram":x["ram"],"disk":x["disk"]})
        except Exception: pass
        for k,cmd in (("gpu",'(Get-CimInstance Win32_VideoController | Select -First 1 -Expand Name)'),("disk_model",'(Get-CimInstance Win32_DiskDrive | Select -First 1 -Expand Model)'),("os",'(Get-CimInstance Win32_OperatingSystem | Select -First 1 -Expand Caption)')):
            try:
                v=_ps(cmd).strip()
                if v:info[k]=v.splitlines()[0]
            except Exception:pass
        if info["ram"]>=90:info["warnings"].append("RAM usage is high")
        if info["disk"]>=95:info["warnings"].append("System disk is nearly full")
        if info["cpu"]>=90:info["warnings"].append("CPU usage is currently high")
        return info
    @staticmethod
    def startup_items():
        lines=[]
        for root in (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",r"HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"):
            out=_ps('(Get-ItemProperty "%s" -ErrorAction SilentlyContinue | Format-List *)'%root)
            if out:lines.append("[%s]\n%s"%(root,out))
        return "\n\n".join(lines)
    @staticmethod
    def benchmark():
        b=sample_loads(); t=time.perf_counter(); _ps('$x=0;1..50000|%%{$x+=$_};$x|Out-Null'); e=time.perf_counter()-t; a=sample_loads()
        return {"cpu_before":b["cpu"],"ram_before":b["ram"],"disk_before":b["disk"],"cpu_after":a["cpu"],"ram_after":a["ram"],"disk_after":a["disk"],"script_time":e}


class AmbientFX:
    """Lightweight ambient UI animation: drifting glow particles and breathing highlights."""
    def __init__(self, canvas):
        self.canvas = canvas
        self.running = True
        self.items = []
        self.phase = 0.0
        self._seed()
        self._tick()

    def _seed(self):
        self.items.clear()
        w = max(self.canvas.winfo_width(), 800)
        h = max(self.canvas.winfo_height(), 600)
        for _ in range(18):
            self.items.append({
                "x": random.uniform(0, w), "y": random.uniform(0, h),
                "r": random.uniform(1.0, 2.8),
                "vx": random.uniform(-0.16, 0.16),
                "vy": random.uniform(-0.10, 0.10),
                "a": random.random() * 6.28
            })

    def _tick(self):
        if not self.running:
            return
        try:
            self.canvas.delete("ambient_fx")
            w = max(self.canvas.winfo_width(), 800)
            h = max(self.canvas.winfo_height(), 600)
            self.phase += 0.025
            if getattr(TH, "name", "") == "RGB":
                import colorsys
                hue = (time.time() * 7.0) % 360
                rr, gg, bb = colorsys.hsv_to_rgb(hue / 360.0, .62, .70)
                c = "#%02x%02x%02x" % (int(rr*255), int(gg*255), int(bb*255))
            else:
                c = TH.NEON_DIM
            for p in self.items:
                p["x"] = (p["x"] + p["vx"]) % w
                p["y"] = (p["y"] + p["vy"]) % h
                pulse = 0.75 + 0.25 * math.sin(self.phase + p["a"])
                r = p["r"] * pulse
                self.canvas.create_oval(p["x"]-r, p["y"]-r, p["x"]+r, p["y"]+r,
                                       fill=c, outline="", tags="ambient_fx")
        except tk.TclError:
            return
        self.canvas.after(40, self._tick)

    def stop(self):
        self.running = False

# ---- app ----
class CoreOpti(tk.Tk):
    # ключи, после которых рекомендуем reboot
    REBOOT_KEYS = {
        "vbs", "spectre", "hyperv", "fastboot", "hibernate", "coreparking",
        "prefetcher", "sysmain", "timer",
    }
    DANGEROUS_JOBS = {
        "PROFILE_Extreme", "SVCS", "DEL_BLOAT", "DEL_OD", "DEL_COP", "DEL_MAIL", "FOLDER",
    }
    PACKS = {
        "Privacy": [
            "telemetry", "cortana", "tips", "notify", "ads", "activity", "input", "ink",
            "location", "camera", "mic", "accountinfo", "appdiag", "diagtrack", "wer",
            "powershelltelem", "office", "timeline", "clipboard", "nearby",
        ],
        "Gaming": [
            "gamedvr", "gamebar", "fse", "gameMode", "fullscreenopt", "mmcss", "netthrottle",
            "tcpnodelay", "mouseaccel", "visualfx", "menu", "animations", "transparency",
            "aeropeek", "bgapps", "widgets", "widgets2", "newsfeeds", "xbox",
        ],
        "Debloat": [
            "onedrive", "copilot", "edge", "uwp", "search", "print", "fax", "maps",
            "phone", "retail", "tablet", "biometric", "rdp", "remoteReg", "startup",
            "updates", "storeauto", "delivery", "storageSense",
        ],
    }

    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        theme_name = self.cfg.get("theme") or "Neon Green"
        if theme_name == "Auto":
            theme_name = detect_windows_theme()
        TH.apply(theme_name if theme_name in THEMES else "Neon Green")
        self.overrideredirect(True)
        try:
            self.geometry(self.cfg.get("geometry") or "1060x700+80+40")
        except Exception:
            self.geometry("1060x700+80+40")
        self.configure(bg=TH.BG)
        self.nav = {}
        self.busy = False
        self.ring = None
        self.sysinfo = {}
        self._drag = {"x": 0, "y": 0}
        self.more_state = dict(self.cfg.get("more_state") or {})
        self.reboot_needed = bool(self.cfg.get("reboot_needed"))
        self._job_q = queue.Queue()
        self._job_worker_running = False
        self._toggle_cards = {}
        self._log_lines = []
        tweaks_dir().mkdir(exist_ok=True)
        ram_dir().mkdir(exist_ok=True)
        backup_dir().mkdir(exist_ok=True)
        self.bg = LiveBG(self)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.rootf = tk.Frame(self, bg=TH.BG)
        self.rootf.place(x=0, y=0, relwidth=1, relheight=1)
        self._chrome()
        self._body()
        self.show("dash")
        self.after(120, lambda: self._round(28))
        self.bind("<Map>", lambda e: self.after(50, lambda: self._round(28)))
        threading.Thread(target=lambda: gather_sysinfo(self._on_info), daemon=True).start()

        def _warmup():
            try:
                import psutil
                psutil.cpu_percent(interval=0.05)
                sample_loads(force=True)
            except Exception:
                pass
        threading.Thread(target=_warmup, daemon=True).start()
        self.bind("<Escape>", lambda e: self._close())
        self.protocol("WM_DELETE_WINDOW", self._close)
        if self.reboot_needed:
            self.after(600, lambda: self.status("Restart recommended", level="warn"))

    def _persist(self):
        try:
            self.cfg["more_state"] = dict(self.more_state)
            self.cfg["theme"] = TH.name
            self.cfg["geometry"] = self.geometry()
            self.cfg["reboot_needed"] = self.reboot_needed
            save_config(self.cfg)
        except Exception:
            pass

    def _close(self):
        self._persist()
        try:
            self.bg.stop()
        except Exception:
            pass
        self.destroy()

    def _round(self, radius=26):
        try:
            self.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()
            w, h = max(self.winfo_width(), 200), max(self.winfo_height(), 200)
            hr = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, radius, radius)
            ctypes.windll.user32.SetWindowRgn(hwnd, hr, True)
        except Exception:
            pass

    def _chrome(self):
        self.bar = tk.Frame(self.rootf, bg=TH.SIDE, height=38)
        self.bar.pack(fill="x")
        self.bar.pack_propagate(False)
        self.bar.bind("<Button-1>", self._sm)
        self.bar.bind("<B1-Motion>", self._mm)
        self.bar.bind("<Double-Button-1>", lambda e: self._close())
        self.logo = tk.Label(self.bar, text="  ◆  CORE OPTI", font=("Segoe UI", 11, "bold"), bg=TH.SIDE, fg=TH.NEON, anchor="w")
        self.logo.pack(side="left", padx=6)
        self.logo.bind("<Button-1>", self._sm)
        self.logo.bind("<B1-Motion>", self._mm)
        self.reboot_badge = tk.Label(self.bar, text="", font=("Segoe UI", 8, "bold"), bg=TH.SIDE, fg="#ff6b6b")
        self.reboot_badge.pack(side="left", padx=8)
        if self.reboot_needed:
            self.reboot_badge.configure(text="● RESTART")
        ctl = tk.Frame(self.bar, bg=TH.SIDE)
        ctl.pack(side="right", padx=6)
        self.btn_min = NeonBtn(ctl, "—", command=self._minimize, w=36, h=26, tip="Свернуть")
        self.btn_min.pack(side="left", padx=2)
        self.btn_x = NeonBtn(ctl, "✕", command=self._close, w=36, h=26, tip="Закрыть")
        self.btn_x.pack(side="left", padx=2)

    def _minimize(self):
        try:
            self._persist()
            self.overrideredirect(False)
            self.iconify()
            self.after(200, lambda: self.overrideredirect(True) if self.state() == "normal" else None)
            self.bind("<Map>", self._on_restore)
        except Exception:
            pass

    def _on_restore(self, event=None):
        if self.state() == "normal":
            try:
                self.overrideredirect(True)
                self.after(40, lambda: self._round(28))
            except Exception:
                pass

    def _sm(self, e):
        self._drag["x"], self._drag["y"] = e.x, e.y

    def _mm(self, e):
        self.geometry("+%d+%d" % (self.winfo_x() + e.x - self._drag["x"], self.winfo_y() + e.y - self._drag["y"]))

    def status(self, text, level="info"):
        """Короткий статус внизу окна."""
        colors = {"info": TH.MUTED, "ok": TH.NEON, "warn": "#ffb347", "err": "#ff6b6b"}
        try:
            self.status_lbl.configure(text=str(text)[:90], fg=colors.get(level, TH.MUTED))
        except Exception:
            pass

    def log(self, t):
        line = "[%s] %s" % (time.strftime("%H:%M:%S"), t)
        print(line)
        self._log_lines.append(line)
        if len(self._log_lines) > 300:
            self._log_lines = self._log_lines[-200:]
        try:
            if getattr(self, "log_text", None) and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.insert("end", line + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            pass

    def _confirm(self, title, message):
        try:
            return messagebox.askyesno(title, message, parent=self)
        except Exception:
            return True

    def _mark_reboot(self):
        self.reboot_needed = True
        self.cfg["reboot_needed"] = True
        try:
            self.reboot_badge.configure(text="● RESTART")
        except Exception:
            pass
        self.status("Restart recommended", level="warn")
        self._persist()

    def _body(self):
        wrap = tk.Frame(self.rootf, bg=TH.BG)
        wrap.pack(fill="both", expand=True)
        self.side = tk.Frame(wrap, bg=TH.SIDE, width=196)
        self.side.pack(side="left", fill="y")
        self.side.pack_propagate(False)
        for key, title in (
            ("dash", "Dashboard"), ("clean", "Cleaner"), ("tweaks", "Tweaks"), ("boost", "Boost"),
            ("more", "More"), ("profiles", "Profiles"), ("recovery", "Recovery"), ("delete", "Delete"),
            ("ram", "RAM"), ("folder", "Tweaks folder"), ("theme", "Theme"), ("settings", "Settings"),
        ):
            it = SideItem(self.side, title, command=lambda k=key: self.show(k))
            it.pack(padx=6, pady=2)
            self.nav[key] = it
        bot = tk.Frame(self.side, bg=TH.SIDE)
        bot.pack(side="bottom", fill="x", padx=8, pady=10)
        self.btn_unload = NeonBtn(bot, "UNLOAD", command=self._unload, w=176, h=30, tip="Сброс power plan + GameDVR")
        self.btn_unload.pack(pady=2)
        self.btn_dc = NeonBtn(bot, "Discord", command=lambda: webbrowser.open(DISCORD_URL), w=176, h=30)
        self.btn_dc.pack(pady=2)
        right = tk.Frame(wrap, bg=TH.BG)
        right.pack(side="right", fill="both", expand=True)
        self.main = tk.Frame(right, bg=TH.BG)
        self.main.pack(fill="both", expand=True)
        self.head = tk.Frame(self.main, bg=TH.BG, height=44)
        self.head.pack(fill="x", padx=18, pady=(8, 0))
        self.head.pack_propagate(False)
        self.h1 = tk.Label(self.head, text="", font=("Segoe UI", 16, "bold"), bg=TH.BG, fg=TH.TEXT, anchor="w")
        self.h1.pack(side="left")
        self.h2 = tk.Label(self.head, text="", font=("Segoe UI", 8), bg=TH.BG, fg=TH.MUTED, anchor="w")
        self.h2.pack(side="left", padx=8, pady=(4, 0))
        self.content = tk.Frame(self.main, bg=TH.BG)
        self.content.pack(fill="both", expand=True, padx=18, pady=(2, 4))
        # status bar
        self.statusbar = tk.Frame(right, bg=TH.SIDE, height=26)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        self.status_lbl = tk.Label(
            self.statusbar,
            text=("Admin OK" if is_admin() else "Run as Admin for full effect"),
            font=("Segoe UI", 8), bg=TH.SIDE, fg=TH.MUTED, anchor="w",
        )
        self.status_lbl.pack(side="left", padx=10)
        self.queue_lbl = tk.Label(self.statusbar, text="", font=("Segoe UI", 8), bg=TH.SIDE, fg=TH.NEON, anchor="e")
        self.queue_lbl.pack(side="right", padx=10)

    def _on_info(self, info):
        self.sysinfo=info
        if getattr(self,"_cur","")=="dash": self.after(0, lambda:self.show("dash"))

    def _clear(self):
        self._cur = ""  # stop dashboard pollers immediately
        for w in self.content.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        self.ring = None
        self.g_cpu = self.g_gpu = self.g_ram = self.g_disk = None

    def show(self, key):
        self._cur = key
        try:
            self.unbind_all("<MouseWheel>")
        except Exception:
            pass
        for k, it in self.nav.items():
            it.set_active(k == key)
        self._clear()
        {"dash": self._dash, "clean": self._clean, "tweaks": self._tweaks, "boost": self._boost,
         "more": self._more, "profiles": self._profiles, "recovery": self._recovery, "delete": self._delete, "ram": self._ram, "folder": self._folder, "theme": self._theme,
         "settings": self._settings}.get(key, self._dash)()

    def _dash(self):
        self.h1.configure(text="What's up")
        self.h2.configure(text="overview · live load")
        # live gauges row
        gauges = tk.Frame(self.content, bg=TH.BG)
        gauges.pack(fill="x", pady=(0, 8))
        self.g_cpu = LoadGauge(gauges, "CPU", 118)
        self.g_gpu = LoadGauge(gauges, "GPU", 118)
        self.g_ram = LoadGauge(gauges, "RAM", 118)
        self.g_disk = LoadGauge(gauges, "DISK", 118)
        for g in (self.g_cpu, self.g_gpu, self.g_ram, self.g_disk):
            g.pack(side="left", padx=10)
        self._load_job = None
        self._poll_loads()

        info = self.sysinfo or {}
        grid = tk.Frame(self.content, bg=TH.BG)
        grid.pack(fill="both", expand=True)
        cards = [
            ("CPU", "Processor", [("Model", (info.get("cpu") or "…")[:38]), ("Cores", info.get("cores", "…"))]),
            ("GPU", "Graphics", [("Model", (info.get("gpu") or "…")[:38]), ("VRAM", info.get("vram", "…"))]),
            ("Memory", "RAM", [("Total", info.get("ram_total", "…")), ("Type", info.get("ram_type", "…"))]),
            ("System", "OS", [("OS", (info.get("os") or "…")[:32]), ("Version", info.get("os_ver", "…"))]),
            ("Storage", "Disk", [("Model", (info.get("disk") or "…")[:32]), ("Size", info.get("disk_size", "…"))]),
            ("More", "Optional", [("Toggles", "More tab"), ("Delete", "Apps tab")]),
        ]
        for i, (t, s, lines) in enumerate(cards):
            InfoCard(grid, t, s, lines).grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="n")
        row = tk.Frame(self.content, bg=TH.BG)
        row.pack(anchor="w", pady=8)
        for lab, k in (("Cleaner", "clean"), ("Tweaks", "tweaks"), ("Boost", "boost"), ("More", "more"), ("Delete", "delete")):
            NeonBtn(row, lab, command=lambda x=k: self.show(x), w=95).pack(side="left", padx=3)

    def _poll_loads(self):
        if getattr(self, "_cur", "") != "dash":
            return
        def work():
            try:
                data = sample_loads()
            except Exception:
                data = {"cpu": 0, "ram": 0, "disk": 0, "gpu": 0}
            def apply():
                if getattr(self, "_cur", "") != "dash":
                    return
                try:
                    if getattr(self, "g_cpu", None):
                        self.g_cpu.set(data.get("cpu", 0))
                        self.g_gpu.set(data.get("gpu", 0))
                        self.g_ram.set(data.get("ram", 0))
                        self.g_disk.set(data.get("disk", 0))
                except Exception:
                    pass
                if getattr(self, "_cur", "") == "dash":
                    self.after(1500, self._poll_loads)
            try:
                self.after(0, apply)
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()


    def _clean(self):
        self.h1.configure(text="Cleaner")
        self.h2.configure(text="temp · prefetch · dns · update cache")
        before = free_space_gb("C")
        self.ring = SmoothRing(self.content, 180)
        self.ring.pack(pady=8)
        self.ring.set(0, "Idle")
        self.clean_space_lbl = tk.Label(
            self.content,
            text="Free C: %.1f GB" % before,
            bg=TH.BG, fg=TH.MUTED, font=("Segoe UI", 9),
        )
        self.clean_space_lbl.pack()

        def run_clean():
            b = free_space_gb("C")

            def wrapped(log, prog):
                ok = E.cleanup(log, prog)
                a = free_space_gb("C")
                freed = max(0.0, a - b)
                log("Freed ~%.2f GB (now %.1f GB free)" % (freed, a))
                def ui():
                    try:
                        self.clean_space_lbl.configure(
                            text="Free C: %.1f GB  (+%.2f GB)" % (a, freed),
                            fg=TH.NEON,
                        )
                    except Exception:
                        pass
                    self.status("Cleaned · +%.2f GB" % freed, level="ok")
                self.after(0, ui)
                return ok

            self._job(wrapped, "CLEAN")

        NeonBtn(self.content, "RUN CLEANUP", command=run_clean, w=150, tip="Очистка TEMP / Prefetch / DNS").pack(pady=6)

    def _tweaks(self):
        self.h1.configure(text="Tweaks")
        self.h2.configure(text="FPS · services · tasks")
        self.ring = SmoothRing(self.content, 170)
        self.ring.pack(pady=8)
        self.ring.set(0, "Idle")
        row = tk.Frame(self.content, bg=TH.BG)
        row.pack(pady=6)
        NeonBtn(row, "GAME TWEAKS", command=lambda: self._job(E.game_tweaks, "TWEAKS"), w=140).pack(side="left", padx=3)
        NeonBtn(row, "SERVICES OFF", command=lambda: self._job(E.kill_services, "SVCS"), w=130, tip="Отключает много фоновых служб").pack(side="left", padx=3)
        NeonBtn(row, "TASKS OFF", command=lambda: self._job(E.disable_tasks, "TASKS"), w=120).pack(side="left", padx=3)

    def _boost(self):
        self.h1.configure(text="Boost")
        self.h2.configure(text="CPU 100% · power · GPU hints")
        self.ring = SmoothRing(self.content, 170)
        self.ring.pack(pady=8)
        self.ring.set(0, "Idle")
        NeonBtn(self.content, "ACTIVATE BOOST", command=lambda: self._job(E.cpu_boost, "BOOST"), w=160, tip="Ultimate power + unpark + RAM hints").pack(pady=8)

    def _more(self):
        self.h1.configure(text="More")
        self.h2.configure(text=("ADMIN OK" if is_admin() else "ЗАПУСТИ ОТ АДМИНА — иначе половина не сработает"))
        top = tk.Frame(self.content, bg=TH.BG)
        top.pack(fill="x", pady=(0, 4))
        tk.Label(top, text="Search", bg=TH.BG, fg=TH.MUTED, font=("Segoe UI", 8)).pack(side="left")
        self.more_search_var = tk.StringVar()
        ent = tk.Entry(
            top, textvariable=self.more_search_var, width=22,
            bg=TH.CARD, fg=TH.TEXT, insertbackground=TH.NEON,
            relief="flat", font=("Segoe UI", 9),
        )
        ent.pack(side="left", padx=6, ipady=3)
        packs = tk.Frame(top, bg=TH.BG)
        packs.pack(side="left", padx=8)
        for pname in ("Privacy", "Gaming", "Debloat"):
            NeonBtn(
                packs, pname,
                command=lambda n=pname: self._apply_pack(n),
                w=78, h=28, tip="Включить пакет: " + pname,
            ).pack(side="left", padx=2)
        NeonBtn(packs, "Export", command=self._export_preset, w=64, h=28, tip="Сохранить пресет JSON").pack(side="left", padx=2)
        NeonBtn(packs, "Import", command=self._import_preset, w=64, h=28, tip="Загрузить пресет JSON").pack(side="left", padx=2)

        body = tk.Frame(self.content, bg=TH.BG)
        body.pack(fill="both", expand=True)
        canvas = tk.Canvas(body, bg=TH.BG, highlightthickness=0, bd=0)
        sb = tk.Scrollbar(
            body, orient="vertical", command=canvas.yview, bg=TH.CARD, troughcolor=TH.BG,
            activebackground=TH.NEON, highlightthickness=0, bd=0, width=8,
        )
        inner = tk.Frame(canvas, bg=TH.BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _wheel)

        # compact activity log
        logf = tk.Frame(self.content, bg=TH.BG, height=72)
        logf.pack(fill="x", pady=(4, 0))
        self.log_text = tk.Text(
            logf, height=3, bg=TH.CARD, fg=TH.MUTED, insertbackground=TH.NEON,
            relief="flat", font=("Consolas", 7), state="disabled",
        )
        self.log_text.pack(fill="x")
        for line in self._log_lines[-12:]:
            self.log_text.configure(state="normal")
            self.log_text.insert("end", line + "\n")
            self.log_text.configure(state="disabled")

        items = [
            ("copilot","Disable Copilot","Кнопка и политика Windows Copilot."),
            ("onedrive","Remove OneDrive","Деинсталл + запрет синхронизации."),
            ("edge","Limit Edge","Фон, автозапуск, обновления Edge."),
            ("telemetry","Telemetry & CEIP","Диагностика, реклама, CEIP-задачи."),
            ("widgets","Widgets / News","Виджеты и новости на панели."),
            ("vbs","Disable VBS / HVCI","+FPS. Может сломать WSL2."),
            ("spectre","Spectre/Meltdown off","Митигации CPU выкл (+FPS/−sec)."),
            ("uwp","Remove UWP junk","Xbox, Bing, Clipchamp, Teams UWP."),
            ("updates","Updates on demand","wuauserv/BITS не в фоне."),
            ("startup","Clear Run keys","Автозагрузка HKCU\\Run."),
            ("standby","Trim memory","Сжатие working set фона."),
            ("cortana","Disable Cortana","Cortana и Bing Search."),
            ("tips","Disable Tips","Подсказки Windows."),
            ("notify","Disable Toasts","Toast-уведомления."),
            ("gamebar","Disable Game Bar","Xbox Game Bar."),
            ("fastboot","Disable Fast Startup","Hiberboot выкл."),
            ("search","Disable WSearch","Индексация поиска."),
            ("xbox","Disable Xbox services","Xbox auth/save/net службы."),
            ("print","Disable Print Spooler","Печать (если не нужна)."),
            ("fax","Disable Fax","Служба факса."),
            ("biometric","Disable Biometric","WbioSrvc."),
            ("tablet","Disable Tablet Input","Сенсорный ввод."),
            ("maps","Disable MapsBroker","Карты Windows."),
            ("phone","Disable PhoneSvc","Связка с телефоном."),
            ("retail","Disable Retail Demo","Демо-режим."),
            ("diagtrack","Disable DiagTrack","Телеметрия Connected User."),
            ("sysmain","Disable SysMain","Superfetch/SysMain."),
            ("wer","Disable Error Reporting","WER."),
            ("rdp","Disable Remote Desktop","RDP/TermService."),
            ("remoteReg","Disable Remote Registry","RemoteRegistry."),
            ("bluetooth","Disable Bluetooth support","BthAvctpSvc (если нет BT)."),
            ("location","Deny Location","Геолокация Deny."),
            ("camera","Deny Camera apps","Камера для UWP Deny."),
            ("mic","Deny Microphone apps","Микрофон UWP Deny."),
            ("accountinfo","Deny Account Info","Данные аккаунта Deny."),
            ("appdiag","Deny App Diagnostics","Диагностика приложений."),
            ("bgapps","Disable Background Apps","Фон UWP GlobalUserDisabled."),
            ("transparency","Disable Transparency","Эффекты прозрачности."),
            ("animations","Disable Animations","Анимации окон."),
            ("aeropeek","Disable Aero Peek","Aero Peek."),
            ("sticky","Disable StickyKeys","Липкие клавиши."),
            ("filterkeys","Disable FilterKeys","Фильтрация клавиш."),
            ("togglekeys","Disable ToggleKeys","ToggleKeys."),
            ("mousekeys","Disable MouseKeys","MouseKeys."),
            ("gamedvr","Disable GameDVR","Запись GameDVR."),
            ("fse","Force FSE","Fullscreen Optimizations mode."),
            ("prefetcher","Disable Prefetcher","Prefetch/Superfetch reg."),
            ("lastaccess","Disable NTFS LastAccess","NTFS last access time."),
            ("8dot3","Disable 8.3 names","NTFS short names."),
            ("hibernate","Hibernate Off","powercfg hibernate off."),
            ("reserved","Disable Reserved Storage","DISM Reserved Storage."),
            ("delivery","Delivery Optimization off","DODownloadMode=0."),
            ("activity","Disable Activity History","Timeline/activities."),
            ("ads","Disable Advertising ID","AdvertisingInfo."),
            ("input","Disable Typing Data","Input personalization."),
            ("ink","Disable Inking Data","Ink collection."),
            ("storeauto","Store Auto-Update off","WindowsStore AutoDownload."),
            ("hyperv","Hyper-V off (bcdedit)","hypervisorlaunchtype off."),
            ("coreparking","CPU Core Unpark","Min cores 100%."),
            ("gpupreempt","GPU Preemption on","Scheduler preemption."),
            ("mmcss","MMCSS Games High","Games task priority."),
            ("netthrottle","Network Throttle off","NetworkThrottlingIndex."),
            ("tcpnodelay","TCP NoDelay","TcpNoDelay=1."),
            ("visualfx","Best Performance FX","VisualFXSetting=2."),
            ("menu","MenuShowDelay 0","Мгновенное меню."),
            ("mouseaccel","Mouse Accel off","Enhance pointer precision."),
            ("gameMode","Game Mode on","AutoGameModeEnabled."),
            ("fullscreenopt","FSO compatible","DXGIHonor FSE."),
            ("powershelltelem","PS Telemetry off","PowerShell telemetry."),
            ("office","Office telemetry off","Если Office установлен."),
            ("widgets2","TaskbarDa off","Кнопка виджетов."),
            ("newsfeeds","News feeds off","ShellFeeds."),
            ("storageSense","Storage Sense off","Автоочистка диска."),
            ("timeline","Timeline off","EnableActivityFeed=0."),
            ("clipboard","Cloud Clipboard off","Clipboard history cloud."),
            ("nearby","Nearby Sharing off","Обмен поблизости."),
            ("focusassist","Focus Assist off","Не беспокоить правила."),
        ]

        self._more_items = items
        self._more_inner = inner
        self._more_canvas = canvas
        self._toggle_cards = {}

        def on_toggle(key, state):
            self.more_state[key] = state
            self._persist()

            def work():
                try:
                    aliases = {
                        "updates": "more_updates_manual",
                        "standby": "more_standby_ram",
                        "remoteReg": "more_remoteReg",
                        "gameMode": "more_gameMode",
                        "storageSense": "more_storageSense",
                        "fullscreenopt": "more_fullscreenopt",
                        "powershelltelem": "more_powershelltelem",
                        "netthrottle": "more_netthrottle",
                        "tcpnodelay": "more_tcpnodelay",
                        "coreparking": "more_coreparking",
                        "gpupreempt": "more_gpupreempt",
                        "widgets2": "more_widgets2",
                        "newsfeeds": "more_newsfeeds",
                        "focusassist": "more_focusassist",
                        "8dot3": "more_8dot3",
                    }
                    name = aliases.get(key, "more_" + key)
                    fn = getattr(E, name, None)
                    if not fn:
                        self.log("NO HANDLER " + key)
                        return
                    if not is_admin():
                        self.log("NEED ADMIN for " + key)
                        self.after(0, lambda: self.status("Need Admin: " + key, level="warn"))
                    try:
                        fn(state)
                        self.log("OK %s = %s" % (key, state))
                        self.after(0, lambda: self.status("%s → %s" % (key, "ON" if state else "OFF"), level="ok"))
                        if state and key in self.REBOOT_KEYS:
                            self.after(0, self._mark_reboot)
                    except Exception as ex:
                        self.log("FAIL %s %s" % (key, ex))
                        self.after(0, lambda: self.status("Fail: " + key, level="err"))
                except Exception as e:
                    self.log(str(e))

            threading.Thread(target=work, daemon=True).start()

        self._more_on_toggle = on_toggle

        def render(filter_text=""):
            for w in inner.winfo_children():
                w.destroy()
            self._toggle_cards.clear()
            q = (filter_text or "").strip().lower()
            shown = 0
            for key, title, desc in items:
                if q and q not in title.lower() and q not in desc.lower() and q not in key.lower():
                    continue
                st = self.more_state.get(key, False)
                tip = desc
                if key in self.REBOOT_KEYS:
                    tip = desc + " · may need restart"
                card = ToggleCard(inner, title, desc, key, st, on_toggle, w=390, h=66, tip=tip)
                card.grid(row=shown // 2, column=shown % 2, padx=6, pady=5, sticky="nw")
                self._toggle_cards[key] = card
                shown += 1
            inner.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        self._more_render = render
        render()
        self.more_search_var.trace_add("write", lambda *_: render(self.more_search_var.get()))

    def _apply_pack(self, pack_name):
        keys = self.PACKS.get(pack_name) or []
        if not keys:
            return
        if not self._confirm("Pack: " + pack_name, "Включить пакет «%s» (%d toggles)?\nРекомендуется backup." % (pack_name, len(keys))):
            return
        for k in keys:
            self.more_state[k] = True
            card = self._toggle_cards.get(k)
            if card is not None:
                card.set_state(True, notify=True)
            elif getattr(self, "_more_on_toggle", None):
                self._more_on_toggle(k, True)
        self._persist()
        self.status("Pack %s applied" % pack_name, level="ok")
        self.log("Pack applied: " + pack_name)

    def _export_preset(self):
        path = app_dir() / ("preset_%s.json" % time.strftime("%Y%m%d_%H%M%S"))
        try:
            data = {"more_state": dict(self.more_state), "theme": TH.name, "exported": time.strftime("%Y-%m-%d %H:%M:%S")}
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.status("Exported: " + path.name, level="ok")
            self.log("Preset exported " + str(path))
        except Exception as e:
            self.status("Export failed", level="err")
            self.log(str(e))

    def _import_preset(self):
        # простой выбор последнего preset_*.json в папке приложения
        files = sorted(app_dir().glob("preset_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            self.status("No preset_*.json found", level="warn")
            return
        path = files[0]
        if not self._confirm("Import preset", "Импортировать %s ?" % path.name):
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            st = data.get("more_state") or {}
            for k, v in st.items():
                self.more_state[k] = bool(v)
                card = self._toggle_cards.get(k)
                if card is not None:
                    card.set_state(bool(v), notify=True)
                elif getattr(self, "_more_on_toggle", None):
                    self._more_on_toggle(k, bool(v))
            self._persist()
            if getattr(self, "_more_render", None):
                self._more_render(self.more_search_var.get() if hasattr(self, "more_search_var") else "")
            self.status("Imported " + path.name, level="ok")
            self.log("Preset imported " + str(path))
        except Exception as e:
            self.status("Import failed", level="err")
            self.log(str(e))


    def _profiles(self):
        self.h1.configure(text="Profiles")
        self.h2.configure(text="backup → optimize → verify → report")
        tk.Label(
            self.content,
            text="Каждый профиль сначала создаёт резервную копию. Extreme отключает много служб.",
            bg=TH.BG, fg=TH.MUTED, font=("Segoe UI", 8),
        ).pack(pady=(4, 12))
        grid = tk.Frame(self.content, bg=TH.BG)
        grid.pack(pady=6)
        desc = {
            "Safe": "Очистка + базовые игровые твики.",
            "Gaming": "Игровые твики + Power/CPU/GPU.",
            "Extreme": "Максимально агрессивный профиль; службы отключаются.",
        }
        last = self.cfg.get("last_profile") or ""
        if last:
            tk.Label(self.content, text="Last used: " + last, bg=TH.BG, fg=TH.NEON, font=("Segoe UI", 8)).pack()

        def run_profile(name):
            if name == "Extreme":
                if not self._confirm("Extreme profile", "Extreme отключает службы и агрессивно твикает систему.\nПродолжить? (backup будет создан)"):
                    return

            def wrapped(log, prog):
                ok = E.optimize_profile(name, log, prog)
                self.cfg["last_profile"] = name
                self._persist()
                if name in ("Gaming", "Extreme"):
                    self.after(0, self._mark_reboot)
                self.after(0, lambda: self.status("Profile %s done" % name, level="ok"))
                return ok

            self._job(wrapped, "PROFILE_" + name)

        for i, name in enumerate(("Safe", "Gaming", "Extreme")):
            box = tk.Frame(grid, bg=TH.BG)
            box.grid(row=i, column=0, pady=6, sticky="w")
            NeonBtn(box, name, command=lambda n=name: run_profile(n), w=120, h=36).pack(side="left")
            tk.Label(box, text=desc[name], bg=TH.BG, fg=TH.TEXT, font=("Segoe UI", 9)).pack(side="left", padx=12)

    def _recovery(self):
        self.h1.configure(text="Recovery")
        self.h2.configure(text="backup · restore point · rollback · verification")
        grid=tk.Frame(self.content,bg=TH.BG); grid.pack(pady=10)
        NeonBtn(grid,"CREATE BACKUP",command=lambda:self._job(E.create_backup,"BACKUP"),w=150).grid(row=0,column=0,padx=5,pady=5)
        NeonBtn(grid,"VERIFY",command=lambda:self._job(lambda log,prog: E.write_report(log,prog),"VERIFY"),w=120).grid(row=0,column=1,padx=5,pady=5)
        backups=E.list_backups()
        tk.Label(self.content,text="Последние резервные копии:",bg=TH.BG,fg=TH.TEXT,font=("Segoe UI Semibold",9)).pack(pady=(8,4))
        for b in backups[:5]:
            NeonBtn(self.content,"ROLLBACK "+b.name,command=lambda p=str(b):self._job(lambda log,prog:E.rollback_backup(p,log,prog),"ROLLBACK"),w=260,h=30).pack(pady=3)
        if not backups:
            tk.Label(self.content,text="Пока резервных копий нет.",bg=TH.BG,fg=TH.MUTED).pack(pady=10)

    def _delete(self):
        self.h1.configure(text="Delete")
        self.h2.configure(text="OneDrive · Copilot · Mail · bloat (нужен Админ)")
        self.ring = SmoothRing(self.content, 160)
        self.ring.pack(pady=8)
        self.ring.set(0, "Idle")
        grid = tk.Frame(self.content, bg=TH.BG)
        grid.pack(pady=6)
        btns = [
            ("OneDrive", lambda: self._job(E.delete_onedrive, "DEL_OD")),
            ("Copilot", lambda: self._job(E.delete_copilot, "DEL_COP")),
            ("Mail / Calendar", lambda: self._job(E.delete_mail, "DEL_MAIL")),
            ("Windows Bloat", lambda: self._job(E.delete_bloat, "DEL_BLOAT")),
            ("Edge limit", lambda: self._job(E.delete_edge_block, "DEL_EDGE")),
        ]
        for i,(lab,cmd) in enumerate(btns):
            NeonBtn(grid, lab, command=cmd, w=150, h=34).grid(row=i//2, column=i%2, padx=6, pady=6)
        tip = tk.Label(self.content, text="Удаляет UWP/политики. Store, Photos, Calculator не трогаем.\nПерезагрузка после удаления желательна.",
                       bg=TH.BG, fg=TH.MUTED, font=("Segoe UI", 8), justify="left")
        tip.pack(pady=8)


    def _ram(self):
        self.h1.configure(text="RAM"); self.ring=SmoothRing(self.content,140); self.ring.pack(pady=6); self.ring.set(0,"Select")
        grid=tk.Frame(self.content,bg=TH.BG); grid.pack()
        for i,lab in enumerate(["8 GB","12 GB","16 GB","24 GB","32 GB","64 GB"]):
            NeonBtn(grid,lab,command=lambda l=lab:self._job(lambda log,prog:E.ram_profile(log,prog,l),"RAM"),w=90,h=30).grid(row=i//3,column=i%3,padx=4,pady=4)

    def _folder(self):
        self.h1.configure(text="Tweaks folder")
        files=sorted([p.name for p in tweaks_dir().glob("*") if p.suffix.lower() in (".reg",".bat",".ps1")])
        txt="\n".join("• "+n for n in files[:12]) if files else "(optional extra files)"
        c=tk.Canvas(self.content,width=500,height=100,bg=TH.BG,highlightthickness=0); c.pack()
        rr(c,1,1,499,99,r=12,fill=TH.CARD,outline=TH.BORDER)
        c.create_text(12,10,text=txt,anchor="nw",fill=TH.TEXT,font=("Consolas",8),width=470)
        self.ring=SmoothRing(self.content,130); self.ring.pack(pady=4)
        NeonBtn(self.content,"RUN FILES",command=lambda:self._job(E.folder_tweaks,"FOLDER"),w=120).pack()


    def _theme(self):
        self.h1.configure(text="Theme"); grid=tk.Frame(self.content,bg=TH.BG); grid.pack(pady=16)
        for i,name in enumerate(THEMES):
            NeonBtn(grid,name,command=lambda n=name:self._set_theme(n),w=140,h=34).grid(row=i//2,column=i%2,padx=6,pady=6)

    def _set_theme(self, name):
        TH.apply(name)
        self.cfg["theme"] = name
        self._persist()
        for w, bg in (
            (self, TH.BG), (self.rootf, TH.BG), (self.bar, TH.SIDE), (self.side, TH.SIDE),
            (self.main, TH.BG), (self.head, TH.BG), (self.content, TH.BG),
            (getattr(self, "statusbar", None), TH.SIDE),
        ):
            if w is None:
                continue
            try:
                w.configure(bg=bg)
            except Exception:
                pass
        try:
            self.logo.configure(bg=TH.SIDE, fg=TH.NEON)
            self.h1.configure(bg=TH.BG, fg=TH.TEXT)
            self.h2.configure(bg=TH.BG, fg=TH.MUTED)
            self.status_lbl.configure(bg=TH.SIDE)
            self.queue_lbl.configure(bg=TH.SIDE, fg=TH.NEON)
            self.reboot_badge.configure(bg=TH.SIDE)
        except Exception:
            pass
        self.bg.refresh_bg()
        self.bg._init()
        for it in self.nav.values():
            it.refresh()
        self.btn_unload.refresh()
        self.btn_dc.refresh()
        for b in (getattr(self, "btn_min", None), getattr(self, "btn_x", None)):
            if b is not None:
                try:
                    b.refresh()
                except Exception:
                    pass
        self.show("theme")

    def _settings(self):
        self.h1.configure(text="Settings")
        self.h2.configure(text="config · presets · verify")
        admin = "YES" if is_admin() else "NO"
        c = tk.Canvas(self.content, width=520, height=100, bg=TH.BG, highlightthickness=0)
        c.pack(pady=8)
        rr(c, 1, 1, 519, 99, r=12, fill=TH.CARD, outline=TH.BORDER)
        c.create_text(14, 22, text="Admin: " + admin, anchor="w", fill=TH.NEON, font=("Segoe UI Semibold", 11))
        c.create_text(14, 48, text=str(app_dir()), anchor="w", fill=TH.MUTED, font=("Segoe UI", 8))
        c.create_text(
            14, 72,
            text="Reboot needed: " + ("YES" if self.reboot_needed else "no") + "  ·  Toggles saved: %d" % len(self.more_state),
            anchor="w", fill=TH.MUTED, font=("Segoe UI", 8),
        )
        row = tk.Frame(self.content, bg=TH.BG)
        row.pack(pady=6)
        NeonBtn(row, "Export preset", command=self._export_preset, w=120).pack(side="left", padx=4)
        NeonBtn(row, "Import preset", command=self._import_preset, w=120).pack(side="left", padx=4)
        NeonBtn(row, "Verify report", command=lambda: self._job(E.write_report, "VERIFY"), w=120).pack(side="left", padx=4)
        NeonBtn(row, "Clear reboot flag", command=self._clear_reboot, w=130).pack(side="left", padx=4)
        NeonBtn(self.content, "Discord", command=lambda: webbrowser.open(DISCORD_URL), w=120).pack(pady=8)
        NeonBtn(
            self.content, "Theme: Auto (Windows)",
            command=lambda: self._set_theme(detect_windows_theme()),
            w=200, tip="AMOLED если тёмная тема Windows, иначе Ice",
        ).pack(pady=4)

    def _clear_reboot(self):
        self.reboot_needed = False
        self.cfg["reboot_needed"] = False
        try:
            self.reboot_badge.configure(text="")
        except Exception:
            pass
        self._persist()
        self.status("Reboot flag cleared", level="ok")

    def prog(self, p, s):
        def _u():
            try:
                if self.ring is not None:
                    self.ring.set(p, s)
            except Exception:
                pass
        try:
            self.after(0, _u)
        except Exception:
            pass

    def _job(self, fn, title):
        """Очередь задач: UI не блокируется, jobs идут по одному."""
        if sys.platform != "win32":
            return
        if title in self.DANGEROUS_JOBS:
            if not self._confirm(title, "Это действие может сильно изменить систему.\nПродолжить?\n\n(%s)" % title):
                return
        now = time.time()
        last = getattr(self, "_last_job", {})
        if now - last.get(title, 0) < 0.6:
            return
        last[title] = now
        self._last_job = last
        self._job_q.put((fn, title))
        try:
            self.queue_lbl.configure(text="Queue: %d" % self._job_q.qsize())
        except Exception:
            pass
        self.status("Queued: " + title, level="info")
        self.log("Queued " + title)
        self._ensure_job_worker()

    def _ensure_job_worker(self):
        if self._job_worker_running:
            return
        self._job_worker_running = True

        def worker():
            while True:
                try:
                    fn, title = self._job_q.get(timeout=0.4)
                except queue.Empty:
                    self._job_worker_running = False
                    try:
                        self.after(0, lambda: self.queue_lbl.configure(text=""))
                    except Exception:
                        pass
                    return
                ring_ref = self.ring
                self.after(0, lambda t=title: self.status("Running: " + t, level="info"))
                self.log("Start " + title)
                try:
                    fn(self.log, self.prog)
                    self.log("Done " + title)
                    self.after(0, lambda t=title: self.status("Done: " + t, level="ok"))
                    if title in ("BOOST", "PROFILE_Gaming", "PROFILE_Extreme", "TWEAKS"):
                        self.after(0, self._mark_reboot)
                except Exception as e:
                    self.log("ERR %s: %s" % (title, e))
                    self.after(0, lambda: self.status("Failed: " + title, level="err"))
                finally:
                    def done(r=ring_ref):
                        try:
                            if self.ring is not None and self.ring is r:
                                self.ring.set(100, "Done")
                        except Exception:
                            pass
                        try:
                            self.queue_lbl.configure(text=("Queue: %d" % self._job_q.qsize()) if self._job_q.qsize() else "")
                        except Exception:
                            pass
                    try:
                        self.after(0, done)
                    except Exception:
                        pass
                    self._job_q.task_done()

        threading.Thread(target=worker, daemon=True).start()

    def _unload(self):
        self.show("clean")
        self._job(E.unload, "UNLOAD")

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    CoreOpti().mainloop()
