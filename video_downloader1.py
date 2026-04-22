"""
VideoVault - Universal Video Downloader
Supports YouTube, Twitter/X, Instagram, TikTok, Facebook, Vimeo, and 1000+ sites via yt-dlp
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys
import json
import subprocess
import urllib.request
from pathlib import Path
import time

try:
    import yt_dlp
except ImportError:
    print("Installing yt-dlp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--break-system-packages", "-q"])
    import yt_dlp

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ─────────────────────────────────────────────
#  Color palette & fonts
# ─────────────────────────────────────────────
BG        = "#0D0D0F"
SURFACE   = "#16161A"
CARD      = "#1E1E24"
BORDER    = "#2A2A35"
ACCENT    = "#7C3AED"        # vivid violet
ACCENT2   = "#A78BFA"        # light violet
SUCCESS   = "#22C55E"
WARNING   = "#F59E0B"
DANGER    = "#EF4444"
TEXT      = "#F4F4F5"
MUTED     = "#71717A"
WHITE     = "#FFFFFF"


class VideoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("VideoVault — Universal Downloader")
        self.root.geometry("820x720")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(700, 600)

        self.download_path = str(Path.home() / "Downloads")
        self.video_info    = None
        self.formats       = []
        self._after_id     = None          # for URL debounce

        self._setup_styles()
        self._build_ui()

    # ──────────────────────────────────────────
    #  Styles
    # ──────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame",        background=BG)
        style.configure("Card.TFrame",   background=CARD)
        style.configure("Surface.TFrame",background=SURFACE)

        style.configure("TLabel",        background=BG,      foreground=TEXT,   font=("Segoe UI", 10))
        style.configure("Card.TLabel",   background=CARD,    foreground=TEXT,   font=("Segoe UI", 10))
        style.configure("Muted.TLabel",  background=CARD,    foreground=MUTED,  font=("Segoe UI", 9))
        style.configure("Title.TLabel",  background=BG,      foreground=WHITE,  font=("Segoe UI", 22, "bold"))
        style.configure("Sub.TLabel",    background=BG,      foreground=MUTED,  font=("Segoe UI", 10))
        style.configure("Success.TLabel",background=CARD,    foreground=SUCCESS,font=("Segoe UI", 9))
        style.configure("Warn.TLabel",   background=BG,      foreground=WARNING,font=("Segoe UI", 9))

        style.configure("Accent.TButton",
            background=ACCENT, foreground=WHITE, font=("Segoe UI", 10, "bold"),
            borderwidth=0, focusthickness=0, padding=(16, 8))
        style.map("Accent.TButton",
            background=[("active", "#6D28D9"), ("disabled", BORDER)],
            foreground=[("disabled", MUTED)])

        style.configure("Ghost.TButton",
            background=SURFACE, foreground=TEXT, font=("Segoe UI", 9),
            borderwidth=1, relief="flat", padding=(10, 6))
        style.map("Ghost.TButton",
            background=[("active", CARD)])

        style.configure("Danger.TButton",
            background=DANGER, foreground=WHITE, font=("Segoe UI", 9, "bold"),
            borderwidth=0, padding=(10, 6))
        style.map("Danger.TButton",
            background=[("active", "#DC2626")])

        style.configure("TCombobox",
            fieldbackground=SURFACE, background=SURFACE,
            foreground=TEXT, selectforeground=WHITE,
            selectbackground=ACCENT, arrowcolor=ACCENT2,
            borderwidth=1, relief="flat")

        style.configure("TProgressbar",
            troughcolor=BORDER, background=ACCENT,
            lightcolor=ACCENT, darkcolor=ACCENT, borderwidth=0, thickness=6)

        style.configure("TNotebook",       background=BG,      borderwidth=0)
        style.configure("TNotebook.Tab",
            background=SURFACE, foreground=MUTED,
            font=("Segoe UI", 9), padding=(14, 6), borderwidth=0)
        style.map("TNotebook.Tab",
            background=[("selected", CARD)],
            foreground=[("selected", ACCENT2)])

    # ──────────────────────────────────────────
    #  UI Layout
    # ──────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=BG, pady=20, padx=28)
        hdr.pack(fill="x")

        tk.Label(hdr, text=" ʘ‿ʘ VideoVault by abdulrahxxm (WinSyS) ", font=("Segoe UI", 24, "bold"),
                 bg=BG, fg=WHITE).pack(side="left")
        tk.Label(hdr, text="Universal Video Downloader", font=("Segoe UI", 10),
                 bg=BG, fg=MUTED).pack(side="left", padx=12, pady=6)

        # URL input card
        url_card = tk.Frame(self.root, bg=CARD, padx=20, pady=16)
        url_card.pack(fill="x", padx=24, pady=(0, 12))

        tk.Label(url_card, text="Video URL", font=("Segoe UI", 9, "bold"),
                 bg=CARD, fg=ACCENT2).pack(anchor="w")
        url_row = tk.Frame(url_card, bg=CARD)
        url_row.pack(fill="x", pady=(6, 0))

        self.url_var = tk.StringVar()
        self.url_var.trace_add("write", self._on_url_change)

        self.url_entry = tk.Entry(url_row, textvariable=self.url_var,
                                  bg=SURFACE, fg=TEXT, insertbackground=ACCENT2,
                                  relief="flat", font=("Segoe UI", 11),
                                  bd=0, highlightthickness=2,
                                  highlightbackground=BORDER,
                                  highlightcolor=ACCENT)
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=8, ipadx=10)

        self.paste_btn = ttk.Button(url_row, text="📋 Paste", style="Ghost.TButton",
                                    command=self._paste_url)
        self.paste_btn.pack(side="left", padx=(8, 0))

        self.fetch_btn = ttk.Button(url_row, text="🔍 Fetch Info", style="Accent.TButton",
                                    command=self._fetch_info)
        self.fetch_btn.pack(side="left", padx=(8, 0))

        # Status bar
        self.status_var = tk.StringVar(value="Paste a video URL above to get started")
        self.status_lbl = tk.Label(url_card, textvariable=self.status_var,
                                   font=("Segoe UI", 9), bg=CARD, fg=MUTED)
        self.status_lbl.pack(anchor="w", pady=(6, 0))

        # Main content area (notebook)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        self._build_info_tab()
        self._build_download_tab()
        self._build_log_tab()

        # Bottom bar
        self._build_bottom_bar()

    def _build_info_tab(self):
        frame = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(frame, text="  ℹ  Video Info  ")

        # Thumbnail + metadata side by side
        content = tk.Frame(frame, bg=CARD)
        content.pack(fill="both", expand=True, padx=16, pady=16)

        # Left: thumbnail
        self.thumb_frame = tk.Frame(content, bg=SURFACE, width=280, height=160,
                                    highlightthickness=1, highlightbackground=BORDER)
        self.thumb_frame.pack(side="left", padx=(0, 16), pady=0)
        self.thumb_frame.pack_propagate(False)

        self.thumb_label = tk.Label(self.thumb_frame, bg=SURFACE, fg=MUTED,
                                    text="🎬\n\nThumbnail\nappears here",
                                    font=("Segoe UI", 9), justify="center")
        self.thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        # Right: metadata
        meta = tk.Frame(content, bg=CARD)
        meta.pack(side="left", fill="both", expand=True)

        fields = [
            ("Title",    "title_val"),
            ("Channel",  "channel_val"),
            ("Duration", "duration_val"),
            ("Views",    "views_val"),
            ("Upload",   "upload_val"),
            ("Site",     "site_val"),
        ]
        for label, attr in fields:
            row = tk.Frame(meta, bg=CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{label}:", width=10, anchor="w",
                     font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED).pack(side="left")
            var = tk.StringVar(value="—")
            setattr(self, attr, var)
            tk.Label(row, textvariable=var, anchor="w", wraplength=340,
                     font=("Segoe UI", 9), bg=CARD, fg=TEXT).pack(side="left", fill="x", expand=True)

        # Description
        tk.Label(meta, text="Description:", anchor="w",
                 font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED).pack(anchor="w", pady=(10, 2))
        self.desc_text = tk.Text(meta, height=4, bg=SURFACE, fg=MUTED,
                                  font=("Segoe UI", 9), relief="flat",
                                  bd=0, wrap="word", state="disabled")
        self.desc_text.pack(fill="x")

    def _build_download_tab(self):
        frame = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(frame, text="  ⬇  Download  ")

        inner = tk.Frame(frame, bg=CARD, padx=16, pady=16)
        inner.pack(fill="both", expand=True)

        # Format selection
        fmt_row = tk.Frame(inner, bg=CARD)
        fmt_row.pack(fill="x", pady=(0, 12))

        tk.Label(fmt_row, text="Format / Quality", font=("Segoe UI", 9, "bold"),
                 bg=CARD, fg=ACCENT2).pack(anchor="w", pady=(0, 4))

        self.format_var = tk.StringVar(value="best — Best Quality (Auto)")
        self.format_cb = ttk.Combobox(fmt_row, textvariable=self.format_var,
                                       state="readonly", font=("Segoe UI", 9))
        self.format_cb["values"] = [
            "best — Best Quality (Auto)",
            "bestvideo+bestaudio — Best Video + Best Audio",
            "1080p — Full HD (1080p)",
            "720p — HD (720p)",
            "480p — SD (480p)",
            "360p — Low (360p)",
            "audio_only — Audio Only (MP3)",
        ]
        self.format_cb.pack(fill="x", ipady=4)

        # Output directory
        dir_row = tk.Frame(inner, bg=CARD)
        dir_row.pack(fill="x", pady=(0, 12))

        tk.Label(dir_row, text="Save To", font=("Segoe UI", 9, "bold"),
                 bg=CARD, fg=ACCENT2).pack(anchor="w", pady=(0, 4))

        path_row = tk.Frame(dir_row, bg=CARD)
        path_row.pack(fill="x")

        self.path_var = tk.StringVar(value=self.download_path)
        self.path_entry = tk.Entry(path_row, textvariable=self.path_var,
                                    bg=SURFACE, fg=TEXT, insertbackground=ACCENT2,
                                    relief="flat", font=("Segoe UI", 9),
                                    bd=0, highlightthickness=1,
                                    highlightbackground=BORDER,
                                    highlightcolor=ACCENT)
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=6, ipadx=6)

        ttk.Button(path_row, text="Browse", style="Ghost.TButton",
                   command=self._browse_path).pack(side="left", padx=(8, 0))

        # Options
        opts_frame = tk.Frame(inner, bg=CARD)
        opts_frame.pack(fill="x", pady=(0, 16))

        tk.Label(opts_frame, text="Options", font=("Segoe UI", 9, "bold"),
                 bg=CARD, fg=ACCENT2).pack(anchor="w", pady=(0, 6))

        self.embed_subs  = tk.BooleanVar(value=False)
        self.embed_thumb = tk.BooleanVar(value=True)
        self.convert_mp4 = tk.BooleanVar(value=True)

        for var, label in [
            (self.embed_subs,  "Embed subtitles (if available)"),
            (self.embed_thumb, "Embed thumbnail in audio downloads"),
            (self.convert_mp4, "Convert to MP4 (recommended)"),
        ]:
            cb = tk.Checkbutton(opts_frame, text=label, variable=var,
                                bg=CARD, fg=TEXT, selectcolor=SURFACE,
                                activebackground=CARD, activeforeground=TEXT,
                                font=("Segoe UI", 9))
            cb.pack(anchor="w")

        # Progress
        prog_frame = tk.Frame(inner, bg=CARD)
        prog_frame.pack(fill="x", pady=(0, 12))

        prog_header = tk.Frame(prog_frame, bg=CARD)
        prog_header.pack(fill="x")
        tk.Label(prog_header, text="Progress", font=("Segoe UI", 9, "bold"),
                 bg=CARD, fg=ACCENT2).pack(side="left")
        self.prog_pct = tk.Label(prog_header, text="", font=("Segoe UI", 9),
                                  bg=CARD, fg=ACCENT2)
        self.prog_pct.pack(side="right")

        self.progress = ttk.Progressbar(prog_frame, mode="determinate", style="TProgressbar")
        self.progress.pack(fill="x", pady=(4, 0))

        self.prog_detail = tk.Label(prog_frame, text="",
                                     font=("Segoe UI", 8), bg=CARD, fg=MUTED)
        self.prog_detail.pack(anchor="w")

        # Download button
        btn_row = tk.Frame(inner, bg=CARD)
        btn_row.pack(fill="x")

        self.dl_btn = ttk.Button(btn_row, text="⬇  Start Download",
                                  style="Accent.TButton", command=self._start_download)
        self.dl_btn.pack(side="left")

        self.cancel_btn = ttk.Button(btn_row, text="✕ Cancel",
                                      style="Danger.TButton", command=self._cancel_download,
                                      state="disabled")
        self.cancel_btn.pack(side="left", padx=(10, 0))

        self.open_btn = ttk.Button(btn_row, text="📂 Open Folder",
                                    style="Ghost.TButton", command=self._open_folder)
        self.open_btn.pack(side="right")

    def _build_log_tab(self):
        frame = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(frame, text="  📋  Log  ")

        inner = tk.Frame(frame, bg=CARD, padx=16, pady=16)
        inner.pack(fill="both", expand=True)

        hdr = tk.Frame(inner, bg=CARD)
        hdr.pack(fill="x", pady=(0, 6))
        tk.Label(hdr, text="Download Log", font=("Segoe UI", 9, "bold"),
                 bg=CARD, fg=ACCENT2).pack(side="left")
        ttk.Button(hdr, text="Clear", style="Ghost.TButton",
                   command=self._clear_log).pack(side="right")

        self.log_text = tk.Text(inner, bg=SURFACE, fg=TEXT,
                                 font=("Consolas", 9), relief="flat", bd=0,
                                 state="disabled", wrap="word")
        log_scroll = ttk.Scrollbar(inner, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        log_scroll.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True)

    def _build_bottom_bar(self):
        bar = tk.Frame(self.root, bg=SURFACE, pady=8, padx=24)
        bar.pack(fill="x", side="bottom")

        tk.Label(bar, text="Powered by yt-dlp  •  Supports 1000+ sites including YouTube, Twitter, Instagram, TikTok",
                 font=("Segoe UI", 8), bg=SURFACE, fg=MUTED).pack(side="left")

    # ──────────────────────────────────────────
    #  Actions
    # ──────────────────────────────────────────
    def _on_url_change(self, *_):
        if self._after_id:
            self.root.after_cancel(self._after_id)
        # Auto-fetch after 1 s of inactivity
        self._after_id = self.root.after(1000, self._auto_fetch)

    def _auto_fetch(self):
        url = self.url_var.get().strip()
        if url.startswith(("http://", "https://")) and len(url) > 15:
            self._fetch_info()

    def _paste_url(self):
        try:
            text = self.root.clipboard_get().strip()
            if text:
                self.url_var.set(text)
        except tk.TclError:
            pass

    def _browse_path(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = folder
            self.path_var.set(folder)

    def _open_folder(self):
        path = self.path_var.get()
        if os.path.exists(path):
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])

    def _set_status(self, msg, color=MUTED):
        self.status_var.set(msg)
        self.status_lbl.configure(fg=color)

    def _log(self, msg):
        self.log_text.configure(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    # ──────────────────────────────────────────
    #  Fetch video info
    # ──────────────────────────────────────────
    def _fetch_info(self):
        url = self.url_var.get().strip()
        if not url:
            self._set_status("Please enter a URL first", DANGER)
            return
        self._set_status("Fetching video info…", ACCENT2)
        self.fetch_btn.configure(state="disabled")
        threading.Thread(target=self._fetch_worker, args=(url,), daemon=True).start()

    def _fetch_worker(self, url):
        opts = {
            "quiet":        True,
            "no_warnings":  True,
            "extract_flat": False,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": url,
            },
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            self.video_info = info
            self.root.after(0, self._update_info_ui, info)
            self.root.after(0, lambda: self._log(f"Fetched: {info.get('title', url)}"))
        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Error: {e}", DANGER))
            self.root.after(0, lambda: self._log(f"FETCH ERROR: {e}"))
        finally:
            self.root.after(0, lambda: self.fetch_btn.configure(state="normal"))

    def _update_info_ui(self, info):
        title    = info.get("title", "Unknown")
        channel  = info.get("uploader") or info.get("channel") or "—"
        duration = info.get("duration")
        views    = info.get("view_count")
        upload   = info.get("upload_date", "")
        site     = info.get("extractor_key", "—")
        desc     = info.get("description", "") or ""

        dur_str = f"{int(duration//60)}m {int(duration%60)}s" if duration else "—"
        view_str = f"{views:,}" if views else "—"
        upload_str = f"{upload[:4]}-{upload[4:6]}-{upload[6:]}" if len(upload) == 8 else "—"

        self.title_val.set(title[:80] + ("…" if len(title) > 80 else ""))
        self.channel_val.set(channel)
        self.duration_val.set(dur_str)
        self.views_val.set(view_str)
        self.upload_val.set(upload_str)
        self.site_val.set(site)

        self.desc_text.configure(state="normal")
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", desc[:400] + ("…" if len(desc) > 400 else ""))
        self.desc_text.configure(state="disabled")

        self._set_status(f"✔ Found: {title[:60]}", SUCCESS)
        self.notebook.select(0)

        # Load thumbnail async
        thumb = info.get("thumbnail")
        if thumb:
            threading.Thread(target=self._load_thumb, args=(thumb,), daemon=True).start()

        # Build format list
        formats = info.get("formats", [])
        self._build_format_list(formats)

    def _load_thumb(self, url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = r.read()

            if PIL_AVAILABLE:
                import io
                img = Image.open(io.BytesIO(data))
                img = img.resize((280, 157), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.root.after(0, lambda: self._show_thumb(photo))
            else:
                self.root.after(0, lambda: self.thumb_label.configure(
                    text="🖼 Thumbnail\n(install Pillow\nfor preview)"))
        except Exception:
            pass

    def _show_thumb(self, photo):
        self._thumb_photo = photo   # keep reference
        self.thumb_label.configure(image=photo, text="")

    def _build_format_list(self, formats):
        labels = [
            "best — Best Quality (Auto)",
            "bestvideo+bestaudio — Best Video + Best Audio",
        ]
        seen = set()
        for f in reversed(formats):
            h = f.get("height")
            ext = f.get("ext", "")
            fid = f.get("format_id", "")
            if h and h not in seen and ext in ("mp4", "webm", "mkv"):
                seen.add(h)
                size = f.get("filesize") or f.get("filesize_approx")
                sz = f"  {size//1024//1024:.0f}MB" if size else ""
                labels.append(f"{h}p — {h}p {ext.upper()}{sz}  [{fid}]")
        labels.append("audio_only — Audio Only (MP3)")
        self.format_cb["values"] = labels

    # ──────────────────────────────────────────
    #  Download
    # ──────────────────────────────────────────
    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a video URL first.")
            return

        self._cancelled = False
        self.dl_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress["value"] = 0
        self.prog_pct.configure(text="")
        self.prog_detail.configure(text="")
        self.notebook.select(1)

        threading.Thread(target=self._download_worker, args=(url,), daemon=True).start()

    def _cancel_download(self):
        self._cancelled = True
        self._set_status("Cancelling…", WARNING)

    def _download_worker(self, url):
        import re
        fmt_label = self.format_var.get()
        fmt_key   = fmt_label.split("—")[0].strip()
        out_dir   = self.path_var.get()

        # Extract explicit format ID from brackets e.g. "532p — 532p MP4 303MB [12]" → "12"
        bracket_match = re.search(r'\[(\w+)\]', fmt_label)
        explicit_fmt_id = bracket_match.group(1) if bracket_match else None

        # Map human label → yt-dlp format string
        fmt_map = {
            "best":                "bestvideo+bestaudio/best",
            "bestvideo+bestaudio": "bestvideo+bestaudio/best",
            "1080p":               "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p":                "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p":                "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "360p":                "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "audio_only":          "bestaudio/best",
        }

        # If a specific format ID came from the dropdown (e.g. BiliBili's [12]),
        # use it directly instead of a generic selector that the site may reject.
        if explicit_fmt_id and fmt_key not in ("best", "bestvideo+bestaudio", "audio_only"):
            ydl_fmt = explicit_fmt_id
        else:
            ydl_fmt = fmt_map.get(fmt_key, "bestvideo+bestaudio/best")

        postprocs = []
        if fmt_key == "audio_only":
            postprocs.append({"key": "FFmpegExtractAudio", "preferredcodec": "mp3"})
            if self.embed_thumb.get():
                postprocs.append({"key": "EmbedThumbnail"})
        elif self.convert_mp4.get():
            postprocs.append({"key": "FFmpegVideoConvertor", "preferedformat": "mp4"})

        if self.embed_subs.get():
            postprocs.append({"key": "FFmpegEmbedSubtitle"})

        opts = {
            "format":               ydl_fmt,
            "outtmpl":              os.path.join(out_dir, "%(title).80s.%(ext)s"),
            "progress_hooks":       [self._progress_hook],
            "postprocessors":       postprocs,
            "writethumbnail":       self.embed_thumb.get() and fmt_key == "audio_only",
            "writesubtitles":       self.embed_subs.get(),
            "quiet":                True,
            "no_warnings":          True,
            # Merge separate video+audio streams (BiliBili always uses DASH)
            "merge_output_format":  "mp4",
            # Spoof a real browser — BiliBili and many sites reject default yt-dlp UA
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": url,
            },
        }

        try:
            self._log(f"Starting download: {url}")
            self._log(f"Format: {fmt_label}")
            self._log(f"Output: {out_dir}")
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            if not self._cancelled:
                self.root.after(0, self._download_done)
        except Exception as e:
            self.root.after(0, lambda: self._download_error(str(e)))

    def _progress_hook(self, d):
        if self._cancelled:
            raise yt_dlp.utils.DownloadCancelled("User cancelled")

        status = d.get("status")
        if status == "downloading":
            pct_str   = d.get("_percent_str", "0%").strip()
            speed_str = d.get("_speed_str", "").strip()
            eta_str   = d.get("_eta_str", "").strip()
            total     = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded= d.get("downloaded_bytes", 0)
            pct = (downloaded / total * 100) if total else 0

            detail = f"{pct_str}  •  {speed_str}  •  ETA {eta_str}"
            self.root.after(0, lambda p=pct, det=detail, pct=pct_str:
                            self._update_progress(p, det, pct))

        elif status == "finished":
            filename = d.get("filename", "")
            self.root.after(0, lambda f=filename: self._log(f"Finished: {os.path.basename(f)}"))
            self.root.after(0, lambda: self._update_progress(100, "Processing…", "100%"))

    def _update_progress(self, pct, detail, pct_str):
        self.progress["value"] = pct
        self.prog_detail.configure(text=detail)
        self.prog_pct.configure(text=pct_str)
        self._set_status(f"Downloading… {pct_str}", ACCENT2)

    def _download_done(self):
        self.progress["value"] = 100
        self.prog_detail.configure(text="Download complete ✔")
        self.prog_pct.configure(text="100%")
        self._set_status("✔ Download complete!", SUCCESS)
        self._log("✔ Download finished successfully.")
        self.dl_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")

    def _download_error(self, msg):
        self._set_status(f"Error: {msg[:80]}", DANGER)
        self._log(f"✕ ERROR: {msg}")
        self.dl_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        messagebox.showerror("Download Failed", msg)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = VideoDownloader(root)
    root.mainloop()
